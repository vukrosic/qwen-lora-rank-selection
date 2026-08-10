<p align="center">
  <img src="assets/starberry-lora-rank.jpg" alt="Starberry comparing LoRA rank 4 and rank 8" width="100%">
</p>

<h1 align="center">LoRA rank changed which training strategy worked</h1>

<p align="center">
  <img alt="Model: Qwen3-0.6B" src="https://img.shields.io/badge/model-Qwen3--0.6B-2563eb">
  <img alt="Framework: MLX-LM" src="https://img.shields.io/badge/framework-MLX--LM-7c3aed">
  <img alt="Result: rank-sensitive" src="https://img.shields.io/badge/result-rank--sensitive-f97316">
</p>

We tested the same training decision at LoRA rank 4 and rank 8.

## Result

| LoRA rank | What happened |
| --- | --- |
| **4** | Validation chose a strategy that lost to always using example-mean training. |
| **8** | The same chooser beat both fixed strategies on the tested seeds. |

> **Practical takeaway:** recheck important training choices when you change
> LoRA rank. A rule that works at one adapter size may fail at another.

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

<details>
<summary>Machine-readable result label</summary>

`RANK_SPECIFIC_BREAK` means that changing LoRA rank reversed the tested
selector's result in this experiment. It is not a claim of general robustness.

</details>

This is an AI-produced research artifact, not a peer-reviewed publication.
