#!/usr/bin/env python3
"""Model-free determinism fixture for package manifest generation."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("manifest_builder_test", ROOT / "build_manifest.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import manifest builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory(prefix="rank-manifest-") as temp:
        root = Path(temp)
        (root / "z.txt").write_text("z\n")
        (root / "nested").mkdir()
        (root / "nested/a.txt").write_text("a\n")
        (root / "MANIFEST.sha256").write_text("must be excluded\n")
        first = module.manifest(root)
        second = module.manifest(root)
        if first != second:
            raise AssertionError("manifest is nondeterministic")
        lines = first.splitlines()
        if [line.split("  ", 1)[1] for line in lines] != ["nested/a.txt", "z.txt"]:
            raise AssertionError(f"manifest ordering/exclusion drift: {lines}")
        if not all(len(line.split("  ", 1)[0]) == 64 for line in lines):
            raise AssertionError("manifest digest length mismatch")

    print(json.dumps({
        "status": "PASS",
        "deterministic": True,
        "self_excluded": True,
        "sorted": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

