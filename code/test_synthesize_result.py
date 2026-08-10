#!/usr/bin/env python3
"""Model-free decision-tree fixtures for result integration."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parent


def load_module():
    path = PROJECT / "synthesize_result.py"
    spec = importlib.util.spec_from_file_location("synthesize_result_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import synthesizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def rank_result(module, rank: int, classification: str) -> dict:
    valid = classification != "INCONCLUSIVE_INVALID"
    supported = classification == "TRANSFER_SUPPORTED"
    return {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "rank": rank,
        "classification": classification,
        "errors": [] if valid else ["fixture invalid"],
        "gates": {
            "all_valid": valid,
            "selected_lower_nll_every_seed": supported,
        },
        "aggregates": {
            name: {"mean_nll": 0.1, "worst_nll": 0.2, "mean_exact": 0.7, "worst_exact": 0.6}
            for name in ("selected", "token", "example")
        },
        "rows": [],
    }


def main() -> None:
    module = load_module()
    historical = module.load_json(module.HISTORICAL_RESULT)
    with tempfile.TemporaryDirectory(prefix="rank-synthesis-") as temp:
        root = Path(temp)
        expected = {
            ("TRANSFER_SUPPORTED", None): "RANK4_TRANSFER_SUPPORTED",
            ("NONTRANSFER_OR_MIXED", None): "MATCHED_RANK8_REQUIRED",
            ("NONTRANSFER_OR_MIXED", "TRANSFER_SUPPORTED"): "RANK_SPECIFIC_BREAK",
            ("NONTRANSFER_OR_MIXED", "NONTRANSFER_OR_MIXED"): "MIXED_OR_SEED_BLOCK_INCONCLUSIVE",
            ("NONTRANSFER_OR_MIXED", "INCONCLUSIVE_INVALID"): "INCONCLUSIVE_INVALID_MATCHED_RANK8",
            ("INCONCLUSIVE_INVALID", None): "INCONCLUSIVE_INVALID",
        }
        observed = {}
        for index, ((rank4_class, rank8_class), outcome) in enumerate(expected.items()):
            rank4 = rank_result(module, 4, rank4_class)
            rank4_path = root / f"rank4-{index}.json"
            write_json(rank4_path, rank4)
            matched = None
            matched_path = None
            if rank8_class is not None:
                matched = rank_result(module, 8, rank8_class)
                matched_path = root / f"rank8-{index}.json"
                write_json(matched_path, matched)
            result = module.synthesize(
                rank4, historical, rank4_path, module.HISTORICAL_RESULT, matched, matched_path
            )
            if result["outcome"] != outcome:
                raise AssertionError(result)
            module.render_markdown(result)
            observed[f"{rank4_class}+{rank8_class}"] = outcome

        positive = rank_result(module, 4, "TRANSFER_SUPPORTED")
        positive_path = root / "positive.json"
        write_json(positive_path, positive)
        try:
            module.synthesize(
                positive, historical, positive_path, module.HISTORICAL_RESULT,
                rank_result(module, 8, "TRANSFER_SUPPORTED"), root / "unused.json",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("unexpected matched rank 8 accepted after supported rank 4")

        print(json.dumps({"status": "PASS", "decision_paths": observed}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
