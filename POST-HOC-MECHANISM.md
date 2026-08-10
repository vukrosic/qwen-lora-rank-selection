# Post-hoc descriptive diagnosis of the rank break

This follow-up describes patterns in the completed rank-4 and matched rank-8
runs. It is **post-hoc, descriptive, and non-causal**. It does not change the
preregistered terminal classification: **`RANK_SPECIFIC_BREAK`**.

## What the recorded runs show

- The validation-selected condition reversed between rank 4 and rank 8 on all
  three matched seeds: `example -> token`, `example -> token`, and
  `token -> example`.
- The endpoint validation-loss ordering also reversed on all three seeds.
- The fixed-test ordering reversed on two of three seeds for both balanced NLL
  and exact match. At rank 4, the selected arm beat the other arm on two of
  three seeds; at rank 8, it beat the other arm on all three.
- Mean absolute selector margin was 0.099 at rank 4 and 0.253 at rank 8.
- Recorded adapter metadata approximately doubled from 0.721M trainable
  parameters and 2,895,443 bytes at rank 4 to 1.442M and 5,779,075 bytes at
  rank 8.

These observations are consistent with rank-associated differences in the
optimization endpoints and validation/test alignment within this seed block.
They do not identify why those differences occurred. Capacity is a plausible
bounded contributor from metadata alone, but no adapter tensors were decoded
and no causal intervention beyond the frozen rank comparison was performed.

## Validation and boundaries

The analysis used the existing 12 train/evaluation arms and six sealed
selections only. A deterministic rerun produced byte-identical outputs. A
separate raw-record recomputation, without importing the follow-up analyzer,
confirmed all selections, margins, raw NLL/exact summaries, three validation
order reversals, and two test-order reversals.

The result is limited to Qwen3-0.6B 3-bit under MLX-LM, one same-fact
synthetic task, ranks 4 and 8, three matched seeds, and update 576. It does not
support a universal rank threshold, a general LoRA mechanism, population-level
stability, or transfer to other models, tasks, data, ranks, or libraries. A
seed-block explanation cannot be ruled out.

## Source fingerprints

- Frozen plan: `bcfb838ace85368d83268e20f5f67d80a9e0c96f455e2631e53b525271addccf`
- Analyzer: `9167dc2dfcc0c6b68b438a1e8ae12e4ef24a9551b9da324024905dfcecfbead9`
- Full machine-readable result: `f70469cbb16e3c1723708c103a63c7362a4e1985a72ca0586ba846222d33bade`
- Full rendered report: `daf05c7157bbde2bbc8ed116dd7eaa4e221590e4dc617b9a1c55e1184d4239e2`
- Analysis fingerprint: `119362426ae77387b7ae33dc1c9f3f52d70a76092e0d0099ee6a04a1cfbb8163`

The full local follow-up remains outside this compact package; these hashes
bind this concise account to its frozen plan, code, and detailed outputs.
