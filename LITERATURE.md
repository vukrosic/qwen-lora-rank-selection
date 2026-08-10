# Literature basis for the rank axis

This package does not claim a new literature review. Two pre-existing primary
sources motivate rank as a scientifically meaningful capacity intervention:

- Hu et al., [LoRA: Low-Rank Adaptation of Large Language
  Models](https://arxiv.org/abs/2106.09685), parameterize the trainable weight
  update through a rank-limited factorization and examine rank choices.
- Zhang et al., [AdaLoRA: Adaptive Budget Allocation for Parameter-Efficient
  Fine-Tuning](https://arxiv.org/abs/2303.10512), treat rank budget and its
  allocation across updates as consequential adaptation capacity.

These papers justify testing rank; they do not predict whether validation-loss
selection between token-mean and example-mean training will transfer at rank 4,
and they do not support a natural-data or general-LoRA claim. The experiment's
answer comes only from the frozen local protocol and evidence.
