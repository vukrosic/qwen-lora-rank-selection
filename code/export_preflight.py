#!/usr/bin/env python3
"""Export the passing model-free preflight without host-specific paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


EXPECTED_ASSETS = {
    "model_config": "7319e769e58a8d819f67a83b3d413624a4a143dccde0d0d326b223ca74f71157",
    "model_weights": "add1354a3e8ddf16fd4308ce9556b2b11c0b6e45863f8898e28e0a0bb8ae18e8",
    "mlx_lm_lora_source": "4d3a8edab111d4ddba33398ba8700203db7b61621c39e9c348fdd50e57278b45",
    "mlx_lm_trainer_source": "ee33ebdbd20a184108541cb490d08085485e71a82ffd6d68d7d216029ecd28fe",
    "mlx_lm_utils_source": "166eaf5e5f923113bed43614a5fb7319795fa0cac5a7fa319ea54e5f0045b553",
    "data_manifest": "6e4cbdeacfee45ed1b3d201d2168d52256e77f1e762d0ee523ca00b7d07efe71",
    "historical_evaluator": "e4fe991feb32dc4ad7108eff4e88462fa85bcd39e1bfc2f9e918ec3b7a79f647",
    "historical_run_capture": "e8ba19d058c05064c42002644800d02fb014cf65bf4343e67d213b344abc150d",
    "historical_trainer": "c59c687bad6b1a4b87160d7df3c9f1160adb80edbaa4a7be255810d453a4139d",
    "protocol": "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58",
    "analyzer": "158b62e9f56fce3ef2eb6a080198387077a4f42ad7b93a92479bf44ab87c67b8",
    "runner": "d2d13c3dd532932d170599805894a661f9e6bbeca1ca3648aa1046174223c2d3",
    "synthesizer": "6486388fb0263ac3b300b2dceee23a14e64f6648202575a7ecd4d8d15bf2b7dd",
    "test_analyzer": "d1df9eca57bdea8e40717f29668a7e1bded9845a6b4d3837078227bcc2fe0c1f",
    "test_rank8_gate": "7f274e8838523ae5db0e6025765e220ebfe7f1c87998aab586bd9d45be27e6e6",
    "test_runner_plan": "d3c0647a5d9ca1713524f171fecda9913095f4d2d9cdbb14dfa0a91fa5053181",
    "test_synthesizer": "2bcacffc9b613c1b56df891b41c5d038e08f97f073f6f5084864b0c20fae98fe",
    "rank_trainer": "3bdfdaa12bb17ea34f4292a77304220e2cc73bde4e7a6c5967bfbe79ee2e23dc",
    "rank8_earned_builder": "6a3df7920ee7051de1b855dc7367466f5641b304410807e7f8a403c7ff65eeb8",
    "test_rank8_earned_builder": "aaf4b9cfca6362589c678ad23e9a89200667caaf3b5fa1e5e08c5e7c2be4af78",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def absolute_strings(value: Any, prefix: str = "$") -> list[str]:
    found = []
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
    if source.get("status") != "PASS" or source.get("errors") != []:
        raise ValueError("source preflight did not pass cleanly")
    if source.get("qwen_loaded") is not False:
        raise ValueError("source preflight loaded Qwen")
    observed = source.get("asset_hashes")
    if not isinstance(observed, dict) or sorted(observed.values()) != sorted(EXPECTED_ASSETS.values()):
        raise ValueError("source preflight asset set mismatch")
    environment = source.get("environment")
    if not isinstance(environment, dict):
        raise ValueError("source preflight environment missing")
    if environment.get("mlx") != "0.31.2" or environment.get("mlx-lm") != "0.31.3":
        raise ValueError("source preflight package versions mismatch")

    result = deepcopy(source)
    result["asset_hashes"] = dict(sorted(EXPECTED_ASSETS.items()))
    result["environment"]["python"] = "frozen-interpreter"
    result["source_preflight_sha256"] = sha256(source_path)
    result["portability_transform"] = (
        "absolute asset keys replaced by logical labels and interpreter path "
        "replaced by frozen-interpreter; all checks/results preserved"
    )
    leaks = absolute_strings(result)
    if leaks:
        raise ValueError(f"absolute paths remain after preflight export: {leaks}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    if not isinstance(source, dict):
        raise ValueError("source preflight must be a JSON object")
    result = export(source, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "source_sha256": result["source_preflight_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
