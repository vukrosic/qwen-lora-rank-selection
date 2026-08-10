#!/usr/bin/env python3
"""Deterministically audit the bundled same-fact synthetic split structure."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "train": "08051d9c2015eb5769aa165b2d45907e57ccf8327336dc9b6985c681615efca9",
    "valid": "e63ce5a4a2c308ec0366e230f73a007150239a5d4579cdeb88507cbc4899d704",
    "test": "0a6900dcdf3ff71885bcb18fc5df908f55b93daef2caad027d8e2f2044620899",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"non-object JSONL row in {path}")
    return rows


def audit(data: Path) -> dict:
    errors: list[str] = []
    splits = {name: load_jsonl(data / f"{name}.jsonl") for name in EXPECTED_HASHES}
    summaries = {}
    keys = {}
    ids = {}
    prompts = {}
    mapping: dict[str, set[str]] = defaultdict(set)
    for name, rows in splits.items():
        required = {"id", "key", "kind", "prompt", "completion"}
        malformed = [index for index, row in enumerate(rows) if set(row) != required]
        if malformed:
            errors.append(f"{name} malformed rows: {malformed[:5]}")
        observed_hash = sha256(data / f"{name}.jsonl")
        if observed_hash != EXPECTED_HASHES[name]:
            errors.append(f"{name} hash mismatch")
        split_keys = [row.get("key") for row in rows]
        split_ids = [row.get("id") for row in rows]
        split_prompts = [row.get("prompt") for row in rows]
        if len(set(split_ids)) != len(split_ids):
            errors.append(f"{name} duplicate IDs")
        if len(set(split_prompts)) != len(split_prompts):
            errors.append(f"{name} duplicate prompts")
        for row in rows:
            mapping[str(row.get("key"))].add(str(row.get("completion")))
        summaries[name] = {
            "records": len(rows),
            "unique_keys": len(set(split_keys)),
            "occurrences_per_key_unique": sorted(set(Counter(split_keys).values())),
            "kinds": dict(sorted(Counter(row.get("kind") for row in rows).items())),
            "sha256": observed_hash,
        }
        keys[name] = set(split_keys)
        ids[name] = set(split_ids)
        prompts[name] = set(split_prompts)

    expected_counts = {
        "train": (384, [4]),
        "valid": (96, [1]),
        "test": (96, [1]),
    }
    for name, (records, occurrences) in expected_counts.items():
        if summaries[name]["records"] != records or summaries[name]["occurrences_per_key_unique"] != occurrences:
            errors.append(f"{name} record/key multiplicity mismatch")
    same_key_sets = keys["train"] == keys["valid"] == keys["test"]
    one_target_per_key = all(len(targets) == 1 for targets in mapping.values())
    id_disjoint = all(
        ids[left].isdisjoint(ids[right])
        for left, right in (("train", "valid"), ("train", "test"), ("valid", "test"))
    )
    prompt_disjoint = all(
        prompts[left].isdisjoint(prompts[right])
        for left, right in (("train", "valid"), ("train", "test"), ("valid", "test"))
    )
    if not same_key_sets:
        errors.append("fact-key sets differ across splits")
    if not one_target_per_key:
        errors.append("a fact key maps to multiple targets")
    if not id_disjoint:
        errors.append("record IDs overlap across splits")
    if not prompt_disjoint:
        errors.append("literal prompts overlap across splits")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "splits": summaries,
        "same_key_sets_across_splits": same_key_sets,
        "one_target_per_key_across_splits": one_target_per_key,
        "record_ids_disjoint_across_splits": id_disjoint,
        "literal_prompts_disjoint_across_splits": prompt_disjoint,
        "interpretation": (
            "Validation and test use distinct records and literal prompts but the exact same "
            "96 key-to-target facts as training; this is same-fact prompt-template transfer."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=PACKAGE / "data")
    args = parser.parse_args()
    result = audit(args.data)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
