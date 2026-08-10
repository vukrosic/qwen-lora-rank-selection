#!/usr/bin/env python3
"""Train one frozen rank/normalization condition using audited prior semantics."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import time
from pathlib import Path

import mlx.core as mx
import mlx.optimizers as optim
from mlx_lm import load
from mlx_lm.tuner.trainer import TrainingArgs, train
from mlx_lm.tuner.utils import linear_to_lora_layers, print_trainable_parameters


PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]
HISTORICAL = ROOT / "initiatives/lora-loss-normalization-20260809/projects/qwen-lora-comparison"
sys.path.insert(0, str(HISTORICAL))
from train_condition import (  # noqa: E402
    BalancedMixedIterator,
    MixedDataset,
    example_mean_loss,
    token_mean_loss,
    validate_dataset,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lora_parameters(rank: int) -> dict:
    if rank not in (4, 8):
        raise ValueError("Frozen protocol permits only rank 4 or rank 8")
    return {"rank": rank, "dropout": 0.0, "scale": 20.0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--condition", choices=("token", "example"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--rank", type=int, choices=(4, 8), required=True)
    parser.add_argument("--iters", type=int, default=576)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--max-seq-length", type=int, default=128)
    args = parser.parse_args()

    if args.iters != 576 or args.batch_size != 4 or args.num_layers != 8:
        raise ValueError("Frozen endpoint requires 576 updates, batch 4, and 8 layers")
    if args.learning_rate != 1e-4 or args.max_seq_length != 128:
        raise ValueError("Frozen learning rate/sequence length changed")
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    mx.reset_peak_memory()
    mx.random.seed(args.seed)
    import numpy as np

    np.random.seed(args.seed)
    started = time.time()
    model, tokenizer = load(str(args.model))
    model.freeze()
    rank_config = lora_parameters(args.rank)
    linear_to_lora_layers(model, args.num_layers, rank_config)
    print_trainable_parameters(model)

    train_data = MixedDataset(args.data / "train.jsonl", tokenizer)
    valid_data = MixedDataset(args.data / "valid.jsonl", tokenizer)
    dataset_validation = {
        "train": validate_dataset(train_data, args.max_seq_length),
        "valid": validate_dataset(valid_data, args.max_seq_length),
    }
    iterator = BalancedMixedIterator(order_seed=args.seed + 1000)
    loss = token_mean_loss if args.condition == "token" else example_mean_loss
    optimizer = optim.AdamW(learning_rate=args.learning_rate, weight_decay=0.0)

    config = {
        "protocol": "lora-selection-robustness-rank-1.0",
        "model": str(args.model),
        "fine_tune_type": "lora",
        "num_layers": args.num_layers,
        "lora_parameters": rank_config,
        "condition": args.condition,
        "seed": args.seed,
        "batch_size": args.batch_size,
        "iters": args.iters,
        "learning_rate": args.learning_rate,
        "max_seq_length": args.max_seq_length,
        "dataset_validation": dataset_validation,
        "data_manifest": json.loads((args.data / "manifest.json").read_text()),
        "fingerprints": {
            "protocol.md": sha256(PROJECT / "PROTOCOL.md"),
            "train_rank_condition.py": sha256(Path(__file__)),
            "historical_train_condition.py": sha256(HISTORICAL / "train_condition.py"),
            "historical_evaluate_condition.py": sha256(HISTORICAL / "evaluate_condition.py"),
            "data_manifest.json": sha256(args.data / "manifest.json"),
            "model.safetensors": sha256(args.model / "model.safetensors"),
            "model_config.json": sha256(args.model / "config.json"),
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "mlx": importlib.metadata.version("mlx"),
            "mlx-lm": importlib.metadata.version("mlx-lm"),
        },
    }
    (args.output / "adapter_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n"
    )
    training_args = TrainingArgs(
        batch_size=args.batch_size,
        iters=args.iters,
        val_batches=-1,
        steps_per_report=24,
        steps_per_eval=96,
        steps_per_save=args.iters,
        adapter_file=args.output / "adapters.safetensors",
        max_seq_length=args.max_seq_length,
        grad_accumulation_steps=1,
        clear_cache_threshold=2_000_000_000,
    )
    train(
        model=model,
        optimizer=optimizer,
        train_dataset=train_data,
        val_dataset=valid_data,
        args=training_args,
        loss=loss,
        iterate_batches=iterator,
    )
    resource = {
        "rank": args.rank,
        "condition": args.condition,
        "seed": args.seed,
        "wall_seconds": time.time() - started,
        "peak_mlx_memory_gb": mx.get_peak_memory() / 1e9,
        "cache_memory_gb": mx.get_cache_memory() / 1e9,
    }
    (args.output / "resource.json").write_text(
        json.dumps(resource, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(resource, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

