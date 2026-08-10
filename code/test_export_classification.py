#!/usr/bin/env python3
"""Model-free preservation and leakage tests for classification export."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("classification_export_test", ROOT / "export_classification.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import classification exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="rank-export-") as temp:
        root = Path(temp)
        source = {
            "protocol": module.PROTOCOL_NAME,
            "protocol_sha256": module.PROTOCOL_SHA256,
            "rank": 4,
            "classification": "TRANSFER_SUPPORTED",
            "errors": [],
            "gates": {"all_valid": True},
            "rows": [{"seed": 20260841, "balanced_nll": 0.1}],
            "evidence_fingerprints": {"fixture": "0" * 64},
            "provenance": {"runs": str(root / "private-runs"), "analyzer_sha256": "1" * 64},
        }
        source_path = root / "source.json"
        source_path.write_text(json.dumps(source, sort_keys=True) + "\n")
        exported = module.export(source, source_path)
        if exported["rows"] != source["rows"] or exported["gates"] != source["gates"]:
            raise AssertionError("scientific fields changed")
        if exported["provenance"]["runs"] != "runs":
            raise AssertionError("run path was not made package-relative")
        if exported["provenance"]["source_classification_sha256"] != module.sha256(source_path):
            raise AssertionError("source fingerprint missing")
        if module.absolute_strings(exported):
            raise AssertionError("absolute path survived export")

        corrupt = dict(source)
        corrupt["unexpected"] = str(root / "secret")
        try:
            module.export(corrupt, source_path)
        except ValueError as exc:
            if "absolute paths remain" not in str(exc):
                raise
        else:
            raise AssertionError("nested absolute path was accepted")

    print(json.dumps({
        "status": "PASS",
        "scientific_fields_preserved": True,
        "nested_absolute_path": "REJECTED",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

