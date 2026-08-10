# Continuation guidance

This repository is a bounded evidence package for one rank-robustness test,
not a general LoRA tuning framework. Read `README.md`, `PACKAGE-STATE.md`, the
frozen protocol, and the final result before interpreting or changing code.

## Preserve the scientific boundary

The test changes only LoRA rank 8 to rank 4 under Qwen3-0.6B 3-bit, MLX-LM,
eight adapted layers, one same-fact synthetic associative-recall dataset, 576
updates, and three frozen seeds. Validation and test hold out prompt templates,
not facts. Never rewrite a positive result as unseen-fact, natural-data,
cross-model, cross-library, or general LoRA robustness.

Historical rank-8 evidence is a contextual prospective baseline when rank 4
passes. It is not a matched causal control for rank-4 failure. Only a valid
rank-4 substantive failure earns fresh rank-8 controls on the same seeds; an
invalid rank-4 block earns no additional model spend.

## Safe continuation

Keep all future work local, zero-cost, non-destructive, and in a separately
owned project folder with a protocol frozen before outcomes. Do not change the
recorded seeds, thresholds, metrics, or gate conjunction after seeing results.
Preserve raw evidence and failures. A same-owner rerun is reproducibility, not
independent verification.

Do not create a worktree, nested `.git`, remote, release, publication, account
change, external message, cloud run, or paid computation without explicit
human authority. Never add model weights, adapter weights, caches, secrets,
private data, or machine-specific absolute paths to this package.
