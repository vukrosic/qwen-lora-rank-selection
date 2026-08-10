#!/usr/bin/env python3
"""Export a predeclared compact sample from analyzer-validated raw evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


SEEDS = (20260841, 20260842, 20260843)
CONDITIONS = ("token", "example")
KINDS = ("short", "long")
SAMPLE_PER_KIND = 2
PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
SAMPLING_RULE = (
    "lexicographically first two record IDs within each seed, condition, and "
    "short/long kind; fixed before outcomes"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"non-object JSONL row in {path}")
    return rows


def export(runs: Path, rank: int, classification: dict, classification_path: Path) -> dict:
    if rank not in (4, 8):
        raise ValueError("rank must be 4 or 8")
    if classification.get("protocol") != PROTOCOL_NAME:
        raise ValueError("classification protocol identity mismatch")
    if classification.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ValueError("classification protocol hash mismatch")
    if classification.get("rank") != rank:
        raise ValueError("classification rank mismatch")
    evidence_fingerprints = classification.get("evidence_fingerprints")
    if not isinstance(evidence_fingerprints, dict):
        raise ValueError("classification evidence fingerprints missing")
    records = []
    source_files = {}
    for seed in SEEDS:
        for condition in CONDITIONS:
            metrics = runs / f"rank{rank}-seed{seed}-{condition}-eval/metrics"
            generation_path = metrics / "generations.jsonl"
            teacher_path = metrics / "teacher-forced.jsonl"
            generations = load_jsonl(generation_path)
            teachers = load_jsonl(teacher_path)
            if len(generations) != 96 or len(teachers) != 96:
                raise ValueError(f"expected 96 raw records for rank {rank} seed {seed} {condition}")
            by_generation = {row.get("id"): row for row in generations}
            by_teacher = {row.get("id"): row for row in teachers}
            if len(by_generation) != 96 or set(by_generation) != set(by_teacher):
                raise ValueError(f"raw record IDs mismatch for rank {rank} seed {seed} {condition}")
            raw_paths = (generation_path, teacher_path)
            for raw_path in raw_paths:
                digest = sha256(raw_path)
                source_files[str(raw_path.relative_to(runs))] = digest
                analyzer_key = f"rank{rank}/seed{seed}/{condition}/{raw_path.name}"
                if evidence_fingerprints.get(analyzer_key) != digest:
                    raise ValueError(
                        f"raw evidence does not match classification fingerprint: {analyzer_key}"
                    )
            for kind in KINDS:
                selected_ids = sorted(
                    record_id for record_id, row in by_generation.items()
                    if row.get("kind") == kind
                )[:SAMPLE_PER_KIND]
                if len(selected_ids) != SAMPLE_PER_KIND:
                    raise ValueError(f"insufficient {kind} records for seed {seed} {condition}")
                for record_id in selected_ids:
                    generation = by_generation[record_id]
                    teacher = by_teacher[record_id]
                    supervised = teacher.get("supervised_tokens")
                    loss_sum = teacher.get("loss_sum")
                    correct = teacher.get("correct_tokens")
                    values = (supervised, loss_sum, correct)
                    if (
                        not isinstance(supervised, int) or supervised <= 0
                        or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values)
                    ):
                        raise ValueError(f"invalid teacher-forced values for {record_id}")
                    records.append({
                        "rank": rank,
                        "seed": seed,
                        "condition": condition,
                        "id": record_id,
                        "kind": kind,
                        "prompt": generation.get("prompt"),
                        "target": generation.get("target"),
                        "generated": generation.get("generated"),
                        "normalized_target": generation.get("normalized_target"),
                        "normalized_generated": generation.get("normalized_generated"),
                        "exact_match": generation.get("exact_match"),
                        "supervised_tokens": supervised,
                        "example_nll": loss_sum / supervised,
                        "target_token_accuracy": correct / supervised,
                    })
    expected = len(SEEDS) * len(CONDITIONS) * len(KINDS) * SAMPLE_PER_KIND
    if len(records) != expected:
        raise ValueError(f"unexpected exported count: {len(records)}")
    return {
        "rank": rank,
        "sampling_rule": SAMPLING_RULE,
        "source_classification_sha256": sha256(classification_path),
        "records": records,
        "source_files": dict(sorted(source_files.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--rank", type=int, choices=(4, 8), required=True)
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    classification = json.loads(args.classification.read_text())
    if not isinstance(classification, dict):
        raise ValueError("classification must be a JSON object")
    result = export(args.runs, args.rank, classification, args.classification)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"rank": args.rank, "records": len(result["records"])}, sort_keys=True))


if __name__ == "__main__":
    main()
