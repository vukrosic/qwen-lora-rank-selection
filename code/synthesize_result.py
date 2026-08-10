#!/usr/bin/env python3
"""Deterministically integrate rank-4, historical rank-8, and matched controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
HISTORICAL_RESULT = PACKAGE / "evidence/historical-rank8-result.json"
PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
HISTORICAL_RESULT_SHA256 = "dab32943fbb882f7285e0ced94453af915d5bfbb0d4682a78f01dbf5d37f6a0d"
HISTORICAL_SCOPE = "synthetic associative recall with held-out prompt templates, not facts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_rank_result(result: dict, rank: int, label: str) -> None:
    if result.get("protocol") != PROTOCOL_NAME:
        raise ValueError(f"{label} protocol identity mismatch")
    if result.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ValueError(f"{label} protocol hash mismatch")
    if result.get("rank") != rank:
        raise ValueError(f"{label} rank mismatch")
    if result.get("classification") not in {
        "TRANSFER_SUPPORTED", "NONTRANSFER_OR_MIXED", "INCONCLUSIVE_INVALID"
    }:
        raise ValueError(f"{label} unknown classification")
    errors = result.get("errors")
    gates = result.get("gates")
    if not isinstance(errors, list) or not isinstance(gates, dict):
        raise ValueError(f"{label} malformed validity fields")
    if result["classification"] == "INCONCLUSIVE_INVALID":
        if not errors or gates.get("all_valid") is not False:
            raise ValueError(f"{label} invalid classification lacks invalid evidence")
    else:
        if errors or gates.get("all_valid") is not True:
            raise ValueError(f"{label} substantive classification is not valid")
    if result["classification"] == "TRANSFER_SUPPORTED" and not all(gates.values()):
        raise ValueError(f"{label} supported classification has a failed gate")
    if result["classification"] == "NONTRANSFER_OR_MIXED":
        failed = [name for name, passed in gates.items() if name != "all_valid" and passed is False]
        if not failed:
            raise ValueError(f"{label} non-transfer classification lacks a failed substantive gate")


def validate_historical(result: dict, path: Path) -> None:
    if sha256(path) != HISTORICAL_RESULT_SHA256:
        raise ValueError("historical rank-8 result hash mismatch")
    if result.get("classification") != "SUPPORTED":
        raise ValueError("historical rank-8 baseline is not supported")
    if result.get("scope") != HISTORICAL_SCOPE:
        raise ValueError("historical rank-8 scope mismatch")
    gates = result.get("gates")
    if not isinstance(gates, dict) or not gates or not all(gates.values()):
        raise ValueError("historical rank-8 gates are not all true")
    rows = result.get("rows")
    if not isinstance(rows, list) or [row.get("seed") for row in rows] != [20260817, 20260818, 20260819]:
        raise ValueError("historical rank-8 seed block mismatch")


def synthesize(
    rank4: dict,
    historical: dict,
    rank4_path: Path,
    historical_path: Path,
    matched_rank8: dict | None = None,
    matched_rank8_path: Path | None = None,
) -> dict:
    validate_rank_result(rank4, 4, "rank-4")
    validate_historical(historical, historical_path)
    rank4_class = rank4["classification"]

    if rank4_class == "INCONCLUSIVE_INVALID":
        if matched_rank8 is not None:
            raise ValueError("matched rank 8 is forbidden after invalid rank 4")
        outcome = "INCONCLUSIVE_INVALID"
        terminal = True
        matched_status = "NOT_EARNED"
        statement = "The rank-4 block is invalid, so no robustness conclusion or matched rank-8 spend is allowed."
    elif rank4_class == "TRANSFER_SUPPORTED":
        if matched_rank8 is not None:
            raise ValueError("fresh matched rank 8 is forbidden after supported rank 4")
        outcome = "RANK4_TRANSFER_SUPPORTED"
        terminal = True
        matched_status = "SKIPPED_BY_PROTOCOL"
        statement = (
            "Validation-guided token-vs-example selection transfers at rank 4 on the frozen "
            "same-fact synthetic task; historical prospective rank 8 is contextual confirmation, "
            "not a matched causal control."
        )
    else:
        if matched_rank8 is None:
            outcome = "MATCHED_RANK8_REQUIRED"
            terminal = False
            matched_status = "EARNED_NOT_RUN"
            statement = (
                "Rank 4 is valid but fails at least one transfer gate; the frozen matched rank-8 "
                "control is required before attributing the break to rank."
            )
        else:
            if matched_rank8_path is None:
                raise ValueError("matched rank-8 path is required with matched result")
            validate_rank_result(matched_rank8, 8, "matched rank-8")
            matched_status = "COMPLETED"
            if matched_rank8["classification"] == "TRANSFER_SUPPORTED":
                outcome = "RANK_SPECIFIC_BREAK"
                statement = (
                    "Validation selection fails the frozen gates at rank 4 but passes on the "
                    "matched fresh rank-8 seed block, supporting a bounded rank-specific break."
                )
            elif matched_rank8["classification"] == "NONTRANSFER_OR_MIXED":
                outcome = "MIXED_OR_SEED_BLOCK_INCONCLUSIVE"
                statement = (
                    "Both rank 4 and matched rank 8 fail on the fresh seed block, so rank is not "
                    "isolated as the cause."
                )
            else:
                outcome = "INCONCLUSIVE_INVALID_MATCHED_RANK8"
                statement = "The earned matched rank-8 block is invalid, so causal rank attribution is inconclusive."
            terminal = True

    inputs = {
        "rank4_classification_sha256": sha256(rank4_path),
        "historical_rank8_result_sha256": sha256(historical_path),
    }
    if matched_rank8 is not None and matched_rank8_path is not None:
        inputs["matched_rank8_classification_sha256"] = sha256(matched_rank8_path)
    return {
        "protocol": PROTOCOL_NAME,
        "protocol_sha256": PROTOCOL_SHA256,
        "outcome": outcome,
        "terminal": terminal,
        "statement": statement,
        "claim_boundary": (
            "Qwen3-0.6B 3-bit MLX LoRA on one synthetic associative-recall task; "
            "test prompts are held out but facts are reused; three rank-4 seeds. No natural-data, "
            "unseen-fact, other-model, other-rank, or general LoRA claim."
        ),
        "historical_rank8": {
            "classification": historical["classification"],
            "seeds": [row["seed"] for row in historical["rows"]],
            "scope": historical["scope"],
            "role": "contextual prospective baseline; not a causal control for a rank-4 failure",
        },
        "rank4": rank4,
        "matched_rank8": matched_rank8,
        "matched_rank8_status": matched_status,
        "input_fingerprints": inputs,
    }


def fmt(value: Any, digits: int = 4) -> str:
    return "n/a" if value is None else f"{float(value):.{digits}f}"


def pct(value: Any) -> str:
    return "n/a" if value is None else f"{100 * float(value):.2f}%"


def render_markdown(result: dict) -> str:
    rank4 = result["rank4"]
    lines = [
        "# LoRA selection robustness under rank reduction",
        "",
        "## Decision",
        "",
        f"**{result['outcome']}**",
        "",
        result["statement"],
        "",
        "## Fresh rank-4 evidence",
        "",
        "| Seed | Selected | Selected exact | Other exact | Selected NLL | Other NLL |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rank4.get("rows", []):
        lines.append(
            f"| {row['seed']} | {row['selected']} | {pct(row['selected_metrics']['balanced_exact'])} "
            f"| {pct(row['other_metrics']['balanced_exact'])} | {fmt(row['selected_metrics']['balanced_nll'])} "
            f"| {fmt(row['other_metrics']['balanced_nll'])} |"
        )
    lines.extend([
        "",
        "| Policy | Mean exact | Worst exact | Mean NLL | Worst NLL |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for policy, label in (("selected", "Validation-selected"), ("token", "Always token"), ("example", "Always example")):
        agg = rank4.get("aggregates", {}).get(policy, {})
        lines.append(
            f"| {label} | {pct(agg.get('mean_exact'))} | {pct(agg.get('worst_exact'))} "
            f"| {fmt(agg.get('mean_nll'))} | {fmt(agg.get('worst_nll'))} |"
        )
    failed = [name for name, passed in rank4.get("gates", {}).items() if passed is False]
    lines.extend([
        "",
        "## Controls and interpretation",
        "",
        f"- Rank-4 validity: `{rank4.get('gates', {}).get('all_valid')}`; analyzer errors: `{len(rank4.get('errors', []))}`.",
        f"- Failed rank-4 gates: `{', '.join(failed) if failed else 'none'}`.",
        f"- Matched rank-8 status: `{result['matched_rank8_status']}`.",
        "- Historical rank 8 used fresh seeds 20260817–20260819 and passed prospectively, but is not a matched control for a rank-4 failure.",
        "",
        "## Scope",
        "",
        result["claim_boundary"],
        "",
        "Authoritative machine-readable integration is `RESULT.json`. Raw adapters remain local and are not part of the GitHub-ready evidence package.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank4", type=Path, default=PACKAGE / "evidence/rank4-classification.json")
    parser.add_argument("--historical-rank8", type=Path, default=HISTORICAL_RESULT)
    parser.add_argument("--matched-rank8", type=Path)
    parser.add_argument("--output-json", type=Path, default=PACKAGE / "evidence/RESULT.json")
    parser.add_argument("--output-md", type=Path, default=PACKAGE / "RESULTS.md")
    args = parser.parse_args()
    rank4 = load_json(args.rank4)
    historical = load_json(args.historical_rank8)
    matched = load_json(args.matched_rank8) if args.matched_rank8 else None
    result = synthesize(rank4, historical, args.rank4, args.historical_rank8, matched, args.matched_rank8)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    args.output_md.write_text(render_markdown(result))
    print(json.dumps({"outcome": result["outcome"], "terminal": result["terminal"]}, sort_keys=True))


if __name__ == "__main__":
    main()
