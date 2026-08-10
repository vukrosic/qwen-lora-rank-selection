#!/usr/bin/env python3
"""Export a rank classification without machine-local paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
CLASSIFICATIONS = {"TRANSFER_SUPPORTED", "NONTRANSFER_OR_MIXED", "INCONCLUSIVE_INVALID"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def absolute_strings(value: Any, prefix: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, str) and Path(value).is_absolute():
        found.append(prefix)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(absolute_strings(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(absolute_strings(item, f"{prefix}[{index}]"))
    return found


def export(source: dict, source_path: Path) -> dict:
    if source.get("protocol") != PROTOCOL_NAME:
        raise ValueError("source protocol identity mismatch")
    if source.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ValueError("source protocol hash mismatch")
    if source.get("rank") not in (4, 8):
        raise ValueError("source rank must be 4 or 8")
    if source.get("classification") not in CLASSIFICATIONS:
        raise ValueError("source classification is unknown")
    if not isinstance(source.get("errors"), list) or not isinstance(source.get("gates"), dict):
        raise ValueError("source validity fields are malformed")
    if not isinstance(source.get("evidence_fingerprints"), dict):
        raise ValueError("source evidence fingerprints are missing")

    result = deepcopy(source)
    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("source provenance is missing")
    run_location = provenance.get("runs")
    if not isinstance(run_location, str) or not Path(run_location).is_absolute():
        raise ValueError("source run location is not an absolute recorded path")
    provenance["runs"] = "runs"
    provenance["source_classification_sha256"] = sha256(source_path)
    provenance["portability_transform"] = (
        "machine-local provenance.runs replaced by package-relative runs; "
        "all scientific fields preserved"
    )
    leaks = absolute_strings(result)
    if leaks:
        raise ValueError(f"absolute paths remain after export: {leaks}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    if not isinstance(source, dict):
        raise ValueError("source classification must be a JSON object")
    result = export(source, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "classification": result["classification"],
        "rank": result["rank"],
        "source_sha256": result["provenance"]["source_classification_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

