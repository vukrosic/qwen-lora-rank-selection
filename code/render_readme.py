#!/usr/bin/env python3
"""Render the package front page from a terminal synthesized result."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


TERMINAL_OUTCOMES = {
    "RANK4_TRANSFER_SUPPORTED",
    "INCONCLUSIVE_INVALID",
    "RANK_SPECIFIC_BREAK",
    "MIXED_OR_SEED_BLOCK_INCONCLUSIVE",
    "INCONCLUSIVE_INVALID_MATCHED_RANK8",
}


def number(value, digits: int = 4) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return "not available"
    return f"{value:.{digits}f}"


def percent(value) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return "not available"
    return f"{100 * value:.2f}%"


def render(result: dict) -> str:
    outcome = result.get("outcome")
    if result.get("terminal") is not True or outcome not in TERMINAL_OUTCOMES:
        raise ValueError("README requires a recognized terminal result")
    statement = result.get("statement")
    boundary = result.get("claim_boundary")
    if not isinstance(statement, str) or not isinstance(boundary, str):
        raise ValueError("terminal statement or claim boundary missing")

    lines = [
        "# Validation-guided LoRA selection under rank reduction",
        "",
        f"**{outcome}**",
        "",
        statement,
        "",
        "## What we tested",
        "",
        "For each of three fresh seeds, we trained token-mean and example-mean LoRA "
        "adapters at rank 4, selected the lower final validation loss before test "
        "evaluation, and compared that policy with always-token and always-example.",
        "",
    ]
    rank4 = result.get("rank4")
    aggregates = rank4.get("aggregates", {}) if isinstance(rank4, dict) else {}
    selected = aggregates.get("selected", {}) if isinstance(aggregates, dict) else {}
    token = aggregates.get("token", {}) if isinstance(aggregates, dict) else {}
    example = aggregates.get("example", {}) if isinstance(aggregates, dict) else {}
    if outcome != "INCONCLUSIVE_INVALID":
        lines.extend([
            "## Rank-4 summary",
            "",
            f"Validation-selected mean NLL was {number(selected.get('mean_nll'))}, "
            f"versus {number(token.get('mean_nll'))} for always-token and "
            f"{number(example.get('mean_nll'))} for always-example. Mean exact match "
            f"was {percent(selected.get('mean_exact'))}, versus "
            f"{percent(token.get('mean_exact'))} and {percent(example.get('mean_exact'))}.",
            "",
        ])
    lines.extend([
        "## Why this is bounded",
        "",
        boundary,
        "",
        "## Inspect and reproduce",
        "",
        "- [Detailed result](RESULTS.md)",
        "- [Frozen protocol](PROTOCOL.md)",
        "- [Methods](METHODS.md)",
        "- [Evidence provenance](PROVENANCE.md)",
        "- [Limitations](LIMITATIONS.md)",
        "- [Reproduction](REPRODUCE.md)",
        "- [Independent review](REVIEW.md)",
        "",
        "This is a local GitHub-ready artifact, not a publication or a remote repository.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    if not isinstance(result, dict):
        raise ValueError("RESULT must be a JSON object")
    print(render(result), end="")


if __name__ == "__main__":
    main()

