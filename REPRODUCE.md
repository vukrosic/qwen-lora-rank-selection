# Reproduction and continuation

## Requirements

- macOS on Apple silicon with enough memory for one local Qwen process;
- Python, MLX 0.31.2, and MLX-LM 0.31.3;
- a local Qwen3-0.6B 3-bit model matching `PROVENANCE.md`;
- the bundled frozen synthetic dataset; and
- imported trainer/evaluator sources matching `PROVENANCE.md`.

Model assets are intentionally not bundled; the frozen dataset and source
snapshots are included. Supply the model path through the source runner's
arguments or adapt its path resolution without changing the scientific
constants. Any code change after observing a partial outcome must be recorded
and treated as non-comparable evidence.

The exact Python package versions used locally are pinned in
`requirements.txt`. Model weights are not a Python dependency and must be
supplied separately with the recorded hash.

## Model-free package validation

Run from this repository root:

```text
PYTHONDONTWRITEBYTECODE=1 python test_verify_package.py
PYTHONDONTWRITEBYTECODE=1 python verify_package.py --stage final
```

The first command tests both a clean package and deliberately corrupted
fixtures. The second validates required files, portability, forbidden bulky
artifacts, terminal outcome consistency, and every manifest fingerprint.
`code/build_manifest.py` prints the exact sorted manifest content and excludes
the manifest itself; create the final file only after every other file is fixed.
`code/render_readme.py` renders the first-screen summary only from a recognized
terminal `RESULT.json` and rejects the nonterminal matched-control-required
branch.

## Scientific execution order

1. verify model, config, data, trainer, evaluator, protocol, runner, and analyzer
   hashes;
2. run the serialized rank-4 block once with frozen seeds 20260841–20260843;
3. set the path variables documented in `code/README.md`, run
   `code/analyze_rank.py`, and inspect raw evidence against `PROTOCOL.md`;
   export the inspected classification with `code/export_classification.py`;
   for a valid substantive block, run `code/audit_margins.py` and inspect its
   exact counts and NLL margins;
4. if rank 4 passes or is invalid, stop without fresh rank 8;
5. only if rank 4 is valid and fails a substantive gate, create the exact
   earned-control record and run matched rank 8 on the same seeds; and
6. run `code/synthesize_result.py`, then compare `RESULTS.md` with the terminal
   machine-readable result and manifest.

Only one model process may run at a time. A locally idle accelerator is not
authorization to use a shared model slot.
