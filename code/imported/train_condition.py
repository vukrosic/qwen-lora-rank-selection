#!/usr/bin/env python3
"""Train one controlled Qwen LoRA loss-normalization condition with MLX-LM."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from mlx_lm import load
from mlx_lm.tuner.trainer import TrainingArgs, train
from mlx_lm.tuner.utils import linear_to_lora_layers, print_trainable_parameters


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MixedDataset:
    def __init__(self, path: Path, tokenizer):
        self.records = [json.loads(line) for line in path.read_text().splitlines()]
        self.tokenizer = tokenizer
        self.cache = [None] * len(self.records)

    def __len__(self):
        return len(self.records)

    def processed(self, index: int):
        if self.cache[index] is None:
            record = self.records[index]
            user = [{"role": "user", "content": record["prompt"]}]
            messages = user + [{"role": "assistant", "content": record["completion"]}]
            tokens = self.tokenizer.apply_chat_template(
                messages, return_dict=False, enable_thinking=False
            )
            prefix = self.tokenizer.apply_chat_template(
                user,
                add_generation_prompt=True,
                return_dict=False,
                enable_thinking=False,
            )
            self.cache[index] = (tokens, len(prefix), record["kind"], record["id"])
        return self.cache[index]


class BalancedMixedIterator:
    def __init__(self, order_seed: int):
        self.order_seed = order_seed

    def __call__(
        self,
        dataset,
        batch_size,
        max_seq_length,
        loop=False,
        seed=None,
        comm_group=None,
    ):
        if comm_group is not None and comm_group.size() != 1:
            raise ValueError("This bounded experiment supports one local worker only")
        if batch_size % 2:
            raise ValueError("batch_size must be even for balanced mixed batches")
        half = batch_size // 2
        short = [i for i, r in enumerate(dataset.records) if r["kind"] == "short"]
        long = [i for i, r in enumerate(dataset.records) if r["kind"] == "long"]
        if len(short) != len(long) or len(short) % half:
            raise ValueError("short/long records must be equal and divisible by half-batch")

        epoch = 0
        while True:
            rng = np.random.default_rng(self.order_seed + epoch)
            s = rng.permutation(short)
            l = rng.permutation(long)
            batches = []
            for start in range(0, len(s), half):
                indices = list(s[start : start + half]) + list(l[start : start + half])
                rng.shuffle(indices)
                batches.append(indices)
            rng.shuffle(batches)

            for indices in batches:
                items = [dataset.processed(i) for i in indices]
                lengths = [min(len(x[0]), max_seq_length) for x in items]
                max_len = min(1 + 32 * ((max(lengths) + 31) // 32), max_seq_length)
                batch = np.zeros((batch_size, max_len), dtype=np.int32)
                offsets = []
                for row, (tokens, offset, _, _) in enumerate(items):
                    length = min(len(tokens), max_seq_length)
                    batch[row, :length] = tokens[:length]
                    offsets.append((min(offset, length), length))
                yield mx.array(batch), mx.array(offsets)

            if not loop:
                return
            epoch += 1


def masked_losses(model, batch, lengths):
    inputs = batch[:, :-1]
    targets = batch[:, 1:]
    logits = model(inputs)
    steps = mx.arange(1, targets.shape[1] + 1)
    # `lengths[:, 1]` is len(tokens), while `steps` is the target-token index.
    # Valid targets are therefore offset <= step < len(tokens).  Using <= would
    # supervise the first zero-padding target because batches are padded beyond
    # the longest record.
    mask = mx.logical_and(steps >= lengths[:, 0:1], steps < lengths[:, 1:])
    losses = nn.losses.cross_entropy(logits, targets).astype(mx.float32) * mask
    counts = mask.sum(axis=1)
    return losses, counts, mask.sum()


def token_mean_loss(model, batch, lengths):
    losses, _, total = masked_losses(model, batch, lengths)
    return losses.sum() / total, total


def example_mean_loss(model, batch, lengths):
    losses, counts, total = masked_losses(model, batch, lengths)
    per_example = losses.sum(axis=1) / counts
    return per_example.mean(), total


def validate_dataset(dataset: MixedDataset, max_seq_length: int) -> dict:
    kinds: dict[str, int] = {}
    ids: set[str] = set()
    supervised_counts = []
    for index in range(len(dataset)):
        tokens, offset, kind, record_id = dataset.processed(index)
        if record_id in ids:
            raise ValueError(f"Duplicate record id: {record_id}")
        ids.add(record_id)
        if len(tokens) > max_seq_length:
            raise ValueError(
                f"Record {record_id} has {len(tokens)} tokens and would be truncated"
            )
        if offset >= len(tokens):
            raise ValueError(f"Record {record_id} has zero supervised tokens")
        kinds[kind] = kinds.get(kind, 0) + 1
        supervised_counts.append(len(tokens) - offset)
    return {
        "records": len(dataset),
        "kinds": kinds,
        "supervised_tokens_min": min(supervised_counts),
        "supervised_tokens_max": max(supervised_counts),
        "supervised_tokens_total": sum(supervised_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--condition", choices=("token", "example"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--iters", type=int, default=288)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--max-seq-length", type=int, default=128)
    args = parser.parse_args()

    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    np.random.seed(args.seed)
    mx.random.seed(args.seed)
    started = time.time()
    model, tokenizer = load(str(args.model))
    model.freeze()
    lora_parameters = {"rank": 8, "dropout": 0.0, "scale": 20.0}
    linear_to_lora_layers(model, args.num_layers, lora_parameters)
    print_trainable_parameters(model)

    train_data = MixedDataset(args.data / "train.jsonl", tokenizer)
    valid_data = MixedDataset(args.data / "valid.jsonl", tokenizer)
    dataset_validation = {
        "train": validate_dataset(train_data, args.max_seq_length),
        "valid": validate_dataset(valid_data, args.max_seq_length),
    }
    iterator = BalancedMixedIterator(order_seed=args.seed + 1000)
    loss = token_mean_loss if args.condition == "token" else example_mean_loss
    optimizer = optim.AdamW(learning_rate=args.learning_rate, weight_decay=0.0)

    config = {
        "model": str(args.model),
        "fine_tune_type": "lora",
        "num_layers": args.num_layers,
        "lora_parameters": lora_parameters,
        "condition": args.condition,
        "seed": args.seed,
        "batch_size": args.batch_size,
        "iters": args.iters,
        "learning_rate": args.learning_rate,
        "max_seq_length": args.max_seq_length,
        "dataset_validation": dataset_validation,
        "data_manifest": json.loads((args.data / "manifest.json").read_text()),
        "fingerprints": {
            "train_condition.py": sha256(Path(__file__)),
            "data_manifest.json": sha256(args.data / "manifest.json"),
            "model.safetensors": sha256(args.model / "model.safetensors"),
            "model_config.json": sha256(args.model / "config.json"),
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "mlx": importlib.metadata.version("mlx"),
            "mlx-lm": importlib.metadata.version("mlx-lm"),
        },
    }
    (args.output / "adapter_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n"
    )
    training_args = TrainingArgs(
        batch_size=args.batch_size,
        iters=args.iters,
        val_batches=-1,
        steps_per_report=24,
        steps_per_eval=96,
        steps_per_save=args.iters,
        adapter_file=args.output / "adapters.safetensors",
        max_seq_length=args.max_seq_length,
        grad_accumulation_steps=1,
        clear_cache_threshold=2_000_000_000,
    )
    train(
        model=model,
        optimizer=optimizer,
        train_dataset=train_data,
        val_dataset=valid_data,
        args=training_args,
        loss=loss,
        iterate_batches=iterator,
    )
    resource = {
        "condition": args.condition,
        "seed": args.seed,
        "wall_seconds": time.time() - started,
        "peak_mlx_memory_gb": mx.get_peak_memory() / 1e9,
        "cache_memory_gb": mx.get_cache_memory() / 1e9,
    }
    (args.output / "resource.json").write_text(
        json.dumps(resource, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(resource, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
