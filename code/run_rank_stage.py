#!/usr/bin/env python3
"""Run one explicitly authorized serialized rank stage and seal selections."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
PROJECT = Path(os.environ.get("RANK_ROBUSTNESS_SOURCE_PROJECT", PACKAGE))
ROOT = Path(os.environ.get("RANK_ROBUSTNESS_REPO_ROOT", PROJECT.parents[3]))
HISTORICAL = Path(os.environ.get(
    "RANK_ROBUSTNESS_HISTORICAL",
    ROOT / "initiatives/lora-loss-normalization-20260809/projects/qwen-lora-comparison",
))
MODEL = Path(os.environ.get("RANK_ROBUSTNESS_MODEL", "model-assets/Qwen3-0.6B-3bit"))
DATA = Path(os.environ.get("RANK_ROBUSTNESS_DATA", HISTORICAL / "data/v1"))
RUNS = Path(os.environ.get("RANK_ROBUSTNESS_RUNS", PROJECT / "runs"))
EXPECTED_PYTHON = Path(os.environ.get("RANK_ROBUSTNESS_PYTHON", sys.executable))
PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
RANK4_ANALYSIS = Path(os.environ.get(
    "RANK_ROBUSTNESS_RANK4_ANALYSIS", PROJECT / "rank4-classification.json"
))
RANK8_EARNED = Path(os.environ.get(
    "RANK_ROBUSTNESS_RANK8_EARNED", PROJECT / "rank8-control-earned.json"
))
PLAN = (
    (20260841, ("token", "example")),
    (20260842, ("example", "token")),
    (20260843, ("token", "example")),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command: list[str]) -> None:
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def require_frozen_interpreter() -> None:
    if not EXPECTED_PYTHON.exists():
        raise SystemExit(f"Frozen interpreter is missing: {EXPECTED_PYTHON}")
    try:
        matches = EXPECTED_PYTHON.samefile(Path(sys.executable))
    except OSError:
        matches = EXPECTED_PYTHON.resolve() == Path(sys.executable).resolve()
    if not matches:
        raise SystemExit(
            "Refusing launch through a non-frozen interpreter: "
            f"observed {sys.executable}; expected {EXPECTED_PYTHON}"
        )


def failed_substantive_gates(analysis: dict) -> list[str]:
    gates = analysis.get("gates")
    if not isinstance(gates, dict):
        return []
    return sorted(
        name for name, passed in gates.items()
        if name != "all_valid" and passed is False
    )


def recompute_rank4_analysis() -> dict:
    analyzer_path = PROJECT / "analyze_rank.py"
    spec = importlib.util.spec_from_file_location("rank8_gate_analyzer", analyzer_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load frozen analyzer: {analyzer_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.analyze(4, RUNS)


def validate_rank8_earned(path: Path = RANK8_EARNED) -> dict:
    """Reject an empty, stale, invalid, or non-substantive rank-8 marker."""
    if not path.is_file():
        raise ValueError(f"Rank-8 control has not been earned: missing {path}")
    try:
        record = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid rank-8 earned record: {exc}") from exc
    if not isinstance(record, dict):
        raise ValueError("Rank-8 earned record must be a JSON object")
    if not RANK4_ANALYSIS.is_file():
        raise ValueError(f"Missing exact rank-4 analysis: {RANK4_ANALYSIS}")
    try:
        analysis = json.loads(RANK4_ANALYSIS.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid rank-4 analysis: {exc}") from exc
    try:
        recomputed = recompute_rank4_analysis()
    except Exception as exc:
        raise ValueError(f"Cannot recompute rank-4 analysis from raw evidence: {exc}") from exc
    if analysis != recomputed:
        raise ValueError("Stored rank-4 analysis does not match recomputation from raw evidence")

    failures = failed_substantive_gates(analysis)
    rows = analysis.get("rows")
    observed_seeds = (
        [row.get("seed") for row in rows]
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
        else []
    )
    required_analysis = {
        "rank": 4,
        "protocol": PROTOCOL_NAME,
        "protocol_sha256": PROTOCOL_SHA256,
        "classification": "NONTRANSFER_OR_MIXED",
        "errors": [],
    }
    for key, expected in required_analysis.items():
        if analysis.get(key) != expected:
            raise ValueError(
                f"Rank-4 analysis does not earn rank 8: {key}="
                f"{analysis.get(key)!r}, expected {expected!r}"
            )
    if analysis.get("gates", {}).get("all_valid") is not True:
        raise ValueError("Rank-4 analysis is not valid")
    if not failures:
        raise ValueError("Rank-4 analysis has no failed substantive gate")
    if observed_seeds != [seed for seed, _ in PLAN]:
        raise ValueError(f"Rank-4 analysis seed block mismatch: {observed_seeds}")

    expected_record = {
        "schema_version": 1,
        "protocol": PROTOCOL_NAME,
        "protocol_sha256": PROTOCOL_SHA256,
        "rank4_analysis": RANK4_ANALYSIS.name,
        "rank4_analysis_sha256": sha256(RANK4_ANALYSIS),
        "rank4_classification": analysis["classification"],
        "rank4_all_valid": True,
        "failed_substantive_gates": failures,
        "fresh_seeds": [seed for seed, _ in PLAN],
        "earned_rank": 8,
        "only_changed_factor": "lora_rank_4_to_8",
    }
    if record != expected_record:
        raise ValueError(
            "Rank-8 earned record content does not match the exact valid "
            "rank-4 substantive failure"
        )
    return record


def train(rank: int, seed: int, condition: str) -> Path:
    run_dir = RUNS / f"rank{rank}-seed{seed}-{condition}"
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite: {run_dir}")
    execute(
        [
            str(EXPECTED_PYTHON), str(HISTORICAL / "run_capture.py"),
            "--run-dir", str(run_dir), "--", str(EXPECTED_PYTHON),
            str(PROJECT / "train_rank_condition.py"),
            "--model", str(MODEL), "--data", str(DATA),
            "--output", str(run_dir / "artifact"),
            "--condition", condition, "--seed", str(seed), "--rank", str(rank),
            "--iters", "576", "--batch-size", "4", "--num-layers", "8",
            "--learning-rate", "1e-4", "--max-seq-length", "128",
        ]
    )
    return run_dir


def final_validation_loss(run_dir: Path) -> float:
    matches = re.findall(
        r"Iter 576: Val loss ([0-9]+(?:\.[0-9]+)?)",
        (run_dir / "stdout.log").read_text(),
    )
    if len(matches) != 1:
        raise ValueError(f"Expected one final validation loss in {run_dir}")
    return float(matches[0])


def seal(rank: int, seed: int, arms: dict[str, Path]) -> None:
    losses = {name: final_validation_loss(path) for name, path in arms.items()}
    selected = "token" if losses["token"] <= losses["example"] else "example"
    record = {
        "protocol": PROTOCOL_NAME,
        "rank": rank,
        "seed": seed,
        "rule": "lower final validation loss at update 576; ties choose token",
        "final_validation_loss": losses,
        "selected_condition": selected,
        "test_evaluation_status_at_seal": "NOT_STARTED",
        "fingerprints": {
            "protocol.md": sha256(PROJECT / "PROTOCOL.md"),
            "train_rank_condition.py": sha256(PROJECT / "train_rank_condition.py"),
            "run_rank_stage.py": sha256(Path(__file__)),
            "historical_run_capture.py": sha256(HISTORICAL / "run_capture.py"),
            "historical_train_condition.py": sha256(HISTORICAL / "train_condition.py"),
            "historical_evaluate_condition.py": sha256(HISTORICAL / "evaluate_condition.py"),
            "data_manifest.json": sha256(DATA / "manifest.json"),
            "model.safetensors": sha256(MODEL / "model.safetensors"),
            "model_config.json": sha256(MODEL / "config.json"),
            **{
                f"{condition}_receipt.json": sha256(path / "receipt.json")
                for condition, path in arms.items()
            },
            **{
                f"{condition}_stdout.log": sha256(path / "stdout.log")
                for condition, path in arms.items()
            },
            **{
                f"{condition}_stderr.log": sha256(path / "stderr.log")
                for condition, path in arms.items()
            },
            **{
                f"{condition}_adapter_config.json": sha256(path / "artifact/adapter_config.json")
                for condition, path in arms.items()
            },
            **{
                f"{condition}_adapter.safetensors": sha256(path / "artifact/adapters.safetensors")
                for condition, path in arms.items()
            },
            **{
                f"{condition}_resource.json": sha256(path / "artifact/resource.json")
                for condition, path in arms.items()
            },
        },
    }
    output = RUNS / f"selection-rank{rank}-seed{seed}.json"
    with output.open("x") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("SEALED", json.dumps(record, sort_keys=True), flush=True)


def evaluate(rank: int, seed: int, condition: str, train_dir: Path) -> None:
    eval_dir = RUNS / f"rank{rank}-seed{seed}-{condition}-eval"
    if eval_dir.exists():
        raise FileExistsError(f"Refusing to overwrite: {eval_dir}")
    execute(
        [
            str(EXPECTED_PYTHON), str(HISTORICAL / "run_capture.py"),
            "--run-dir", str(eval_dir), "--", str(EXPECTED_PYTHON),
            str(HISTORICAL / "evaluate_condition.py"),
            "--model", str(MODEL), "--adapter", str(train_dir / "artifact"),
            "--data", str(DATA), "--output", str(eval_dir / "metrics"),
            "--label", f"rank{rank}-seed{seed}-{condition}",
            "--batch-size", "4", "--max-seq-length", "128",
            "--max-generation-tokens", "24",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", type=int, choices=(4, 8), required=True)
    parser.add_argument(
        "--confirmed-slot-grant",
        action="store_true",
        help="Required acknowledgement that the leader recorded an explicit slot grant.",
    )
    args = parser.parse_args()
    require_frozen_interpreter()
    if not args.confirmed_slot_grant:
        raise SystemExit("Refusing model launch without --confirmed-slot-grant")
    if sha256(PROJECT / "PROTOCOL.md") != PROTOCOL_SHA256:
        raise SystemExit("Frozen protocol hash changed; refusing launch")
    if args.rank == 8:
        try:
            validate_rank8_earned()
        except ValueError as exc:
            raise SystemExit(f"Rank-8 stage is conditional and not earned: {exc}") from exc

    RUNS.mkdir(parents=True, exist_ok=True)
    for seed, order in PLAN:
        arms = {condition: train(args.rank, seed, condition) for condition in order}
        seal(args.rank, seed, arms)
        for condition in order:
            evaluate(args.rank, seed, condition, arms[condition])


if __name__ == "__main__":
    main()
