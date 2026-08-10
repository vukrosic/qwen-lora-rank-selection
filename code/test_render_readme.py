#!/usr/bin/env python3
"""Model-free terminal-branch fixtures for README rendering."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("readme_renderer_test", ROOT / "render_readme.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import README renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    observed = {}
    aggregates = {
        name: {"mean_nll": 0.1, "mean_exact": 0.7}
        for name in ("selected", "token", "example")
    }
    for outcome in sorted(module.TERMINAL_OUTCOMES):
        text = module.render({
            "outcome": outcome,
            "terminal": True,
            "statement": "Fixture terminal statement.",
            "claim_boundary": "Fixture bounded scope.",
            "rank4": {"aggregates": aggregates},
        })
        if outcome not in text or "NOT_RESULT_READY" in text:
            raise AssertionError(f"outcome rendering failed: {outcome}")
        for target in ("RESULTS.md", "PROTOCOL.md", "REVIEW.md"):
            if target not in text:
                raise AssertionError(f"missing README link: {target}")
        observed[outcome] = "PASS"
    try:
        module.render({"outcome": "MATCHED_RANK8_REQUIRED", "terminal": False})
    except ValueError:
        nonterminal = "REJECTED"
    else:
        raise AssertionError("nonterminal result produced a final README")

    print(json.dumps({
        "status": "PASS",
        "terminal_branches": observed,
        "nonterminal": nonterminal,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

