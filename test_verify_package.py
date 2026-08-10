#!/usr/bin/env python3
"""Model-free scaffold and corruption fixtures for package verification."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("package_verifier_test", ROOT / "verify_package.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import package verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(root: Path, module) -> None:
    rows = [
        f"{module.sha256(path)}  {path.relative_to(root)}"
        for path in module.files(root)
        if path.name != "MANIFEST.sha256"
    ]
    (root / "MANIFEST.sha256").write_text("\n".join(rows) + "\n")


def write_margin_fixture(root: Path, module, rank4: dict) -> None:
    rank4_path = root / "evidence/rank4-classification.json"
    per_seed = []
    for row in rank4["rows"]:
        selected = row["selected_metrics"]
        other = row["other_metrics"]
        selected_count = round(selected["balanced_exact"] * 96)
        other_count = round(other["balanced_exact"] * 96)
        short_count = round(selected["short_exact"] * 48)
        long_count = round(selected["long_exact"] * 48)
        per_seed.append({
            "seed": row["seed"],
            "selected": row["selected"],
            "selected_exact_count_of_96": selected_count,
            "other_exact_count_of_96": other_count,
            "selected_minus_other_exact_records": selected_count - other_count,
            "selected_short_exact_count_of_48": short_count,
            "selected_long_exact_count_of_48": long_count,
            "other_minus_selected_nll": other["balanced_nll"] - selected["balanced_nll"],
        })
    selected = rank4["aggregates"]["selected"]
    comparisons = {}
    for name in ("token", "example"):
        baseline = rank4["aggregates"][name]
        comparisons[name] = {
            "selected_minus_baseline_mean_exact_records_of_288": (
                round(selected["mean_exact"] * 288) - round(baseline["mean_exact"] * 288)
            ),
            "selected_minus_baseline_worst_exact_records_of_96": (
                round(selected["worst_exact"] * 96) - round(baseline["worst_exact"] * 96)
            ),
            "baseline_minus_selected_mean_nll": baseline["mean_nll"] - selected["mean_nll"],
            "baseline_minus_selected_worst_nll": baseline["worst_nll"] - selected["worst_nll"],
        }
    margin = {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "rank": 4,
        "classification": rank4["classification"],
        "source_classification_sha256": module.sha256(rank4_path),
        "interpretation": module.MARGIN_INTERPRETATION,
        "per_seed": per_seed,
        "aggregate_comparisons": comparisons,
    }
    (root / "evidence/margins.json").write_text(json.dumps(margin, sort_keys=True) + "\n")


def build_final_fixture(root: Path, module) -> None:
    for name in module.COMMON_REQUIRED | module.FINAL_REQUIRED:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json" or path.name == "MANIFEST.sha256":
            continue
        path.write_text("fixture\n")
    source_classification_sha = "1" * 64
    accepted_raw = {
        f"rank4/seed{seed}/{condition}/{name}": "0" * 64
        for seed in (20260841, 20260842, 20260843)
        for condition in ("token", "example")
        for name in ("generations.jsonl", "teacher-forced.jsonl")
    }
    rank4 = {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "rank": 4,
        "classification": "TRANSFER_SUPPORTED",
        "errors": [],
        "gates": {"all_valid": True, "fixture_gate": True},
        "evidence_fingerprints": accepted_raw,
        "provenance": {"source_classification_sha256": source_classification_sha},
        "rows": [
            {
                "seed": seed,
                "selected": "token",
                "selected_metrics": {
                    "balanced_exact": selected_count / 96,
                    "short_exact": (selected_count // 2) / 48,
                    "long_exact": (selected_count - selected_count // 2) / 48,
                    "balanced_nll": 0.2,
                },
                "other_metrics": {
                    "balanced_exact": (selected_count - 2) / 96,
                    "balanced_nll": 0.3,
                },
            }
            for seed, selected_count in zip((20260841, 20260842, 20260843), (48, 50, 52))
        ],
        "aggregates": {
            "selected": {
                "mean_exact": 150 / 288, "worst_exact": 48 / 96,
                "mean_nll": 0.2, "worst_nll": 0.22,
            },
            "token": {
                "mean_exact": 138 / 288, "worst_exact": 45 / 96,
                "mean_nll": 0.25, "worst_nll": 0.27,
            },
            "example": {
                "mean_exact": 135 / 288, "worst_exact": 44 / 96,
                "mean_nll": 0.28, "worst_nll": 0.31,
            },
        },
    }
    rank4_path = root / "evidence/rank4-classification.json"
    rank4_path.write_text(json.dumps(rank4, sort_keys=True) + "\n")
    write_margin_fixture(root, module, rank4)
    historical_source = module.ROOT / "evidence/historical-rank8-result.json"
    (root / "evidence/historical-rank8-result.json").write_bytes(historical_source.read_bytes())
    for relative in module.DATA_SHA256:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((module.ROOT / relative).read_bytes())
    for relative in module.SOURCE_CODE_SHA256:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((module.ROOT / relative).read_bytes())
    for relative in module.PORTABLE_CODE_SHA256:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((module.ROOT / relative).read_bytes())
    for relative in module.EVIDENCE_SHA256:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((module.ROOT / relative).read_bytes())
    (root / "requirements.txt").write_bytes((module.ROOT / "requirements.txt").read_bytes())
    (root / "validation/preflight.json").write_bytes(
        (module.ROOT / "validation/preflight.json").read_bytes()
    )
    audit_path = root / "validation/data-audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_bytes((module.ROOT / "validation/data-audit.json").read_bytes())
    records = []
    for seed in (20260841, 20260842, 20260843):
        for condition in ("token", "example"):
            for kind in ("short", "long"):
                for index in range(2):
                    records.append({
                        "rank": 4,
                        "seed": seed,
                        "condition": condition,
                        "id": f"{kind}-{index}",
                        "kind": kind,
                        "prompt": "prompt",
                        "target": "target",
                        "generated": "target",
                        "normalized_target": "target",
                        "normalized_generated": "target",
                        "exact_match": True,
                        "supervised_tokens": 1,
                        "example_nll": 0.1,
                        "target_token_accuracy": 1.0,
                    })
    representative = {
        "rank": 4,
        "sampling_rule": (
            "lexicographically first two record IDs within each seed, condition, and "
            "short/long kind; fixed before outcomes"
        ),
        "source_classification_sha256": source_classification_sha,
        "records": records,
        "source_files": {
            f"rank4-seed{seed}-{condition}-eval/metrics/{name}": "0" * 64
            for seed in (20260841, 20260842, 20260843)
            for condition in ("token", "example")
            for name in ("generations.jsonl", "teacher-forced.jsonl")
        },
    }
    (root / "evidence/representative-records.json").write_text(
        json.dumps(representative, sort_keys=True) + "\n"
    )
    result = {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "outcome": "RANK4_TRANSFER_SUPPORTED",
        "terminal": True,
        "rank4": rank4,
        "matched_rank8": None,
        "matched_rank8_status": "SKIPPED_BY_PROTOCOL",
        "input_fingerprints": {
            "rank4_classification_sha256": module.sha256(rank4_path),
            "historical_rank8_result_sha256": module.HISTORICAL_RESULT_SHA256,
        },
    }
    (root / "evidence/RESULT.json").write_text(json.dumps(result, sort_keys=True) + "\n")
    (root / "README.md").write_text("RANK4_TRANSFER_SUPPORTED\n")
    (root / "RESULTS.md").write_text("RANK4_TRANSFER_SUPPORTED\n")
    write_manifest(root, module)


def configure_terminal_branch(root: Path, module, outcome: str) -> None:
    branches = {
        "INCONCLUSIVE_INVALID": ("INCONCLUSIVE_INVALID", "NOT_EARNED", None),
        "RANK_SPECIFIC_BREAK": ("NONTRANSFER_OR_MIXED", "COMPLETED", "TRANSFER_SUPPORTED"),
        "MIXED_OR_SEED_BLOCK_INCONCLUSIVE": (
            "NONTRANSFER_OR_MIXED", "COMPLETED", "NONTRANSFER_OR_MIXED"
        ),
        "INCONCLUSIVE_INVALID_MATCHED_RANK8": (
            "NONTRANSFER_OR_MIXED", "COMPLETED", "INCONCLUSIVE_INVALID"
        ),
    }
    rank4_class, matched_status, matched_class = branches[outcome]

    def rank_result(rank: int, classification: str) -> dict:
        valid = classification != "INCONCLUSIVE_INVALID"
        supported = classification == "TRANSFER_SUPPORTED"
        result = {
            "protocol": module.PROTOCOL_NAME,
            "protocol_sha256": module.PROTOCOL_SHA256,
            "rank": rank,
            "classification": classification,
            "errors": [] if valid else ["fixture invalid"],
            "gates": {"all_valid": valid, "fixture_gate": supported},
        }
        if rank == 4:
            previous = json.loads((root / "evidence/rank4-classification.json").read_text())
            result["evidence_fingerprints"] = previous["evidence_fingerprints"]
            result["provenance"] = previous["provenance"]
            result["rows"] = previous["rows"]
            result["aggregates"] = previous["aggregates"]
        return result

    rank4 = rank_result(4, rank4_class)
    rank4_path = root / "evidence/rank4-classification.json"
    rank4_path.write_text(json.dumps(rank4, sort_keys=True) + "\n")
    matched = None
    fingerprints = {
        "rank4_classification_sha256": module.sha256(rank4_path),
        "historical_rank8_result_sha256": module.HISTORICAL_RESULT_SHA256,
    }
    if matched_class is not None:
        matched = rank_result(8, matched_class)
        matched_path = root / "evidence/matched-rank8-classification.json"
        matched_path.write_text(json.dumps(matched, sort_keys=True) + "\n")
        fingerprints["matched_rank8_classification_sha256"] = module.sha256(matched_path)
    result = {
        "protocol": module.PROTOCOL_NAME,
        "protocol_sha256": module.PROTOCOL_SHA256,
        "outcome": outcome,
        "terminal": True,
        "rank4": rank4,
        "matched_rank8": matched,
        "matched_rank8_status": matched_status,
        "input_fingerprints": fingerprints,
    }
    (root / "evidence/RESULT.json").write_text(json.dumps(result, sort_keys=True) + "\n")
    (root / "README.md").write_text(outcome + "\n")
    (root / "RESULTS.md").write_text(outcome + "\n")
    if outcome == "INCONCLUSIVE_INVALID":
        (root / "evidence/representative-records.json").unlink()
        (root / "evidence/margins.json").unlink()
        omission = "REPRESENTATIVE_SAMPLE_UNAVAILABLE: fixture raw evidence is incomplete.\n"
        (root / "RESULTS.md").write_text(outcome + "\n" + omission)
        (root / "REVIEW.md").write_text(omission)
    else:
        write_margin_fixture(root, module, rank4)
    write_manifest(root, module)


def main() -> None:
    module = load_module()
    readme = (ROOT / "README.md").read_text()
    live_stage = "scaffold" if "NOT_RESULT_READY" in readme else "final"
    live = module.verify(ROOT, live_stage)
    if live["status"] != "PASS":
        raise AssertionError(live)
    with tempfile.TemporaryDirectory(prefix="rank-package-corrupt-") as temp:
        corrupt = Path(temp)
        for name in module.COMMON_REQUIRED:
            path = corrupt / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("NOT_RESULT_READY\n")
        private_path = "/" + "Users" + "/example/private"
        (corrupt / "README.md").write_text(f"NOT_RESULT_READY\n{private_path}\n")
        (corrupt / "weights.safetensors").write_bytes(b"not-real-weights")
        (corrupt / "metadata.json").write_text('{"temporary": "/private/tmp/run"}\n')
        result = module.verify(corrupt, "scaffold")
        if result["status"] != "FAIL":
            raise AssertionError(result)
        joined = "\n".join(result["errors"])
        if not all(message in joined for message in (
            "machine-specific absolute path", "weight forbidden", "absolute JSON path"
        )):
            raise AssertionError(result)
    with tempfile.TemporaryDirectory(prefix="rank-package-final-") as temp:
        complete = Path(temp)
        build_final_fixture(complete, module)
        final_pass = module.verify(complete, "final")
        if final_pass["status"] != "PASS":
            raise AssertionError(final_pass)

        root_git = complete / ".git/config"
        root_git.parent.mkdir()
        root_git.write_text("[core]\n")
        root_git_pass = module.verify(complete, "final")
        if root_git_pass["status"] != "PASS":
            raise AssertionError(root_git_pass)

        nested_git = complete / "nested/.git/config"
        nested_git.parent.mkdir(parents=True)
        nested_git.write_text("[core]\n")
        write_manifest(complete, module)
        nested_git_fail = module.verify(complete, "final")
        if nested_git_fail["status"] != "FAIL" or not any(
            "nested Git metadata" in error for error in nested_git_fail["errors"]
        ):
            raise AssertionError(nested_git_fail)
        nested_git.unlink()
        nested_git.parent.rmdir()
        nested_git.parent.parent.rmdir()
        write_manifest(complete, module)

        terminal_branches = {"RANK4_TRANSFER_SUPPORTED": final_pass["status"]}
        for outcome in (
            "INCONCLUSIVE_INVALID",
            "RANK_SPECIFIC_BREAK",
            "MIXED_OR_SEED_BLOCK_INCONCLUSIVE",
            "INCONCLUSIVE_INVALID_MATCHED_RANK8",
        ):
            with tempfile.TemporaryDirectory(prefix="rank-package-branch-") as branch_temp:
                branch_root = Path(branch_temp)
                build_final_fixture(branch_root, module)
                configure_terminal_branch(branch_root, module, outcome)
                branch_result = module.verify(branch_root, "final")
                if branch_result["status"] != "PASS":
                    raise AssertionError({"outcome": outcome, "result": branch_result})
                terminal_branches[outcome] = branch_result["status"]

        rank4_path = complete / "evidence/rank4-classification.json"
        rank4 = json.loads(rank4_path.read_text())
        rank4["classification"] = "NONTRANSFER_OR_MIXED"
        rank4_path.write_text(json.dumps(rank4, sort_keys=True) + "\n")
        (complete / "data/test.jsonl").write_text("{}\n")
        (complete / "code/imported/evaluate_condition.py").write_text("def broken(:\n")
        (complete / "README.md").write_text("RANK4_TRANSFER_SUPPORTED\n[missing](MISSING.md)\n")
        preflight_path = complete / "validation/preflight.json"
        preflight = json.loads(preflight_path.read_text())
        preflight["asset_hashes"]["model_weights"] = "0" * 64
        preflight_path.write_text(json.dumps(preflight, sort_keys=True) + "\n")
        representative_path = complete / "evidence/representative-records.json"
        representative = json.loads(representative_path.read_text())
        representative["source_files"][sorted(representative["source_files"])[0]] = "2" * 64
        representative_path.write_text(json.dumps(representative, sort_keys=True) + "\n")
        margin_path = complete / "evidence/margins.json"
        margin = json.loads(margin_path.read_text())
        margin["source_classification_sha256"] = "3" * 64
        margin_path.write_text(json.dumps(margin, sort_keys=True) + "\n")
        final_corrupt = module.verify(complete, "final")
        if final_corrupt["status"] != "FAIL":
            raise AssertionError(final_corrupt)
        joined = "\n".join(final_corrupt["errors"])
        required_errors = (
            "embedded rank-4 result differs",
            "fingerprint mismatch",
            "frozen data hash mismatch",
            "frozen source hash mismatch",
            "Python syntax error",
            "broken local link",
            "preflight asset fingerprints mismatch",
            "representative raw fingerprint differs",
            "margin audit classification fingerprint mismatch",
        )
        if not all(message in joined for message in required_errors):
            raise AssertionError(final_corrupt)
    print(json.dumps({
        "status": "PASS",
        "live_stage": live_stage,
        "live_root": live["status"],
        "corruption": result["status"],
        "corruption_errors": len(result["errors"]),
        "final_fixture": final_pass["status"],
        "root_git_fixture": root_git_pass["status"],
        "nested_git_fixture": nested_git_fail["status"],
        "final_corruption": final_corrupt["status"],
        "final_corruption_errors": len(final_corrupt["errors"]),
        "terminal_branches": terminal_branches,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
