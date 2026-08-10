#!/usr/bin/env python3
"""Model-free fixtures for exact-count and NLL margin reporting."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("margin_audit_test", ROOT / "audit_margins.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import margin auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    counts = (48, 50, 52)
    rows = []
    for seed, selected_count in zip((20260841, 20260842, 20260843), counts):
        rows.append({
            "seed": seed,
            "selected": "token",
            "selected_metrics": {
                "balanced_exact": selected_count / 96,
                "short_exact": (selected_count // 2) / 48,
                "long_exact": (selected_count - selected_count // 2) / 48,
                "balanced_nll": 0.2,
            },
            "other_metrics": {
                "balanced_exact": (selected_count - 2) / 96,
                "balanced_nll": 0.3,
            },
        })
    classification = {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "rank": 4,
        "classification": "TRANSFER_SUPPORTED",
        "errors": [],
        "gates": {"all_valid": True},
        "rows": rows,
        "aggregates": {
            "selected": {
                "mean_exact": sum(counts) / 288,
                "worst_exact": min(counts) / 96,
                "mean_nll": 0.2,
                "worst_nll": 0.22,
            },
            "token": {
                "mean_exact": 138 / 288,
                "worst_exact": 45 / 96,
                "mean_nll": 0.25,
                "worst_nll": 0.27,
            },
            "example": {
                "mean_exact": 135 / 288,
                "worst_exact": 44 / 96,
                "mean_nll": 0.28,
                "worst_nll": 0.31,
            },
        },
    }
    with tempfile.TemporaryDirectory(prefix="rank-margin-audit-") as temp:
        source = Path(temp) / "classification.json"
        source.write_text(json.dumps(classification, sort_keys=True) + "\n")
        result = module.audit(classification, source)
        if [row["selected_minus_other_exact_records"] for row in result["per_seed"]] != [2, 2, 2]:
            raise AssertionError("per-seed exact-count margins drifted")
        if result["aggregate_comparisons"]["token"]["selected_minus_baseline_mean_exact_records_of_288"] != 12:
            raise AssertionError("aggregate exact-count margin drifted")

        corrupted = json.loads(json.dumps(classification))
        corrupted["rows"][0]["selected_metrics"]["balanced_exact"] = 0.5001
        try:
            module.audit(corrupted, source)
        except ValueError as exc:
            if "96-record grid" not in str(exc):
                raise
        else:
            raise AssertionError("off-grid exact rate was accepted")

        invalid = json.loads(json.dumps(classification))
        invalid["classification"] = "INCONCLUSIVE_INVALID"
        invalid["errors"] = ["fixture"]
        invalid["gates"]["all_valid"] = False
        try:
            module.audit(invalid, source)
        except ValueError:
            invalid_status = "REJECTED"
        else:
            raise AssertionError("invalid classification received substantive margins")

    print(json.dumps({
        "status": "PASS",
        "exact_grid_corruption": "REJECTED",
        "invalid_classification": invalid_status,
        "seed_count": 3,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
