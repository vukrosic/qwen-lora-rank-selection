# Limitations

- One small quantized model, one library stack, one synthetic task, one adapter
  layer budget, one endpoint, two tested ranks, and one three-seed block shared
  by the prospective rank-4 test and matched rank-8 control.
- Validation and test prompts are held out, but their arbitrary fact mappings
  occur in training. This is same-fact recall, not unseen-fact generalization.
- The observed rank-4 failure plus matched rank-8 pass supports the frozen
  rank-specific contrast. It does not locate a universal rank threshold,
  isolate which learned representations changed, or imply that every rank-4
  seed block would fail.
- Strict exact match is sensitive to formatting. Teacher-forced NLL and target
  token accuracy provide complementary diagnostics but do not erase this
  limitation.
- Exact match is discrete on 96 records per seed and arm. One record changes a
  seed-level balanced exact score by about 1.04 percentage points, and a strict
  aggregate win may be only one record. The frozen gates are descriptive
  decision rules, not significance tests or confidence intervals.
- NLL gates use strict inequality without a preregistered minimum practical
  effect size, so a technical pass must still report the observed margins.
- A non-floor gate is required because comparisons at universal 0% or 100%
  exact-match saturation would not demonstrate useful selection.
- The package does not claim natural-instruction-data transfer, general LoRA
  robustness, novelty, production utility, or publication-level verification.
- The exact outcomes received a same-owner final evidence audit and a
  from-scratch second implementation independently recomputed all raw metrics,
  gates, chronology, commands, and evidence fingerprints. A separate Luna
  reviewer audited the protocol and conditional-control logic before the model
  runs, but no separate owner inspected the final outcome snapshot in this
  task runtime; `REVIEW.md` keeps implementation independence, owner
  independence, and publication review distinct.
