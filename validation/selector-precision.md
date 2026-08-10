# Selector precision clarification

Status: fixed before rank-4 outcomes  
Recorded: 2026-08-10 04:35 Asia/Singapore

The frozen runner extracts `Iter 576: Val loss ...` from MLX-LM stdout.
Installed MLX-LM 0.31.3 formats that value with `val_loss:.3f` in
`mlx_lm/tuner/trainer.py`, whose SHA-256 is
`ee33ebdbd20a184108541cb490d08085485e71a82ffd6d68d7d216029ecd28fe`.

Therefore the operational selector compares the final validation losses at
their logged three-decimal precision. A tie at that logged precision selects
token mean. No hidden full-precision value will be reconstructed or substituted
after test outcomes. The inherited prospective rank-8 selection used the same
logged precision, and all its endpoint margins exceeded 0.17.

This clarification does not alter the runner, historical comparison, frozen
seeds, gates, or endpoint. It narrows “exact numerical tie” in the source
protocol to the value actually available to the predeclared selector. A
rank-4 tie after rounding will remain auditable as such and is a limitation on
selection resolution, not permission to change the tie rule.
