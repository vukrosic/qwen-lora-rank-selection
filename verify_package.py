#!/usr/bin/env python3
"""Fail-closed model-free checks for the canonical evidence package."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMMON_REQUIRED = {
    ".gitignore", "README.md", "PACKAGE-STATE.md", "AGENTS.md",
    "LICENSE-NOT-SUPPLIED.md", "verify_package.py", "test_verify_package.py",
}
FINAL_REQUIRED = {
    "RESULTS.md", "PROTOCOL.md", "METHODS.md", "PROVENANCE.md",
    "LITERATURE.md",
    "LIMITATIONS.md", "AI-AUTHORSHIP.md", "REPRODUCE.md", "REVIEW.md",
    "REVIEW-SPEC.md",
    "MANIFEST.sha256",
    "evidence/RESULT.json", "evidence/rank4-classification.json",
    "evidence/historical-rank8-result.json",
    "data/manifest.json", "data/train.jsonl", "data/valid.jsonl", "data/test.jsonl",
    "code/analyze_rank.py", "code/synthesize_result.py",
    "code/run_rank_stage.py",
    "code/test_synthesize_result.py", "code/export_classification.py",
    "code/test_export_classification.py",
    "code/train_rank_condition.py", "code/imported/train_condition.py",
    "code/imported/evaluate_condition.py", "code/imported/run_capture.py",
    "code/audit_data.py", "validation/data-audit.json",
    "validation/rank-mechanism-audit.md",
    "code/export_evidence.py", "code/test_export_evidence.py",
    "requirements.txt",
    "code/build_manifest.py", "code/test_build_manifest.py",
    "code/export_preflight.py", "code/test_export_preflight.py",
    "validation/preflight.json",
    "code/render_readme.py", "code/test_render_readme.py",
    "validation/selector-precision.md",
    "code/audit_margins.py", "code/test_audit_margins.py",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".txt", ".sha256", ".toml", ".yaml", ".yml"}
USER_HOME_PREFIX = "/" + "Users" + "/"
PROTOCOL_NAME = "lora-selection-robustness-rank-1.0"
PROTOCOL_SHA256 = "d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58"
HISTORICAL_RESULT_SHA256 = "dab32943fbb882f7285e0ced94453af915d5bfbb0d4682a78f01dbf5d37f6a0d"
DATA_SHA256 = {
    "data/manifest.json": "6e4cbdeacfee45ed1b3d201d2168d52256e77f1e762d0ee523ca00b7d07efe71",
    "data/train.jsonl": "08051d9c2015eb5769aa165b2d45907e57ccf8327336dc9b6985c681615efca9",
    "data/valid.jsonl": "e63ce5a4a2c308ec0366e230f73a007150239a5d4579cdeb88507cbc4899d704",
    "data/test.jsonl": "0a6900dcdf3ff71885bcb18fc5df908f55b93daef2caad027d8e2f2044620899",
}
SOURCE_CODE_SHA256 = {
    "code/train_rank_condition.py": "3bdfdaa12bb17ea34f4292a77304220e2cc73bde4e7a6c5967bfbe79ee2e23dc",
    "code/imported/train_condition.py": "c59c687bad6b1a4b87160d7df3c9f1160adb80edbaa4a7be255810d453a4139d",
    "code/imported/evaluate_condition.py": "e4fe991feb32dc4ad7108eff4e88462fa85bcd39e1bfc2f9e918ec3b7a79f647",
    "code/imported/run_capture.py": "e8ba19d058c05064c42002644800d02fb014cf65bf4343e67d213b344abc150d",
}
PORTABLE_CODE_SHA256 = {
    "code/analyze_rank.py": "8bd29a0846587018323234bb89560c3851016c6ebb0dd7a5008f232603e2cb0a",
    "code/synthesize_result.py": "7615f111dccce12ce228daba1c92ea98953d52eabf739787ea2add66476d1042",
    "code/run_rank_stage.py": "a3e756f17399530aed6ecaf32cb57c6a9c04aa6f4ca7882acc3a3ed6ffbe10a5",
}
EVIDENCE_SHA256 = {
    "validation/rank-mechanism-audit.md": "d154cc5df5adbc70e3c315f2d7e9ac938268c1c4b541e290022875e1d02ec318",
    "REVIEW-SPEC.md": "b8d131ad03387f03c6a11d13a08f17fa2af8f521d518d63e5c1df44f860ff20c",
    "validation/selector-precision.md": "016b6ae13e8b20cb7e0dbf1e287ff91eb76c5038336edb696cadfec3a823401f",
}
PREFLIGHT_SOURCE_SHA256 = "679e07fc82e3153aaafe2b86d53ed2fc783047ef308a6c7f2346693aafff68ee"
PREFLIGHT_ASSETS = {
    "model_config": "7319e769e58a8d819f67a83b3d413624a4a143dccde0d0d326b223ca74f71157",
    "model_weights": "add1354a3e8ddf16fd4308ce9556b2b11c0b6e45863f8898e28e0a0bb8ae18e8",
    "mlx_lm_lora_source": "4d3a8edab111d4ddba33398ba8700203db7b61621c39e9c348fdd50e57278b45",
    "mlx_lm_trainer_source": "ee33ebdbd20a184108541cb490d08085485e71a82ffd6d68d7d216029ecd28fe",
    "mlx_lm_utils_source": "166eaf5e5f923113bed43614a5fb7319795fa0cac5a7fa319ea54e5f0045b553",
    "data_manifest": "6e4cbdeacfee45ed1b3d201d2168d52256e77f1e762d0ee523ca00b7d07efe71",
    "historical_evaluator": "e4fe991feb32dc4ad7108eff4e88462fa85bcd39e1bfc2f9e918ec3b7a79f647",
    "historical_run_capture": "e8ba19d058c05064c42002644800d02fb014cf65bf4343e67d213b344abc150d",
    "historical_trainer": "c59c687bad6b1a4b87160d7df3c9f1160adb80edbaa4a7be255810d453a4139d",
    "protocol": PROTOCOL_SHA256,
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
TERMINAL_OUTCOMES = {
    "RANK4_TRANSFER_SUPPORTED",
    "INCONCLUSIVE_INVALID",
    "RANK_SPECIFIC_BREAK",
    "MIXED_OR_SEED_BLOCK_INCONCLUSIVE",
    "INCONCLUSIVE_INVALID_MATCHED_RANK8",
}
MARGIN_INTERPRETATION = (
    "descriptive frozen-gate margins only; not a significance test or confidence interval"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def strict_json(path: Path) -> dict:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant {value}")

    value = json.loads(path.read_text(), parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def absolute_json_locations(value, prefix: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, str) and Path(value).is_absolute():
        found.append(prefix)
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and Path(key).is_absolute():
                found.append(f"{prefix}.<key>")
            found.extend(absolute_json_locations(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(absolute_json_locations(item, f"{prefix}[{index}]"))
    return found


def verify_rank_evidence(value: dict, rank: int, label: str, errors: list[str]) -> None:
    if value.get("protocol") != PROTOCOL_NAME or value.get("protocol_sha256") != PROTOCOL_SHA256:
        errors.append(f"{label} protocol identity mismatch")
    if value.get("rank") != rank:
        errors.append(f"{label} rank mismatch")
    classification = value.get("classification")
    rank_errors = value.get("errors")
    gates = value.get("gates")
    if classification not in {"TRANSFER_SUPPORTED", "NONTRANSFER_OR_MIXED", "INCONCLUSIVE_INVALID"}:
        errors.append(f"{label} classification is unknown")
        return
    if not isinstance(rank_errors, list) or not isinstance(gates, dict):
        errors.append(f"{label} validity fields are malformed")
        return
    substantive = [passed for name, passed in gates.items() if name != "all_valid"]
    if classification == "INCONCLUSIVE_INVALID":
        if not rank_errors or gates.get("all_valid") is not False:
            errors.append(f"{label} invalid classification lacks invalid evidence")
    else:
        if rank_errors or gates.get("all_valid") is not True:
            errors.append(f"{label} substantive classification is not valid")
    if classification == "TRANSFER_SUPPORTED" and (not substantive or not all(value is True for value in substantive)):
        errors.append(f"{label} supported classification has a failed gate")
    if classification == "NONTRANSFER_OR_MIXED" and not any(value is False for value in substantive):
        errors.append(f"{label} non-transfer classification lacks a failed gate")


def grid_count(value, denominator: int) -> int | None:
    if (
        not isinstance(value, (int, float)) or isinstance(value, bool)
        or not math.isfinite(value) or not 0 <= value <= 1
    ):
        return None
    count = round(value * denominator)
    return count if math.isclose(value, count / denominator, rel_tol=0, abs_tol=1e-12) else None


def finite_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def verify_margins(root: Path, rank4: dict, outcome: str, errors: list[str]) -> None:
    path = root / "evidence/margins.json"
    if outcome == "INCONCLUSIVE_INVALID":
        if path.exists():
            errors.append("unexpected substantive margin audit for invalid rank 4")
        return
    if not path.is_file():
        errors.append("missing exact-count/NLL margin audit for substantive rank 4")
        return
    try:
        margin = strict_json(path)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        errors.append(f"unreadable margin audit: {exc}")
        return
    if (
        margin.get("protocol") != PROTOCOL_NAME
        or margin.get("protocol_sha256") != PROTOCOL_SHA256
        or margin.get("rank") != 4
        or margin.get("classification") != rank4.get("classification")
    ):
        errors.append("margin audit identity mismatch")
    if margin.get("source_classification_sha256") != sha256(root / "evidence/rank4-classification.json"):
        errors.append("margin audit classification fingerprint mismatch")
    if margin.get("interpretation") != MARGIN_INTERPRETATION:
        errors.append("margin audit interpretation boundary mismatch")
    rows = rank4.get("rows")
    reported_rows = margin.get("per_seed")
    if not isinstance(rows, list) or not isinstance(reported_rows, list) or len(rows) != 3 or len(reported_rows) != 3:
        errors.append("margin audit seed rows malformed")
        return
    for source, reported in zip(rows, reported_rows):
        if not isinstance(source, dict) or not isinstance(reported, dict):
            errors.append("margin audit contains a malformed seed row")
            continue
        selected = source.get("selected_metrics", {})
        other = source.get("other_metrics", {})
        if not isinstance(selected, dict) or not isinstance(other, dict):
            errors.append(f"rank-4 metrics malformed for seed {source.get('seed')}")
            continue
        selected_count = grid_count(selected.get("balanced_exact"), 96)
        other_count = grid_count(other.get("balanced_exact"), 96)
        short_count = grid_count(selected.get("short_exact"), 48)
        long_count = grid_count(selected.get("long_exact"), 48)
        if None in (selected_count, other_count, short_count, long_count):
            errors.append(f"rank-4 exact rates are off-grid for seed {source.get('seed')}")
            continue
        if not finite_number(other.get("balanced_nll")) or not finite_number(selected.get("balanced_nll")):
            errors.append(f"rank-4 NLL is non-finite for seed {source.get('seed')}")
            continue
        expected = {
            "seed": source.get("seed"),
            "selected": source.get("selected"),
            "selected_exact_count_of_96": selected_count,
            "other_exact_count_of_96": other_count,
            "selected_minus_other_exact_records": selected_count - other_count,
            "selected_short_exact_count_of_48": short_count,
            "selected_long_exact_count_of_48": long_count,
            "other_minus_selected_nll": other.get("balanced_nll") - selected.get("balanced_nll"),
        }
        if reported != expected:
            errors.append(f"margin audit seed row mismatch: {source.get('seed')}")
    aggregates = rank4.get("aggregates", {})
    reported_comparisons = margin.get("aggregate_comparisons")
    if not isinstance(aggregates, dict):
        errors.append("rank-4 aggregate metrics malformed")
        return
    if not isinstance(reported_comparisons, dict):
        errors.append("margin audit aggregate comparisons malformed")
        return
    selected = aggregates.get("selected", {})
    if not isinstance(selected, dict):
        errors.append("selected aggregate metrics malformed")
        return
    for baseline_name in ("token", "example"):
        baseline = aggregates.get(baseline_name, {})
        if not isinstance(baseline, dict):
            errors.append(f"aggregate metrics malformed for {baseline_name}")
            continue
        counts = (
            grid_count(selected.get("mean_exact"), 288),
            grid_count(baseline.get("mean_exact"), 288),
            grid_count(selected.get("worst_exact"), 96),
            grid_count(baseline.get("worst_exact"), 96),
        )
        if None in counts:
            errors.append(f"aggregate exact rates are off-grid for {baseline_name}")
            continue
        nll_values = (
            baseline.get("mean_nll"), selected.get("mean_nll"),
            baseline.get("worst_nll"), selected.get("worst_nll"),
        )
        if not all(finite_number(value) for value in nll_values):
            errors.append(f"aggregate NLL is non-finite for {baseline_name}")
            continue
        expected = {
            "selected_minus_baseline_mean_exact_records_of_288": counts[0] - counts[1],
            "selected_minus_baseline_worst_exact_records_of_96": counts[2] - counts[3],
            "baseline_minus_selected_mean_nll": baseline.get("mean_nll") - selected.get("mean_nll"),
            "baseline_minus_selected_worst_nll": baseline.get("worst_nll") - selected.get("worst_nll"),
        }
        if reported_comparisons.get(baseline_name) != expected:
            errors.append(f"margin audit aggregate mismatch: {baseline_name}")


def verify_result_bundle(root: Path, readme: str, errors: list[str]) -> None:
    result_path = root / "evidence/RESULT.json"
    rank4_path = root / "evidence/rank4-classification.json"
    if not result_path.is_file() or not rank4_path.is_file():
        return
    try:
        result = strict_json(result_path)
        rank4 = strict_json(rank4_path)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        errors.append(f"unreadable result evidence: {exc}")
        return

    if result.get("terminal") is not True:
        errors.append("final RESULT.json is not terminal")
    outcome = result.get("outcome")
    if outcome not in TERMINAL_OUTCOMES:
        errors.append(f"unknown or nonterminal outcome: {outcome!r}")
    if not isinstance(outcome, str) or outcome not in readme:
        errors.append("README does not contain exact terminal outcome")
    results_md = (root / "RESULTS.md").read_text() if (root / "RESULTS.md").is_file() else ""
    if isinstance(outcome, str) and outcome not in results_md:
        errors.append("RESULTS.md does not contain exact terminal outcome")
    if result.get("protocol") != PROTOCOL_NAME or result.get("protocol_sha256") != PROTOCOL_SHA256:
        errors.append("RESULT.json protocol identity mismatch")
    verify_rank_evidence(rank4, 4, "rank-4 classification", errors)
    if result.get("rank4") != rank4:
        errors.append("embedded rank-4 result differs from packaged classification")
    fingerprints = result.get("input_fingerprints")
    if not isinstance(fingerprints, dict):
        errors.append("missing result input fingerprints")
        fingerprints = {}
    if fingerprints.get("rank4_classification_sha256") != sha256(rank4_path):
        errors.append("rank-4 classification fingerprint mismatch")
    if fingerprints.get("historical_rank8_result_sha256") != HISTORICAL_RESULT_SHA256:
        errors.append("historical rank-8 fingerprint mismatch")
    historical_path = root / "evidence/historical-rank8-result.json"
    if historical_path.is_file() and sha256(historical_path) != HISTORICAL_RESULT_SHA256:
        errors.append("packaged historical rank-8 result hash mismatch")

    rank4_class = rank4.get("classification")
    matched = result.get("matched_rank8")
    matched_status = result.get("matched_rank8_status")
    expected = {
        "RANK4_TRANSFER_SUPPORTED": ("TRANSFER_SUPPORTED", "SKIPPED_BY_PROTOCOL", None),
        "INCONCLUSIVE_INVALID": ("INCONCLUSIVE_INVALID", "NOT_EARNED", None),
        "RANK_SPECIFIC_BREAK": ("NONTRANSFER_OR_MIXED", "COMPLETED", "TRANSFER_SUPPORTED"),
        "MIXED_OR_SEED_BLOCK_INCONCLUSIVE": ("NONTRANSFER_OR_MIXED", "COMPLETED", "NONTRANSFER_OR_MIXED"),
        "INCONCLUSIVE_INVALID_MATCHED_RANK8": ("NONTRANSFER_OR_MIXED", "COMPLETED", "INCONCLUSIVE_INVALID"),
    }.get(outcome)
    if expected is not None:
        expected_rank4, expected_status, expected_matched = expected
        if rank4_class != expected_rank4 or matched_status != expected_status:
            errors.append("terminal outcome branch is inconsistent with rank-4/status fields")
        if expected_matched is None:
            if matched is not None or (root / "evidence/matched-rank8-classification.json").exists():
                errors.append("unexpected matched rank-8 evidence for terminal branch")
        else:
            matched_path = root / "evidence/matched-rank8-classification.json"
            if not matched_path.is_file():
                errors.append("missing matched rank-8 classification")
            else:
                try:
                    packaged_matched = strict_json(matched_path)
                    if matched != packaged_matched:
                        errors.append("embedded matched rank-8 result differs from packaged classification")
                    verify_rank_evidence(packaged_matched, 8, "matched rank-8 classification", errors)
                    if packaged_matched.get("classification") != expected_matched:
                        errors.append("matched rank-8 classification is inconsistent with outcome")
                    if fingerprints.get("matched_rank8_classification_sha256") != sha256(matched_path):
                        errors.append("matched rank-8 classification fingerprint mismatch")
                except (json.JSONDecodeError, OSError, ValueError) as exc:
                    errors.append(f"unreadable matched rank-8 evidence: {exc}")
    representative_path = root / "evidence/representative-records.json"
    if outcome != "INCONCLUSIVE_INVALID" and not representative_path.is_file():
        errors.append("missing representative records for substantive rank-4 evidence")
    if outcome == "INCONCLUSIVE_INVALID" and not representative_path.is_file():
        for relative in ("RESULTS.md", "REVIEW.md"):
            text = (root / relative).read_text() if (root / relative).is_file() else ""
            if "REPRESENTATIVE_SAMPLE_UNAVAILABLE:" not in text:
                errors.append(f"{relative} lacks invalid-evidence sample-omission reason")
    verify_margins(root, rank4, outcome, errors)


def verify_data_audit(root: Path, errors: list[str]) -> None:
    path = root / "validation/data-audit.json"
    if not path.is_file():
        return
    try:
        audit = strict_json(path)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        errors.append(f"unreadable data audit: {exc}")
        return
    expected_true = (
        "same_key_sets_across_splits",
        "one_target_per_key_across_splits",
        "record_ids_disjoint_across_splits",
        "literal_prompts_disjoint_across_splits",
    )
    if audit.get("status") != "PASS" or audit.get("errors") != []:
        errors.append("frozen data audit did not pass")
    if not all(audit.get(name) is True for name in expected_true):
        errors.append("frozen data audit boundary flags mismatch")
    split_counts = {
        name: audit.get("splits", {}).get(name, {}).get("records")
        for name in ("train", "valid", "test")
    }
    if split_counts != {"train": 384, "valid": 96, "test": 96}:
        errors.append("frozen data audit split counts mismatch")


def verify_representative_records(root: Path, errors: list[str]) -> None:
    path = root / "evidence/representative-records.json"
    if not path.is_file():
        return
    try:
        sample = strict_json(path)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        errors.append(f"unreadable representative records: {exc}")
        return
    records = sample.get("records")
    if sample.get("rank") != 4 or not isinstance(records, list) or len(records) != 24:
        errors.append("representative rank-4 sample shape mismatch")
        records = []
    if sample.get("sampling_rule") != (
        "lexicographically first two record IDs within each seed, condition, and "
        "short/long kind; fixed before outcomes"
    ):
        errors.append("representative sampling rule mismatch")
    source_files = sample.get("source_files")
    expected_source_files = {
        f"rank4-seed{seed}-{condition}-eval/metrics/{name}"
        for seed in (20260841, 20260842, 20260843)
        for condition in ("token", "example")
        for name in ("generations.jsonl", "teacher-forced.jsonl")
    }
    if not isinstance(source_files, dict) or set(source_files) != expected_source_files:
        errors.append("representative source fingerprint count mismatch")
    elif not all(
        isinstance(name, str) and re.fullmatch(r"[0-9a-f]{64}", digest or "")
        for name, digest in source_files.items()
    ):
        errors.append("representative source fingerprints are malformed")
    classification_path = root / "evidence/rank4-classification.json"
    if classification_path.is_file() and isinstance(source_files, dict):
        try:
            classification = strict_json(classification_path)
            provenance = classification.get("provenance")
            accepted = classification.get("evidence_fingerprints")
            source_classification_sha = (
                provenance.get("source_classification_sha256")
                if isinstance(provenance, dict) else None
            )
            if (
                not re.fullmatch(r"[0-9a-f]{64}", source_classification_sha or "")
                or sample.get("source_classification_sha256") != source_classification_sha
            ):
                errors.append("representative source classification fingerprint mismatch")
            if not isinstance(accepted, dict):
                errors.append("rank-4 classification lacks accepted evidence fingerprints")
            else:
                for seed in (20260841, 20260842, 20260843):
                    for condition in ("token", "example"):
                        for name in ("generations.jsonl", "teacher-forced.jsonl"):
                            sample_key = f"rank4-seed{seed}-{condition}-eval/metrics/{name}"
                            analyzer_key = f"rank4/seed{seed}/{condition}/{name}"
                            if source_files.get(sample_key) != accepted.get(analyzer_key):
                                errors.append(
                                    "representative raw fingerprint differs from analyzer-accepted "
                                    f"evidence: {analyzer_key}"
                                )
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            errors.append(f"cannot bind representative records to rank-4 evidence: {exc}")
    expected_combinations = Counter({
        (seed, condition, kind): 2
        for seed in (20260841, 20260842, 20260843)
        for condition in ("token", "example")
        for kind in ("short", "long")
    })
    if records and not all(isinstance(row, dict) for row in records):
        errors.append("representative records contain a non-object")
    elif records:
        observed_combinations = Counter(
            (row.get("seed"), row.get("condition"), row.get("kind"))
            for row in records
        )
        if observed_combinations != expected_combinations:
            errors.append("representative seed/condition/kind coverage mismatch")
        required_fields = {
            "rank", "seed", "condition", "id", "kind", "prompt", "target",
            "generated", "normalized_target", "normalized_generated",
            "exact_match", "supervised_tokens", "example_nll",
            "target_token_accuracy",
        }
        if any(set(row) != required_fields for row in records):
            errors.append("representative record fields mismatch")


def verify_manifest(root: Path, errors: list[str]) -> None:
    manifest = root / "MANIFEST.sha256"
    if not manifest.is_file():
        errors.append("missing MANIFEST.sha256")
        return
    listed = {}
    for number, line in enumerate(manifest.read_text().splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            errors.append(f"malformed manifest line {number}")
            continue
        rel = parts[1].removeprefix("./")
        if rel in listed:
            errors.append(f"duplicate manifest path on line {number}: {rel}")
            continue
        listed[rel] = parts[0]
    actual = {
        str(path.relative_to(root)): sha256(path)
        for path in files(root)
        if path.name != "MANIFEST.sha256"
    }
    if listed != actual:
        missing = sorted(set(actual) - set(listed))
        extra = sorted(set(listed) - set(actual))
        changed = sorted(name for name in set(actual) & set(listed) if actual[name] != listed[name])
        errors.append(f"manifest mismatch missing={missing} extra={extra} changed={changed}")


def verify_local_links(root: Path, errors: list[str]) -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in files(root):
        if path.suffix.lower() != ".md":
            continue
        for target in pattern.findall(path.read_text(errors="replace")):
            clean = target.strip().strip("<>").split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if not (path.parent / clean).resolve().is_file():
                errors.append(f"broken local link in {path.relative_to(root)}: {target}")


def verify_requirements(root: Path, errors: list[str]) -> None:
    path = root / "requirements.txt"
    if not path.is_file():
        return
    observed = path.read_text().splitlines()
    expected = ["mlx==0.31.2", "mlx-lm==0.31.3", "numpy==2.2.5"]
    if observed != expected:
        errors.append(f"requirements drift: {observed}")


def verify_preflight(root: Path, errors: list[str]) -> None:
    path = root / "validation/preflight.json"
    if not path.is_file():
        return
    try:
        preflight = strict_json(path)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        errors.append(f"unreadable preflight evidence: {exc}")
        return
    if preflight.get("status") != "PASS" or preflight.get("errors") != []:
        errors.append("packaged preflight did not pass cleanly")
    if preflight.get("qwen_loaded") is not False:
        errors.append("packaged preflight unexpectedly loaded Qwen")
    if preflight.get("frozen_seeds") != [20260841, 20260842, 20260843]:
        errors.append("packaged preflight seed block mismatch")
    if preflight.get("source_preflight_sha256") != PREFLIGHT_SOURCE_SHA256:
        errors.append("packaged preflight source fingerprint mismatch")
    if preflight.get("asset_hashes") != PREFLIGHT_ASSETS:
        errors.append("packaged preflight asset fingerprints mismatch")
    environment = preflight.get("environment")
    if environment != {"python": "frozen-interpreter", "mlx": "0.31.2", "mlx-lm": "0.31.3"}:
        errors.append("packaged preflight environment mismatch")


def verify(root: Path, stage: str) -> dict:
    errors: list[str] = []
    present = {str(path.relative_to(root)) for path in files(root)}
    missing_common = sorted(COMMON_REQUIRED - present)
    if missing_common:
        errors.append(f"missing common files: {missing_common}")
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".git" in rel_parts:
            errors.append(f"nested Git metadata: {path.relative_to(root)}")
        if "__pycache__" in rel_parts or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"cache artifact: {path.relative_to(root)}")
        if path.is_file() and path.stat().st_size > 2_000_000:
            errors.append(f"oversized file: {path.relative_to(root)}")
        if path.is_file() and (path.suffix == ".safetensors" or "adapter" in path.name.lower() and path.suffix == ".npz"):
            errors.append(f"model/adapter weight forbidden: {path.relative_to(root)}")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(errors="replace")
            if USER_HOME_PREFIX in text:
                errors.append(f"machine-specific absolute path: {path.relative_to(root)}")
            if path.suffix == ".py":
                try:
                    ast.parse(text)
                except SyntaxError as exc:
                    errors.append(f"Python syntax error in {path.relative_to(root)}: {exc}")
            if path.suffix.lower() in {".json", ".jsonl"}:
                try:
                    values = (
                        [json.loads(line) for line in text.splitlines() if line.strip()]
                        if path.suffix.lower() == ".jsonl" else [json.loads(text)]
                    )
                    locations = [
                        location
                        for index, value in enumerate(values)
                        for location in absolute_json_locations(value, f"$[{index}]")
                    ]
                    if locations:
                        errors.append(
                            f"absolute JSON path in {path.relative_to(root)}: {locations[:3]}"
                        )
                except (json.JSONDecodeError, OSError, ValueError) as exc:
                    errors.append(f"unreadable JSON artifact {path.relative_to(root)}: {exc}")

    readme = (root / "README.md").read_text() if (root / "README.md").is_file() else ""
    if stage == "scaffold":
        if "NOT_RESULT_READY" not in readme:
            errors.append("scaffold lacks explicit NOT_RESULT_READY marker")
    else:
        missing_final = sorted(FINAL_REQUIRED - present)
        if missing_final:
            errors.append(f"missing final files: {missing_final}")
        if "NOT_RESULT_READY" in readme:
            errors.append("final package still carries NOT_RESULT_READY marker")
        verify_result_bundle(root, readme, errors)
        verify_data_audit(root, errors)
        verify_representative_records(root, errors)
        verify_local_links(root, errors)
        verify_requirements(root, errors)
        verify_preflight(root, errors)
        for relative, digest in DATA_SHA256.items():
            data_path = root / relative
            if data_path.is_file() and sha256(data_path) != digest:
                errors.append(f"frozen data hash mismatch: {relative}")
        for relative, digest in SOURCE_CODE_SHA256.items():
            source_path = root / relative
            if source_path.is_file() and sha256(source_path) != digest:
                errors.append(f"frozen source hash mismatch: {relative}")
        for relative, digest in PORTABLE_CODE_SHA256.items():
            portable_path = root / relative
            if portable_path.is_file() and sha256(portable_path) != digest:
                errors.append(f"portable decision-code hash mismatch: {relative}")
        for relative, digest in EVIDENCE_SHA256.items():
            evidence_path = root / relative
            if evidence_path.is_file() and sha256(evidence_path) != digest:
                errors.append(f"frozen evidence hash mismatch: {relative}")
        verify_manifest(root, errors)
    return {
        "status": "PASS" if not errors else "FAIL",
        "stage": stage,
        "errors": errors,
        "files": len(present),
        "qwen_loaded": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--stage", choices=("scaffold", "final"), default="final")
    args = parser.parse_args()
    result = verify(args.root.resolve(), args.stage)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
