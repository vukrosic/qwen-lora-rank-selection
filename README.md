# LoRA rank changed which training strategy worked

We tested the same Qwen3-0.6B training decision at LoRA rank 4 and rank 8.

At rank 4, choosing between token-mean and example-mean training from
validation loss was worse than simply always using example-mean training. At
rank 8, the same chooser beat both fixed choices on the tested seeds.

**Practical takeaway:** a LoRA training rule that works at one rank may fail at
another rank. Recheck important choices when you change adapter capacity.

## What we tested

For every seed and rank, token-mean and example-mean adapters were trained to
the same 576-update endpoint. Final validation loss selected one arm before
either test was run. The matched control changed only LoRA rank from 4 to 8;
model, data, seeds, layer budget, scale, optimizer, selector, and evaluator
were fixed.

At rank 4, the chooser reached 36.11% mean exact match and 0.3950 mean NLL,
worse than always-example on both measures. At rank 8, it reached 77.78% mean
exact match and 0.1352 mean NLL, beating both fixed choices on mean and
worst-seed results.

The machine-readable evidence calls this outcome `RANK_SPECIFIC_BREAK`; that
label means only that changing rank reversed the result in this experiment.

## Why this is bounded

The experiment uses Qwen3-0.6B 3-bit, MLX-LM 0.31.3, one synthetic
associative-recall dataset, and held-out prompt templates over facts reused
from training. It does not establish natural-data, unseen-fact, cross-model,
cross-library, other-rank, production, or general LoRA robustness.

## Inspect and reproduce

- [Detailed result](RESULTS.md)
- [Post-hoc descriptive mechanism diagnosis](POST-HOC-MECHANISM.md)
- [Frozen protocol](PROTOCOL.md)
- [Methods](METHODS.md)
- [Evidence provenance](PROVENANCE.md)
- [Limitations](LIMITATIONS.md)
- [Reproduction](REPRODUCE.md)
- [Verification review](REVIEW.md)

This is an AI-produced research artifact, not a peer-reviewed publication.
