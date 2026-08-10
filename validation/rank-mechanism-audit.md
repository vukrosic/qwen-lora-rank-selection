# MLX-LM rank/scale mechanism audit

Status: model-free, completed before rank-4 outcomes  
Audited: 2026-08-10 04:20 Asia/Singapore

## Question

Does holding LoRA `scale=20` while reducing rank 8 to rank 4 accidentally
change the explicit update multiplier through an `alpha / rank` convention?
If so, the selected axis would combine capacity and scaling.

## Inspection

Installed MLX-LM version: 0.31.3.

- `mlx_lm/tuner/lora.py` SHA-256:
  `4d3a8edab111d4ddba33398ba8700203db7b61621c39e9c348fdd50e57278b45`.
- `mlx_lm/tuner/utils.py` SHA-256:
  `166eaf5e5f923113bed43614a5fb7319795fa0cac5a7fa319ea54e5f0045b553`.

`LoRALinear.__call__` computes the low-rank branch as `(x @ A) @ B` and adds
`self.scale * z` to the frozen linear output. `LoRALinear.fuse` likewise uses
`self.scale * B^T @ A^T`. Neither path divides scale by rank. The conversion
helper passes the configured `rank`, `scale`, and `dropout` directly.

The existing model-free shape check also confirms `(16,4)/(4,12)` versus
`(16,8)/(8,12)`, 112 versus 224 low-rank parameters, and identical base output
at zero-B initialization.

## Consequence

The rank-4 intervention does not alter an explicit `scale/r` coefficient:
`scale=20` is the same multiplier at both ranks. Reducing rank changes the
low-rank parameterization and available update subspace (including intrinsic
optimization effects of that parameterization), which is the intended axis.
This audit does not predict the outcome and does not change any frozen gate.

Preflight now pins both implementation source files in addition to package
versions, so local source drift before launch fails closed.
## Real adapter budget check

Metadata-only inspection of all six established prospective rank-8 adapters
(seeds 20260817–20260819, token and example) found the same structure in every
file: 112 LoRA A/B tensors across 56 adapted linear modules, 1,441,792 trainable
values, and rank dimension 8 in every low-rank tensor. With the same module
shapes, rank 4 therefore contains 720,896 trainable adapter values exactly half
the rank-8 budget. This reads safetensor shapes only; it does not load Qwen or
predict the rank-4 result.
