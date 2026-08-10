# Methods

## Design

This package separates selection from evaluation. For each frozen seed, two
LoRA adapters are trained with identical examples and settings but different
loss aggregation. Final validation loss selects one arm before either arm's
test result is generated. Testing both arms allows comparison with the selected
policy and the two fixed policies.

LoRA rank is the intervention. Rank 4 halves the adapter bottleneck dimension
relative to the inherited rank-8 setting while holding adapted layers, scale,
training duration, optimizer, dataset, and evaluator constant. The historical
rank-8 result is sufficient context if rank 4 passes. It cannot isolate rank as
the cause of a rank-4 failure because it uses different seeds, so that outcome
alone earns a fresh matched rank-8 block.

## Data boundary

The task is synthetic associative recall with balanced short and long targets.
Train, validation, and test differ in prompt templates but reuse the same
arbitrary facts. This design tests optimization and validation-selection
behavior under rank reduction, not semantic generalization to unseen mappings.

## Execution and evidence

The stage runner serializes all model processes. Each launch records command,
timestamps, exit status, output streams, resource use, settings, and hashes.
The analyzer verifies every training report through update 576, the order of
both training completions before selection and selection before both tests,
all 96 raw evaluation records, raw-to-summary metric agreement, and
model/data/code/protocol identity before applying scientific gates.

`code/analyze_rank.py` is the fail-closed block analyzer.
`code/synthesize_result.py` combines rank 4, the immutable historical rank-8
baseline, and a matched rank-8 block only when predeclared conditions earn it.
For a valid rank-4 block, `code/audit_margins.py` independently converts exact
rates to record counts and records every strict exact/NLL comparison margin;
it refuses an invalid classification.

## Software target

The frozen environment uses Python from the experiment host, MLX 0.31.2, and
MLX-LM 0.31.3. Reproduction requires a local Qwen3-0.6B 3-bit model and the
frozen dataset assets identified in `PROVENANCE.md`; neither is redistributed
in this compact repository.
