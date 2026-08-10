#!/usr/bin/env python3
"""Model-free fixture for the predeclared representative-evidence export."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("evidence_export_test", ROOT / "export_evidence.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import evidence exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="rank-evidence-export-") as temp:
        runs = Path(temp)
        fingerprints = {}
        for seed in module.SEEDS:
            for condition in module.CONDITIONS:
                generations = []
                teachers = []
                for index in range(96):
                    kind = "short" if index < 48 else "long"
                    record_id = f"{kind}-{index:03d}"
                    generations.append({
                        "id": record_id,
                        "kind": kind,
                        "prompt": f"prompt {record_id}",
                        "target": "target",
                        "generated": "target" if index % 2 == 0 else "wrong",
                        "normalized_target": "target",
                        "normalized_generated": "target" if index % 2 == 0 else "wrong",
                        "exact_match": index % 2 == 0,
                    })
                    teachers.append({
                        "id": record_id,
                        "kind": kind,
                        "supervised_tokens": 2,
                        "loss_sum": 0.5,
                        "correct_tokens": 1,
                    })
                metrics = runs / f"rank4-seed{seed}-{condition}-eval/metrics"
                write_jsonl(metrics / "generations.jsonl", generations)
                write_jsonl(metrics / "teacher-forced.jsonl", teachers)
                for name in ("generations.jsonl", "teacher-forced.jsonl"):
                    fingerprints[f"rank4/seed{seed}/{condition}/{name}"] = sha256(metrics / name)
        classification = {
            "protocol": module.PROTOCOL_NAME,
            "protocol_sha256": module.PROTOCOL_SHA256,
            "rank": 4,
            "evidence_fingerprints": fingerprints,
        }
        classification_path = runs / "rank4-classification.json"
        classification_path.write_text(json.dumps(classification, sort_keys=True) + "\n")
        result = module.export(runs, 4, classification, classification_path)
        if len(result["records"]) != 24:
            raise AssertionError("representative sample is not exactly 24 records")
        expected_ids = {"short-000", "short-001", "long-048", "long-049"}
        for seed in module.SEEDS:
            for condition in module.CONDITIONS:
                observed = {
                    row["id"] for row in result["records"]
                    if row["seed"] == seed and row["condition"] == condition
                }
                if observed != expected_ids:
                    raise AssertionError(f"sampling rule drift for {seed} {condition}: {observed}")
        if len(result["source_files"]) != 12:
            raise AssertionError("source fingerprint count mismatch")
        if result["source_classification_sha256"] != sha256(classification_path):
            raise AssertionError("source classification fingerprint mismatch")

        corrupted = json.loads(classification_path.read_text())
        first_key = sorted(fingerprints)[0]
        corrupted["evidence_fingerprints"][first_key] = "0" * 64
        try:
            module.export(runs, 4, corrupted, classification_path)
        except ValueError as exc:
            if "does not match classification fingerprint" not in str(exc):
                raise
        else:
            raise AssertionError("classification/raw mismatch was accepted")

    print(json.dumps({
        "status": "PASS",
        "records": 24,
        "source_files": 12,
        "classification_binding": "VERIFIED",
        "sampling": "FIXED_BEFORE_OUTCOMES",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
