# Validation-guided LoRA selection under rank reduction

**RANK_SPECIFIC_BREAK**

Validation-guided token-vs-example selection failed the frozen gates at LoRA
rank 4 but passed every gate on matched rank 8 using the same three fresh
seeds. This supports a bounded rank-specific break on the tested task.

## What changed

For every seed and rank, token-mean and example-mean adapters were trained to
the same 576-update endpoint. Final validation loss selected one arm before
either test was run. The matched control changed only LoRA rank from 4 to 8;
model, data, seeds, layer budget, scale, optimizer, selector, and evaluator
were fixed.

At rank 4, validation-selected mean exact match was 36.11% and mean NLL was
0.3950, worse than always-example on both measures. At matched rank 8, the
selected policy reached 77.78% mean exact match and 0.1352 mean NLL, beating
both fixed policies on mean and worst-seed metrics. All rank-8 gates passed;
all six substantive rank-4 gates failed.

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
