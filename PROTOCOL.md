# Prospective rank-robustness protocol

Status: frozen before any initiative model execution.  
Source protocol SHA-256:
`d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58`.

## Question

Does choosing between token-mean and example-mean LoRA training by lower final
validation loss retain its bounded advantage when LoRA rank is reduced from 8
to 4?

This is a three-seed prospective test on Qwen3-0.6B 3-bit and one synthetic
associative-recall dataset. Validation and test prompts are held out, but facts
are reused. It is not a test of unseen-fact or natural-data generalization.

## Fresh rank-4 block

Seeds are fixed to 20260841, 20260842, and 20260843. Within each seed, both
arms use the same seed, data order, model, optimizer, and settings. Arm order is
token/example, example/token, token/example respectively.

Each arm uses LoRA rank 4, scale 20, dropout 0, the final 8 eligible linear
layers, batch size 4, balanced 2-short/2-long batches, AdamW at 1e-4 with zero
weight decay, 576 optimizer updates, maximum sequence length 128, and the final
adapter. The sole within-pair difference is supervised-loss aggregation:

- token mean divides summed corrected completion-token loss by supervised-token
  count in the minibatch;
- example mean averages each example's corrected completion-token mean.

After both arms train, the arm with lower validation loss at update 576 is
sealed as selected; an exact tie selects token mean. Neither test is evaluated
before selection is sealed. Both arms are then tested on all 96 fixed records
using greedy decoding, at most 24 generated tokens, and unchanged exact-match
and teacher-forced metrics.

Operationally, MLX-LM 0.31.3 logs endpoint validation loss to three decimals;
the frozen runner compares those logged values. A tie at that precision selects
token. No full-precision reconstruction is permitted after outcomes.

## Frozen metrics and gates

Primary metrics are balanced example NLL and balanced strict exact match.
Diagnostics include per-skill metrics, worst-skill exact, short-minus-long
exact gap, target-token accuracy, validation margin, wall time, adapter size,
trainable parameters, and peak model memory.

Rank-4 transfer is supported only when all conditions hold:

1. selected NLL is strictly lower than the other arm on every seed;
2. selected exact is no more than 5 percentage points below the other arm on
   every seed;
3. selected mean and worst-seed NLL are strictly lower than always-token and
   always-example;
4. selected mean and worst-seed exact are strictly higher than both fixed
   policies; and
5. on at least two seeds, selected exact is strictly between 10% and 90%, with
   both short and long exact above 5%.

Every process must exit successfully, all reports and metrics must be finite,
all frozen hashes/settings must match, and all 96 test records must be
auditable. Integrity failure is `INCONCLUSIVE_INVALID`; a valid failed
substantive gate is `RANK4_NONTRANSFER_OR_MIXED`.

Machine-readable clarification: `analyze_rank.py` emits
`NONTRANSFER_OR_MIXED` for the latter state. That string is the analyzer's
encoding of the protocol label `RANK4_NONTRANSFER_OR_MIXED`; it does not alter
the gates or earn any different branch.

## Conditional matched rank-8 block

Fresh rank 8 is forbidden if rank 4 passes or is invalid. If and only if rank 4
is valid but fails a substantive gate, repeat the same fresh seeds, order,
data, endpoint, selector, metrics, and gates while changing only rank 4 to 8.

- rank 4 fails and matched rank 8 passes: `RANK_SPECIFIC_BREAK`;
- both valid blocks fail: `MIXED_OR_SEED_BLOCK_INCONCLUSIVE`;
- matched rank 8 is invalid: `INCONCLUSIVE_INVALID_MATCHED_RANK8`.

No test output may change the rank, seed block, arm, endpoint, layer count,
threshold, metric, or stopping rule. No extra or replacement seed is allowed.
