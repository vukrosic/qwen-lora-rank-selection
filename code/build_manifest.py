#!/usr/bin/env python3
"""Print a deterministic SHA-256 manifest for the canonical package."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(root: Path) -> str:
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name != "MANIFEST.sha256"
    )
    return "".join(f"{sha256(path)}  {path.relative_to(root)}\n" for path in files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=PACKAGE)
    args = parser.parse_args()
    print(manifest(args.root.resolve()), end="")


if __name__ == "__main__":
    main()

