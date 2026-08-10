#!/usr/bin/env python3
"""Evaluate one base or adapted Qwen condition with common frozen metrics."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

from train_condition import MixedDataset


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(text: str) -> str:
    return " ".join(text.strip().split())


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def collate(dataset: MixedDataset, indices: list[int], max_seq_length: int):
    items = [dataset.processed(index) for index in indices]
    if any(len(item[0]) > max_seq_length for item in items):
        raise ValueError("Evaluation record would be truncated")
    max_length = 1 + 32 * ((max(len(item[0]) for item in items) + 31) // 32)
    max_length = min(max_length, max_seq_length)
    batch = np.zeros((len(items), max_length), dtype=np.int32)
    spans = []
    metadata = []
    for row, (tokens, offset, kind, record_id) in enumerate(items):
        batch[row, : len(tokens)] = tokens
        spans.append((offset, len(tokens)))
        metadata.append((kind, record_id))
    return mx.array(batch), mx.array(spans), metadata


def aggregate(records: list[dict], value_prefix: str) -> dict:
    grouped = defaultdict(list)
    for record in records:
        grouped[record["kind"]].append(record)
    result = {}
    for kind, rows in sorted(grouped.items()):
        tokens = sum(row["supervised_tokens"] for row in rows)
        result[kind] = {
            "examples": len(rows),
            "example_nll_mean": sum(row["example_nll"] for row in rows) / len(rows),
            "token_nll": sum(row["loss_sum"] for row in rows) / tokens,
            "target_token_accuracy": sum(row["correct_tokens"] for row in rows)
            / tokens,
        }
        if value_prefix == "generation":
            result[kind]["exact_match"] = sum(row["exact_match"] for row in rows) / len(rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-seq-length", type=int, default=128)
    parser.add_argument("--max-generation-tokens", type=int, default=24)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    started = time.time()
    mx.reset_peak_memory()
    model, tokenizer = load(
        str(args.model),
        adapter_path=str(args.adapter) if args.adapter is not None else None,
    )
    model.eval()
    dataset = MixedDataset(args.data / "test.jsonl", tokenizer)
    teacher_records = []
    for start in range(0, len(dataset), args.batch_size):
        indices = list(range(start, min(start + args.batch_size, len(dataset))))
        batch, spans, metadata = collate(dataset, indices, args.max_seq_length)
        inputs = batch[:, :-1]
        targets = batch[:, 1:]
        logits = model(inputs)
        steps = mx.arange(1, targets.shape[1] + 1)
        mask = mx.logical_and(steps >= spans[:, 0:1], steps < spans[:, 1:])
        losses = nn.losses.cross_entropy(logits, targets).astype(mx.float32) * mask
        counts = mask.sum(axis=1)
        loss_sums = losses.sum(axis=1)
        correct = (mx.argmax(logits, axis=-1) == targets) * mask
        correct_counts = correct.sum(axis=1)
        mx.eval(counts, loss_sums, correct_counts)
        for row, (kind, record_id) in enumerate(metadata):
            count = int(counts[row])
            loss_sum = float(loss_sums[row])
            teacher_records.append(
                {
                    "id": record_id,
                    "kind": kind,
                    "supervised_tokens": count,
                    "loss_sum": loss_sum,
                    "example_nll": loss_sum / count,
                    "correct_tokens": int(correct_counts[row]),
                }
            )

    sampler = make_sampler(temp=0.0)
    generation_records = []
    for record in dataset.records:
        user = [{"role": "user", "content": record["prompt"]}]
        prompt_tokens = tokenizer.apply_chat_template(
            user,
            add_generation_prompt=True,
            return_dict=False,
            enable_thinking=False,
        )
        generated = generate(
            model,
            tokenizer,
            prompt_tokens,
            max_tokens=args.max_generation_tokens,
            sampler=sampler,
            verbose=False,
        )
        generation_records.append(
            {
                "id": record["id"],
                "kind": record["kind"],
                "prompt": record["prompt"],
                "target": record["completion"],
                "generated": generated,
                "normalized_target": normalized(record["completion"]),
                "normalized_generated": normalized(generated),
                "exact_match": normalized(generated) == normalized(record["completion"]),
            }
        )

    teacher_by_kind = aggregate(teacher_records, "teacher")
    teacher_by_id = {record["id"]: record for record in teacher_records}
    generation_by_kind = aggregate(
        [
            {
                **row,
                "supervised_tokens": teacher_by_id[row["id"]]["supervised_tokens"],
                "loss_sum": teacher_by_id[row["id"]]["loss_sum"],
                "example_nll": teacher_by_id[row["id"]]["example_nll"],
                "correct_tokens": teacher_by_id[row["id"]]["correct_tokens"],
            }
            for row in generation_records
        ],
        "generation",
    )
    short = generation_by_kind["short"]
    long = generation_by_kind["long"]
    metrics = {
        "label": args.label,
        "adapter": str(args.adapter) if args.adapter is not None else None,
        "test_scope": "held-out prompt template over training facts; not held-out facts",
        "normalization": "strip outer whitespace and collapse internal whitespace; case-sensitive",
        "fingerprints": {
            "evaluate_condition.py": sha256(Path(__file__)),
            "data_manifest.json": sha256(args.data / "manifest.json"),
            "model.safetensors": sha256(args.model / "model.safetensors"),
            "model_config.json": sha256(args.model / "config.json"),
            **(
                {
                    "adapter_config.json": sha256(args.adapter / "adapter_config.json"),
                    "adapters.safetensors": sha256(args.adapter / "adapters.safetensors"),
                }
                if args.adapter is not None
                else {}
            ),
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "mlx": importlib.metadata.version("mlx"),
            "mlx-lm": importlib.metadata.version("mlx-lm"),
        },
        "teacher_forced": teacher_by_kind,
        "generation": generation_by_kind,
        "summary": {
            "balanced_exact_match": (short["exact_match"] + long["exact_match"]) / 2,
            "worst_skill_exact_match": min(short["exact_match"], long["exact_match"]),
            "short_minus_long_exact_gap": short["exact_match"] - long["exact_match"],
            "balanced_example_nll": (
                teacher_by_kind["short"]["example_nll_mean"]
                + teacher_by_kind["long"]["example_nll_mean"]
            )
            / 2,
            "balanced_target_token_accuracy": (
                teacher_by_kind["short"]["target_token_accuracy"]
                + teacher_by_kind["long"]["target_token_accuracy"]
            )
            / 2,
        },
        "resource": {
            "wall_seconds": time.time() - started,
            "peak_mlx_memory_gb": mx.get_peak_memory() / 1e9,
            "active_mlx_memory_gb": mx.get_active_memory() / 1e9,
            "cache_mlx_memory_gb": mx.get_cache_memory() / 1e9,
        },
    }
    write_jsonl(args.output / "teacher-forced.jsonl", teacher_records)
    write_jsonl(args.output / "generations.jsonl", generation_records)
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
