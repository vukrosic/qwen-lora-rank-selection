#!/usr/bin/env python3
"""Render exact record-count and NLL margins from a valid rank-4 classification."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
SUBSTANTIVE = {"TRANSFER_SUPPORTED", "NONTRANSFER_OR_MIXED"}
INTERPRETATION = (
    "descriptive frozen-gate margins only; not a significance test or confidence interval"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def exact_count(rate, denominator: int, label: str) -> int:
    if not finite(rate) or not 0 <= rate <= 1:
        raise ValueError(f"{label} is not a finite exact-match rate")
    count = round(rate * denominator)
    if not math.isclose(rate, count / denominator, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"{label} is not on the {denominator}-record grid")
    return count


def nll_advantage(baseline, selected, label: str) -> float:
    if not finite(baseline) or not finite(selected):
        raise ValueError(f"{label} has non-finite NLL")
    return baseline - selected


def audit(classification: dict, source_path: Path) -> dict:
    if classification.get("protocol") != PROTOCOL_NAME:
        raise ValueError("classification protocol identity mismatch")
    if classification.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ValueError("classification protocol hash mismatch")
    if classification.get("rank") != 4:
        raise ValueError("margin audit requires rank 4")
    if classification.get("classification") not in SUBSTANTIVE:
        raise ValueError("margin audit requires a valid substantive rank-4 classification")
    gates = classification.get("gates")
    if classification.get("errors") != [] or not isinstance(gates, dict) or gates.get("all_valid") is not True:
        raise ValueError("margin audit requires clean rank-4 validity")
    rows = classification.get("rows")
    if not isinstance(rows, list) or [row.get("seed") for row in rows] != [20260841, 20260842, 20260843]:
        raise ValueError("rank-4 rows do not match the frozen seed block")

    per_seed = []
    for row in rows:
        if row.get("selected") not in {"token", "example"}:
            raise ValueError(f"seed {row.get('seed')} selected condition is invalid")
        selected = row.get("selected_metrics")
        other = row.get("other_metrics")
        if not isinstance(selected, dict) or not isinstance(other, dict):
            raise ValueError(f"seed {row.get('seed')} metrics missing")
        selected_count = exact_count(selected.get("balanced_exact"), 96, "selected exact")
        other_count = exact_count(other.get("balanced_exact"), 96, "other exact")
        short_count = exact_count(selected.get("short_exact"), 48, "selected short exact")
        long_count = exact_count(selected.get("long_exact"), 48, "selected long exact")
        if short_count + long_count != selected_count:
            raise ValueError(f"seed {row.get('seed')} selected exact counts are inconsistent")
        per_seed.append({
            "seed": row["seed"],
            "selected": row.get("selected"),
            "selected_exact_count_of_96": selected_count,
            "other_exact_count_of_96": other_count,
            "selected_minus_other_exact_records": selected_count - other_count,
            "selected_short_exact_count_of_48": short_count,
            "selected_long_exact_count_of_48": long_count,
            "other_minus_selected_nll": nll_advantage(
                other.get("balanced_nll"), selected.get("balanced_nll"), "seed NLL"
            ),
        })

    aggregates = classification.get("aggregates")
    if not isinstance(aggregates, dict) or not all(
        isinstance(aggregates.get(name), dict) for name in ("selected", "token", "example")
    ):
        raise ValueError("rank-4 aggregate metrics missing")
    selected = aggregates["selected"]
    comparisons = {}
    for baseline_name in ("token", "example"):
        baseline = aggregates[baseline_name]
        selected_mean_count = exact_count(selected.get("mean_exact"), 288, "selected mean exact")
        baseline_mean_count = exact_count(baseline.get("mean_exact"), 288, f"{baseline_name} mean exact")
        selected_worst_count = exact_count(selected.get("worst_exact"), 96, "selected worst exact")
        baseline_worst_count = exact_count(baseline.get("worst_exact"), 96, f"{baseline_name} worst exact")
        comparisons[baseline_name] = {
            "selected_minus_baseline_mean_exact_records_of_288": (
                selected_mean_count - baseline_mean_count
            ),
            "selected_minus_baseline_worst_exact_records_of_96": (
                selected_worst_count - baseline_worst_count
            ),
            "baseline_minus_selected_mean_nll": nll_advantage(
                baseline.get("mean_nll"), selected.get("mean_nll"), "mean NLL"
            ),
            "baseline_minus_selected_worst_nll": nll_advantage(
                baseline.get("worst_nll"), selected.get("worst_nll"), "worst NLL"
            ),
        }
    return {
        "protocol": PROTOCOL_NAME,
        "protocol_sha256": PROTOCOL_SHA256,
        "rank": 4,
        "classification": classification["classification"],
        "source_classification_sha256": sha256(source_path),
        "interpretation": INTERPRETATION,
        "per_seed": per_seed,
        "aggregate_comparisons": comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    classification = json.loads(args.classification.read_text())
    if not isinstance(classification, dict):
        raise ValueError("classification must be a JSON object")
    result = audit(classification, args.classification)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"classification": result["classification"], "status": "PASS"}, sort_keys=True))


if __name__ == "__main__":
    main()
