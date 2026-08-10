#!/usr/bin/env python3
"""Model-free preservation test for portable preflight export."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("preflight_export_test", ROOT / "export_preflight.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import preflight exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="rank-preflight-export-") as temp:
        root = Path(temp)
        source = {
            "status": "PASS",
            "errors": [],
            "qwen_loaded": False,
            "asset_hashes": {
                str(root / f"asset-{index}"): digest
                for index, digest in enumerate(module.EXPECTED_ASSETS.values())
            },
            "environment": {"python": str(root / "python"), "mlx": "0.31.2", "mlx-lm": "0.31.3"},
            "frozen_seeds": [20260841, 20260842, 20260843],
        }
        source_path = root / "preflight.json"
        source_path.write_text(json.dumps(source, sort_keys=True) + "\n")
        result = module.export(source, source_path)
        if result["frozen_seeds"] != source["frozen_seeds"]:
            raise AssertionError("preflight check result changed")
        if result["source_preflight_sha256"] != module.sha256(source_path):
            raise AssertionError("source preflight hash missing")
        if module.absolute_strings(result):
            raise AssertionError("absolute path survived preflight export")

    print(json.dumps({
        "status": "PASS",
        "checks_preserved": True,
        "absolute_paths": "REMOVED",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

