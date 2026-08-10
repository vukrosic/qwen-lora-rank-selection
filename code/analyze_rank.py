#!/usr/bin/env python3
"""Fail-closed classifier for one completed frozen rank block."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


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
TRAINER_SHA256 = "3bdfdaa12bb17ea34f4292a77304220e2cc73bde4e7a6c5967bfbe79ee2e23dc"
HISTORICAL_TRAIN_SHA256 = "c59c687bad6b1a4b87160d7df3c9f1160adb80edbaa4a7be255810d453a4139d"
EVALUATOR_SHA256 = "e4fe991feb32dc4ad7108eff4e88462fa85bcd39e1bfc2f9e918ec3b7a79f647"
RUN_CAPTURE_SHA256 = "e8ba19d058c05064c42002644800d02fb014cf65bf4343e67d213b344abc150d"
DATA_SHA256 = "6e4cbdeacfee45ed1b3d201d2168d52256e77f1e762d0ee523ca00b7d07efe71"
MODEL_SHA256 = "add1354a3e8ddf16fd4308ce9556b2b11c0b6e45863f8898e28e0a0bb8ae18e8"
MODEL_CONFIG_SHA256 = "7319e769e58a8d819f67a83b3d413624a4a143dccde0d0d326b223ca74f71157"
SEEDS = (20260841, 20260842, 20260843)
CONDITIONS = ("token", "example")
RULE = "lower final validation loss at update 576; ties choose token"
EXPECTED_DATASET_VALIDATION = {
    "train": {
        "kinds": {"long": 192, "short": 192},
        "records": 384,
        "supervised_tokens_max": 14,
        "supervised_tokens_min": 3,
        "supervised_tokens_total": 2860,
    },
    "valid": {
        "kinds": {"long": 48, "short": 48},
        "records": 96,
        "supervised_tokens_max": 14,
        "supervised_tokens_min": 3,
        "supervised_tokens_total": 715,
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"expected JSON objects: {path}")
    return rows


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def recursively_finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(recursively_finite(item) for item in value.values())
    if isinstance(value, list):
        return all(recursively_finite(item) for item in value)
    return True


def equal_float(observed: Any, expected: float, *, tolerance: float = 1e-12) -> bool:
    return finite_number(observed) and math.isclose(
        float(observed), float(expected), rel_tol=tolerance, abs_tol=tolerance
    )


def check_equal(errors: list[str], observed: Any, expected: Any, label: str) -> None:
    if observed != expected:
        errors.append(f"{label} mismatch: observed {observed!r}, expected {expected!r}")


def check_float(errors: list[str], observed: Any, expected: float, label: str) -> None:
    if not equal_float(observed, expected):
        errors.append(f"{label} mismatch or non-finite: observed {observed!r}, expected {expected!r}")


def expected_asset_hashes() -> dict[str, tuple[Path, str]]:
    return {
        "protocol.md": (PROJECT / "PROTOCOL.md", PROTOCOL_SHA256),
        "train_rank_condition.py": (PROJECT / "train_rank_condition.py", TRAINER_SHA256),
        "historical_train_condition.py": (HISTORICAL / "train_condition.py", HISTORICAL_TRAIN_SHA256),
        "historical_evaluate_condition.py": (HISTORICAL / "evaluate_condition.py", EVALUATOR_SHA256),
        "data_manifest.json": (DATA / "manifest.json", DATA_SHA256),
        "model.safetensors": (MODEL / "model.safetensors", MODEL_SHA256),
        "model_config.json": (MODEL / "config.json", MODEL_CONFIG_SHA256),
    }


def verify_frozen_assets(errors: list[str]) -> None:
    for name, (path, expected) in expected_asset_hashes().items():
        try:
            observed = sha256(path)
        except OSError as exc:
            errors.append(f"missing frozen asset {name}: {exc}")
            continue
        if observed != expected:
            errors.append(f"frozen asset hash mismatch {name}: {observed}")
    if sha256(HISTORICAL / "run_capture.py") != RUN_CAPTURE_SHA256:
        errors.append("frozen asset hash mismatch historical_run_capture.py")


def expected_train_command(rank: int, seed: int, condition: str, train_dir: Path) -> list[str]:
    return [
        str(EXPECTED_PYTHON), str(PROJECT / "train_rank_condition.py"),
        "--model", str(MODEL), "--data", str(DATA),
        "--output", str(train_dir / "artifact"),
        "--condition", condition, "--seed", str(seed), "--rank", str(rank),
        "--iters", "576", "--batch-size", "4", "--num-layers", "8",
        "--learning-rate", "1e-4", "--max-seq-length", "128",
    ]


def expected_eval_command(rank: int, seed: int, condition: str, train_dir: Path, eval_dir: Path) -> list[str]:
    return [
        str(EXPECTED_PYTHON), str(HISTORICAL / "evaluate_condition.py"),
        "--model", str(MODEL), "--adapter", str(train_dir / "artifact"),
        "--data", str(DATA), "--output", str(eval_dir / "metrics"),
        "--label", f"rank{rank}-seed{seed}-{condition}",
        "--batch-size", "4", "--max-seq-length", "128",
        "--max-generation-tokens", "24",
    ]


def verify_receipt(
    errors: list[str], receipt: dict, expected_command: list[str], label: str
) -> tuple[datetime, datetime] | None:
    check_equal(errors, receipt.get("status"), "COMPLETED", f"{label} receipt status")
    check_equal(errors, receipt.get("exit_code"), 0, f"{label} receipt exit code")
    check_equal(errors, receipt.get("command"), expected_command, f"{label} receipt command")
    check_equal(errors, receipt.get("cwd"), str(ROOT), f"{label} receipt cwd")
    if not finite_number(receipt.get("wall_seconds")) or receipt["wall_seconds"] <= 0:
        errors.append(f"{label} receipt has invalid wall_seconds")
    for field in ("launcher_pid", "child_pid"):
        if not isinstance(receipt.get(field), int) or isinstance(receipt.get(field), bool):
            errors.append(f"{label} receipt has invalid {field}")
    try:
        started = datetime.fromisoformat(receipt["started_at"])
        ended = datetime.fromisoformat(receipt["ended_at"])
        if started.tzinfo is None or ended.tzinfo is None or ended < started:
            raise ValueError("invalid receipt timestamps")
        return started, ended
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"{label} receipt time invalid: {exc}")
        return None


def parse_training_log(errors: list[str], text: str, label: str) -> float | None:
    if "Starting training..., iters: 576" not in text:
        errors.append(f"{label} did not declare 576 updates")
    train_reports = re.findall(r"Iter (\d+): Train loss ([^,\s]+)", text)
    observed_updates = [int(update) for update, _ in train_reports]
    expected_updates = list(range(24, 577, 24))
    if observed_updates != expected_updates:
        errors.append(f"{label} train report updates mismatch: {observed_updates}")
    for update, loss in train_reports:
        try:
            if not math.isfinite(float(loss)):
                raise ValueError
        except ValueError:
            errors.append(f"{label} non-finite train loss at update {update}: {loss}")
    val_reports = re.findall(r"Iter (\d+): Val loss ([^,\s]+)", text)
    expected_val_updates = [1, 96, 192, 288, 384, 480, 576]
    if [int(update) for update, _ in val_reports] != expected_val_updates:
        errors.append(f"{label} validation report updates mismatch")
    for update, loss in val_reports:
        try:
            if not math.isfinite(float(loss)):
                raise ValueError
        except ValueError:
            errors.append(f"{label} non-finite validation loss at update {update}: {loss}")
    final = []
    for update, loss in val_reports:
        if update != "576":
            continue
        try:
            value = float(loss)
        except ValueError:
            continue
        if math.isfinite(value):
            final.append(value)
    if len(final) != 1:
        errors.append(f"{label} has no unique finite final validation loss")
        return None
    return final[0]


def verify_config(
    errors: list[str], config: dict, rank: int, seed: int, condition: str, label: str
) -> None:
    expected_manifest = load_json(DATA / "manifest.json")
    exact = {
        "protocol": PROTOCOL_NAME,
        "model": str(MODEL),
        "fine_tune_type": "lora",
        "num_layers": 8,
        "lora_parameters": {"rank": rank, "dropout": 0.0, "scale": 20.0},
        "condition": condition,
        "seed": seed,
        "batch_size": 4,
        "iters": 576,
        "learning_rate": 0.0001,
        "max_seq_length": 128,
        "dataset_validation": EXPECTED_DATASET_VALIDATION,
        "data_manifest": expected_manifest,
    }
    for key, expected in exact.items():
        check_equal(errors, config.get(key), expected, f"{label} config {key}")
    expected_fingerprints = {
        name: expected for name, (_, expected) in expected_asset_hashes().items()
        if name != "run_rank_stage.py"
    }
    check_equal(errors, config.get("fingerprints"), expected_fingerprints, f"{label} config fingerprints")
    environment = config.get("environment", {})
    check_equal(errors, environment.get("python_executable"), str(EXPECTED_PYTHON), f"{label} Python")
    check_equal(errors, environment.get("mlx"), "0.31.2", f"{label} MLX version")
    check_equal(errors, environment.get("mlx-lm"), "0.31.3", f"{label} MLX-LM version")


def verify_resource(errors: list[str], resource: dict, rank: int, seed: int, condition: str, label: str) -> None:
    for key, expected in {"rank": rank, "seed": seed, "condition": condition}.items():
        check_equal(errors, resource.get(key), expected, f"{label} resource {key}")
    for field in ("wall_seconds", "peak_mlx_memory_gb", "cache_memory_gb"):
        value = resource.get(field)
        if not finite_number(value) or value < 0:
            errors.append(f"{label} resource has invalid {field}")


def normalized(text: str) -> str:
    return " ".join(text.strip().split())


def frozen_test_index() -> dict[str, dict]:
    rows = load_jsonl(DATA / "test.jsonl")
    index = {row["id"]: row for row in rows}
    if len(rows) != 96 or len(index) != 96:
        raise ValueError("frozen test data does not contain 96 unique IDs")
    return index


def aggregate_teacher(rows: list[dict], kind: str) -> dict[str, float | int]:
    subset = [row for row in rows if row["kind"] == kind]
    tokens = sum(row["supervised_tokens"] for row in subset)
    return {
        "examples": len(subset),
        "example_nll_mean": sum(row["example_nll"] for row in subset) / len(subset),
        "token_nll": sum(row["loss_sum"] for row in subset) / tokens,
        "target_token_accuracy": sum(row["correct_tokens"] for row in subset) / tokens,
    }


def verify_metric_block(errors: list[str], observed: dict, expected: dict, label: str) -> None:
    check_equal(errors, set(observed), set(expected), f"{label} keys")
    for key, value in expected.items():
        if isinstance(value, float):
            check_float(errors, observed.get(key), value, f"{label} {key}")
        else:
            check_equal(errors, observed.get(key), value, f"{label} {key}")


def verify_metrics(
    errors: list[str], data: dict, teacher_rows: list[dict], generation_rows: list[dict],
    rank: int, seed: int, condition: str, train_dir: Path, label: str,
) -> dict[str, float]:
    if not recursively_finite(data) or not recursively_finite(teacher_rows) or not recursively_finite(generation_rows):
        errors.append(f"{label} contains non-finite numeric metrics")
    index = frozen_test_index()
    expected_ids = set(index)
    teacher_ids = [row.get("id") for row in teacher_rows]
    generation_ids = [row.get("id") for row in generation_rows]
    if len(teacher_rows) != 96 or len(teacher_ids) != len(set(teacher_ids)) or set(teacher_ids) != expected_ids:
        errors.append(f"{label} teacher rows do not match 96 frozen test IDs")
    if len(generation_rows) != 96 or len(generation_ids) != len(set(generation_ids)) or set(generation_ids) != expected_ids:
        errors.append(f"{label} generation rows do not match 96 frozen test IDs")

    valid_teacher = True
    for row in teacher_rows:
        row_id = row.get("id")
        frozen = index.get(row_id, {})
        if row.get("kind") != frozen.get("kind"):
            valid_teacher = False
            continue
        count = row.get("supervised_tokens")
        loss_sum = row.get("loss_sum")
        example_nll = row.get("example_nll")
        correct = row.get("correct_tokens")
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            valid_teacher = False
        elif not finite_number(loss_sum) or loss_sum < 0 or not equal_float(example_nll, loss_sum / count):
            valid_teacher = False
        elif not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct <= count:
            valid_teacher = False
    if not valid_teacher:
        errors.append(f"{label} malformed teacher-forced row")

    valid_generation = True
    for row in generation_rows:
        row_id = row.get("id")
        frozen = index.get(row_id, {})
        if row.get("kind") != frozen.get("kind"):
            valid_generation = False
        if row.get("prompt") != frozen.get("prompt") or row.get("target") != frozen.get("completion"):
            valid_generation = False
        if row.get("normalized_target") != normalized(str(frozen.get("completion", ""))):
            valid_generation = False
        if row.get("normalized_generated") != normalized(str(row.get("generated", ""))):
            valid_generation = False
        if not isinstance(row.get("exact_match"), bool):
            valid_generation = False
        elif row["exact_match"] != (row.get("normalized_target") == row.get("normalized_generated")):
            valid_generation = False
    if not valid_generation:
        errors.append(f"{label} malformed generation row")

    if not valid_teacher or not valid_generation or len(teacher_rows) != 96 or len(generation_rows) != 96:
        nan_metrics = {key: math.nan for key in ("balanced_nll", "balanced_exact", "short_exact", "long_exact")}
        return nan_metrics

    teacher = {kind: aggregate_teacher(teacher_rows, kind) for kind in ("long", "short")}
    generation = {}
    for kind in ("long", "short"):
        exact = sum(row["exact_match"] for row in generation_rows if row.get("kind") == kind) / 48
        generation[kind] = {**teacher[kind], "exact_match": exact}
        verify_metric_block(errors, data.get("teacher_forced", {}).get(kind, {}), teacher[kind], f"{label} teacher {kind}")
        verify_metric_block(errors, data.get("generation", {}).get(kind, {}), generation[kind], f"{label} generation {kind}")

    expected_summary = {
        "balanced_exact_match": (generation["short"]["exact_match"] + generation["long"]["exact_match"]) / 2,
        "worst_skill_exact_match": min(generation["short"]["exact_match"], generation["long"]["exact_match"]),
        "short_minus_long_exact_gap": generation["short"]["exact_match"] - generation["long"]["exact_match"],
        "balanced_example_nll": (teacher["short"]["example_nll_mean"] + teacher["long"]["example_nll_mean"]) / 2,
        "balanced_target_token_accuracy": (teacher["short"]["target_token_accuracy"] + teacher["long"]["target_token_accuracy"]) / 2,
    }
    verify_metric_block(errors, data.get("summary", {}), expected_summary, f"{label} summary")
    check_equal(errors, data.get("label"), f"rank{rank}-seed{seed}-{condition}", f"{label} metrics label")
    check_equal(errors, data.get("adapter"), str(train_dir / "artifact"), f"{label} metrics adapter")
    check_equal(errors, data.get("test_scope"), "held-out prompt template over training facts; not held-out facts", f"{label} test scope")
    check_equal(errors, data.get("normalization"), "strip outer whitespace and collapse internal whitespace; case-sensitive", f"{label} normalization")
    expected_fingerprints = {
        "evaluate_condition.py": EVALUATOR_SHA256,
        "data_manifest.json": DATA_SHA256,
        "model.safetensors": MODEL_SHA256,
        "model_config.json": MODEL_CONFIG_SHA256,
        "adapter_config.json": sha256(train_dir / "artifact/adapter_config.json"),
        "adapters.safetensors": sha256(train_dir / "artifact/adapters.safetensors"),
    }
    check_equal(errors, data.get("fingerprints"), expected_fingerprints, f"{label} metrics fingerprints")
    environment = data.get("environment", {})
    check_equal(errors, environment.get("python_executable"), str(EXPECTED_PYTHON), f"{label} eval Python")
    check_equal(errors, environment.get("mlx"), "0.31.2", f"{label} eval MLX")
    check_equal(errors, environment.get("mlx-lm"), "0.31.3", f"{label} eval MLX-LM")
    resource = data.get("resource", {})
    for field in ("wall_seconds", "peak_mlx_memory_gb", "active_mlx_memory_gb", "cache_mlx_memory_gb"):
        value = resource.get(field)
        if not finite_number(value) or value < 0:
            errors.append(f"{label} metrics resource has invalid {field}")
    return {
        "balanced_nll": expected_summary["balanced_example_nll"],
        "balanced_exact": expected_summary["balanced_exact_match"],
        "short_exact": generation["short"]["exact_match"],
        "long_exact": generation["long"]["exact_match"],
    }


def analyze(rank: int, runs: Path) -> dict:
    errors: list[str] = []
    verify_frozen_assets(errors)
    rows: list[dict] = []
    policy: dict[str, list[dict]] = {condition: [] for condition in CONDITIONS}
    selected_rows: list[dict] = []
    evidence_fingerprints: dict[str, str] = {}
    manifest = load_json(DATA / "manifest.json")

    for seed in SEEDS:
        selection_path = runs / f"selection-rank{rank}-seed{seed}.json"
        try:
            selection = load_json(selection_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"unreadable selection for seed {seed}: {exc}")
            continue
        evidence_fingerprints[f"rank{rank}/seed{seed}/selection.json"] = sha256(selection_path)
        for key, expected in {
            "protocol": PROTOCOL_NAME,
            "rank": rank,
            "seed": seed,
            "rule": RULE,
            "test_evaluation_status_at_seal": "NOT_STARTED",
        }.items():
            check_equal(errors, selection.get(key), expected, f"selection seed {seed} {key}")

        metrics: dict[str, dict] = {}
        train_ends: list[datetime] = []
        eval_starts: list[datetime] = []
        expected_selection_fingerprints = {
            "protocol.md": PROTOCOL_SHA256,
            "train_rank_condition.py": TRAINER_SHA256,
            "run_rank_stage.py": sha256(PROJECT / "run_rank_stage.py"),
            "historical_run_capture.py": RUN_CAPTURE_SHA256,
            "historical_train_condition.py": HISTORICAL_TRAIN_SHA256,
            "historical_evaluate_condition.py": EVALUATOR_SHA256,
            "data_manifest.json": DATA_SHA256,
            "model.safetensors": MODEL_SHA256,
            "model_config.json": MODEL_CONFIG_SHA256,
        }
        parsed_losses: dict[str, float] = {}

        for condition in CONDITIONS:
            label = f"rank {rank} seed {seed} {condition}"
            train_dir = runs / f"rank{rank}-seed{seed}-{condition}"
            eval_dir = runs / f"rank{rank}-seed{seed}-{condition}-eval"
            try:
                train_receipt = load_json(train_dir / "receipt.json")
                eval_receipt = load_json(eval_dir / "receipt.json")
                config = load_json(train_dir / "artifact/adapter_config.json")
                resource = load_json(train_dir / "artifact/resource.json")
                data = load_json(eval_dir / "metrics/metrics.json")
                teacher_rows = load_jsonl(eval_dir / "metrics/teacher-forced.jsonl")
                generation_rows = load_jsonl(eval_dir / "metrics/generations.jsonl")
                stdout = (train_dir / "stdout.log").read_text()
                (train_dir / "stderr.log").read_text()
                adapter_path = train_dir / "artifact/adapters.safetensors"
                adapter_path.stat()
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"unreadable artifact {label}: {exc}")
                continue

            train_window = verify_receipt(
                errors, train_receipt,
                expected_train_command(rank, seed, condition, train_dir),
                f"{label} train",
            )
            eval_window = verify_receipt(
                errors, eval_receipt,
                expected_eval_command(rank, seed, condition, train_dir, eval_dir),
                f"{label} eval",
            )
            if train_window is not None:
                train_ends.append(train_window[1])
            if eval_window is not None:
                eval_starts.append(eval_window[0])
            if train_window is not None and eval_window is not None and eval_window[0] < train_window[1]:
                errors.append(f"evaluation started before training ended for {label}")
            verify_config(errors, config, rank, seed, condition, label)
            verify_resource(errors, resource, rank, seed, condition, label)
            parsed_loss = parse_training_log(errors, stdout, label)
            if parsed_loss is not None:
                parsed_losses[condition] = parsed_loss
            metrics[condition] = verify_metrics(
                errors, data, teacher_rows, generation_rows, rank, seed, condition, train_dir, label
            )

            expected_selection_fingerprints.update({
                f"{condition}_receipt.json": sha256(train_dir / "receipt.json"),
                f"{condition}_stdout.log": sha256(train_dir / "stdout.log"),
                f"{condition}_stderr.log": sha256(train_dir / "stderr.log"),
                f"{condition}_adapter_config.json": sha256(train_dir / "artifact/adapter_config.json"),
                f"{condition}_adapter.safetensors": sha256(adapter_path),
                f"{condition}_resource.json": sha256(train_dir / "artifact/resource.json"),
            })
            evidence_fingerprints.update({
                f"rank{rank}/seed{seed}/{condition}/train-receipt.json": sha256(train_dir / "receipt.json"),
                f"rank{rank}/seed{seed}/{condition}/train-stdout.log": sha256(train_dir / "stdout.log"),
                f"rank{rank}/seed{seed}/{condition}/train-stderr.log": sha256(train_dir / "stderr.log"),
                f"rank{rank}/seed{seed}/{condition}/adapter-config.json": sha256(train_dir / "artifact/adapter_config.json"),
                f"rank{rank}/seed{seed}/{condition}/adapter.safetensors": sha256(adapter_path),
                f"rank{rank}/seed{seed}/{condition}/train-resource.json": sha256(train_dir / "artifact/resource.json"),
                f"rank{rank}/seed{seed}/{condition}/eval-receipt.json": sha256(eval_dir / "receipt.json"),
                f"rank{rank}/seed{seed}/{condition}/metrics.json": sha256(eval_dir / "metrics/metrics.json"),
                f"rank{rank}/seed{seed}/{condition}/teacher-forced.jsonl": sha256(eval_dir / "metrics/teacher-forced.jsonl"),
                f"rank{rank}/seed{seed}/{condition}/generations.jsonl": sha256(eval_dir / "metrics/generations.jsonl"),
            })

        check_equal(errors, selection.get("fingerprints"), expected_selection_fingerprints, f"selection seed {seed} fingerprints")
        check_equal(errors, selection.get("final_validation_loss"), parsed_losses, f"selection seed {seed} final losses")
        if len(eval_starts) == 2 and len(train_ends) == 2:
            selection_mtime = datetime.fromtimestamp(selection_path.stat().st_mtime, tz=eval_starts[0].tzinfo)
            if not all(ended <= selection_mtime for ended in train_ends):
                errors.append(f"selection sealed before both trainings ended for seed {seed}")
            if not all(selection_mtime <= started for started in eval_starts):
                errors.append(f"selection sealed after evaluation start for seed {seed}")
        else:
            selection_mtime = None

        selected = selection.get("selected_condition")
        if set(parsed_losses) == set(CONDITIONS):
            expected_selected = "token" if parsed_losses["token"] <= parsed_losses["example"] else "example"
            check_equal(errors, selected, expected_selected, f"selection seed {seed} selected condition")
        if selected not in CONDITIONS or set(metrics) != set(CONDITIONS):
            errors.append(f"incomplete selectable metrics for seed {seed}")
            continue
        other = "example" if selected == "token" else "token"
        chosen = metrics[selected]
        selected_rows.append(chosen)
        policy[selected].append(chosen)
        policy[other].append(metrics[other])
        rows.append({
            "seed": seed,
            "selected": selected,
            "selected_metrics": chosen,
            "other_metrics": metrics[other],
            "selection_mtime": selection_mtime.isoformat() if selection_mtime else None,
            "last_train_end": max(train_ends).isoformat() if train_ends else None,
            "first_eval_start": min(eval_starts).isoformat() if eval_starts else None,
        })

    def aggregate(items: list[dict]) -> dict:
        if len(items) != len(SEEDS) or not recursively_finite(items):
            return {key: None for key in ("mean_nll", "worst_nll", "mean_exact", "worst_exact")}
        return {
            "mean_nll": sum(row["balanced_nll"] for row in items) / len(items),
            "worst_nll": max(row["balanced_nll"] for row in items),
            "mean_exact": sum(row["balanced_exact"] for row in items) / len(items),
            "worst_exact": min(row["balanced_exact"] for row in items),
        }

    complete = (
        len(rows) == len(SEEDS)
        and all(len(items) == len(SEEDS) for items in policy.values())
        and recursively_finite(rows)
    )
    aggregates = {
        "selected": aggregate(selected_rows),
        "token": aggregate(policy["token"]),
        "example": aggregate(policy["example"]),
    }
    if not complete:
        errors.append("rank block does not contain three complete seed pairs")
    gates = {
        "all_valid": not errors,
        "selected_lower_nll_every_seed": complete and all(row["selected_metrics"]["balanced_nll"] < row["other_metrics"]["balanced_nll"] for row in rows),
        "selected_exact_within_5pp_every_seed": complete and all(row["selected_metrics"]["balanced_exact"] >= row["other_metrics"]["balanced_exact"] - 0.05 for row in rows),
        "selected_mean_nll_lower_than_both": complete and all(aggregates["selected"]["mean_nll"] < aggregates[name]["mean_nll"] for name in CONDITIONS),
        "selected_worst_nll_lower_than_both": complete and all(aggregates["selected"]["worst_nll"] < aggregates[name]["worst_nll"] for name in CONDITIONS),
        "selected_mean_exact_higher_than_both": complete and all(aggregates["selected"]["mean_exact"] > aggregates[name]["mean_exact"] for name in CONDITIONS),
        "selected_worst_exact_higher_than_both": complete and all(aggregates["selected"]["worst_exact"] > aggregates[name]["worst_exact"] for name in CONDITIONS),
        "headroom_two_seeds": complete and sum(
            0.10 < row["balanced_exact"] < 0.90 and row["short_exact"] > 0.05 and row["long_exact"] > 0.05
            for row in selected_rows
        ) >= 2,
    }
    supported = all(gates.values())
    return {
        "protocol": PROTOCOL_NAME,
        "protocol_sha256": PROTOCOL_SHA256,
        "rank": rank,
        "classification": "TRANSFER_SUPPORTED" if supported else ("INCONCLUSIVE_INVALID" if errors else "NONTRANSFER_OR_MIXED"),
        "errors": errors,
        "gates": gates,
        "aggregates": aggregates,
        "rows": rows,
        "evidence_fingerprints": evidence_fingerprints,
        "provenance": {
            "analyzer_sha256": sha256(Path(__file__)),
            "run_rank_stage_sha256": sha256(PROJECT / "run_rank_stage.py"),
            "runs": str(runs.resolve()),
            "frozen_data_manifest": manifest,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rank", type=int, choices=(4, 8), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runs", type=Path, default=RUNS)
    args = parser.parse_args()
    output = analyze(args.rank, args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
