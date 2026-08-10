# LoRA selection robustness under rank reduction

## Decision

**RANK_SPECIFIC_BREAK**

Validation-guided selection failed the frozen gates at rank 4 but passed every
gate on the matched fresh rank-8 block. Within this one same-fact synthetic
Qwen/MLX experiment, reduced LoRA rank changed the scientific conclusion.

This is a bounded mechanism result, not a claim that rank 4 generally fails or
that validation-guided selection generally succeeds at rank 8.

## Prospective rank-4 test

| Seed | Selected before test | Selected exact | Other exact | Selected NLL | Other NLL |
| ---: | --- | ---: | ---: | ---: | ---: |
| 20260841 | example | 72/96 (75.00%) | 49/96 (51.04%) | 0.1239 | 0.3503 |
| 20260842 | example | 23/96 (23.96%) | 8/96 (8.33%) | 0.4840 | 0.7561 |
| 20260843 | token | 9/96 (9.38%) | 20/96 (20.83%) | 0.5772 | 0.4951 |

| Policy | Mean exact | Worst exact | Mean NLL | Worst NLL |
| --- | ---: | ---: | ---: | ---: |
| Validation-selected | 104/288 (36.11%) | 9/96 (9.38%) | 0.3950 | 0.5772 |
| Always token | 66/288 (22.92%) | 8/96 (8.33%) | 0.5612 | 0.7561 |
| Always example | 115/288 (39.93%) | 20/96 (20.83%) | 0.3677 | 0.4951 |

Rank 4 was valid (`errors: []`) and had anti-floor headroom, but all six
substantive transfer gates failed. The decisive reversal was seed 20260843:
validation selected token, which lost to example by 11 exact records and
0.0820269357 NLL. Consequently the selected policy also lost to always-example
by 11/288 mean exact records, 11/96 worst-seed exact records, 0.0273423119 mean
NLL, and 0.0820269357 worst-seed NLL. These are descriptive frozen-gate
margins, not significance tests.

## Matched rank-8 control

Only LoRA rank changed. Model, quantization, data, seeds, arm order, eight
adapted layers, fixed scale, optimizer, 576-update endpoint, selection rule,
evaluator, and test boundary remained fixed.

| Seed | Selected before test | Selected exact | Other exact | Selected NLL | Other NLL |
| ---: | --- | ---: | ---: | ---: | ---: |
| 20260841 | token | 95/96 (98.96%) | 37/96 (38.54%) | 0.0087 | 0.3762 |
| 20260842 | token | 74/96 (77.08%) | 67/96 (69.79%) | 0.1681 | 0.1923 |
| 20260843 | example | 55/96 (57.29%) | 10/96 (10.42%) | 0.2288 | 0.6693 |

| Policy | Mean exact | Worst exact | Mean NLL | Worst NLL |
| --- | ---: | ---: | ---: | ---: |
| Validation-selected | 224/288 (77.78%) | 55/96 (57.29%) | 0.1352 | 0.2288 |
| Always token | 179/288 (62.15%) | 10/96 (10.42%) | 0.2820 | 0.6693 |
| Always example | 159/288 (55.21%) | 37/96 (38.54%) | 0.2657 | 0.3762 |

Matched rank 8 was valid (`errors: []`) and passed every frozen gate. The
narrowest seed-level selected-arm margin was still seven exact records and
0.0241954118 NLL on seed 20260842. Against the fixed policies, selection gained
45/288 mean exact records over always-token and 65/288 over always-example;
mean NLL advantages were 0.1468548848 and 0.1305594109, respectively. The full
descriptive recomputation is in
`validation/matched-rank8-margin-audit.md`.

## Integrity and interpretation

- All 24 training/evaluation receipts across rank 4 and matched rank 8 report
  `COMPLETED` with exit code 0.
- Each seed's two trainings ended before its selection file was sealed, and
  that seal predates both test evaluations.
- Every arm has 96 unique generation rows and 96 unique teacher-forced rows;
  the frozen analyzer recomputed summaries and verified protocol, model, data,
  trainer, evaluator, runner, receipt, adapter, log, and metric fingerprints.
- Maximum observed training peak was 0.8167 GB at rank 4 and 0.8311 GB at
  matched rank 8. One Qwen process ran at a time.
- The first rank-4 analyzer invocation failed closed on relative-versus-absolute
  path strings. The unchanged analyzer was re-invoked with the absolute run
  directory; only that path representation changed, yielding `errors: []`.

The contrast supports a rank-specific break under the frozen design: the same
validation rule and seed block did not satisfy the claim at rank 4 but did at
rank 8. It does not identify a universal rank threshold or prove that capacity
alone caused every per-seed difference.

## Post-hoc descriptive mechanism diagnosis

A model-free follow-up found that the selected condition and endpoint
validation-loss ordering reversed between rank 4 and rank 8 on all three
matched seeds, while fixed-test NLL and exact-match ordering reversed on two of
three. Mean absolute selector margin was 0.099 at rank 4 and 0.253 at rank 8.
This is a descriptive, non-causal account of how the recorded break appeared;
it neither changes `RANK_SPECIFIC_BREAK` nor identifies a universal rank
threshold. See [POST-HOC-MECHANISM.md](POST-HOC-MECHANISM.md).

## Scope

Qwen3-0.6B 3-bit under MLX-LM 0.31.3, one synthetic associative-recall task,
three fixed seeds, and held-out prompt templates over facts reused from
training. There is no natural-data, unseen-fact, other-model, other-library,
other-rank, production, novelty, or general-LoRA claim.

`evidence/RESULT.json` is the authoritative machine-readable integration.
Adapters and model weights remain local and are excluded from this package.
