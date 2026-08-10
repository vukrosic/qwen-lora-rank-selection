# Provenance

## Frozen external assets

The compact package includes the complete frozen synthetic dataset, but not
model or adapter weights. Reproduction must supply external assets whose
SHA-256 values match; bundled data are independently checked against the same
manifest:

| Asset | SHA-256 |
| --- | --- |
| Qwen3-0.6B-3bit `model.safetensors` | `add1354a3e8ddf16fd4308ce9556b2b11c0b6e45863f8898e28e0a0bb8ae18e8` |
| model `config.json` | `7319e769e58a8d819f67a83b3d413624a4a143dccde0d0d326b223ca74f71157` |
| data manifest | `6e4cbdeacfee45ed1b3d201d2168d52256e77f1e762d0ee523ca00b7d07efe71` |
| imported trainer source | `c59c687bad6b1a4b87160d7df3c9f1160adb80edbaa4a7be255810d453a4139d` |
| imported evaluator source | `e4fe991feb32dc4ad7108eff4e88462fa85bcd39e1bfc2f9e918ec3b7a79f647` |

## Frozen local decision artifacts

| Artifact | SHA-256 |
| --- | --- |
| source protocol | `d381bed59456352132e5c108a7556c52657fd6a3defe4da1013f39c26a761f58` |
| prospective trainer | `3bdfdaa12bb17ea34f4292a77304220e2cc73bde4e7a6c5967bfbe79ee2e23dc` |
| stage runner | `d2d13c3dd532932d170599805894a661f9e6bbeca1ca3648aa1046174223c2d3` |
| analyzer | `158b62e9f56fce3ef2eb6a080198387077a4f42ad7b93a92479bf44ab87c67b8` |
| result synthesizer | `6486388fb0263ac3b300b2dceee23a14e64f6648202575a7ecd4d8d15bf2b7dd` |

The package includes path-portable analyzer and synthesizer copies. Their
package hashes are recorded in `code/README.md`; scientific logic and frozen
constants are unchanged, while local path discovery and default package paths
are adapted explicitly.

The installed MLX-LM 0.31.3 rank implementation was inspected model-free and
is pinned in `validation/rank-mechanism-audit.md`: `lora.py` SHA-256
`4d3a8edab111d4ddba33398ba8700203db7b61621c39e9c348fdd50e57278b45`
and conversion `utils.py` SHA-256
`166eaf5e5f923113bed43614a5fb7319795fa0cac5a7fa319ea54e5f0045b553`.
The selector's three-decimal validation logging is pinned by
`trainer.py` SHA-256
`ee33ebdbd20a184108541cb490d08085485e71a82ffd6d68d7d216029ecd28fe`
and documented in `validation/selector-precision.md`.

The historical prospective rank-8 result has SHA-256
`dab32943fbb882f7285e0ced94453af915d5bfbb0d4682a78f01dbf5d37f6a0d`
and uses seeds 20260817–20260819. It is contextual evidence, not a matched
causal control for a failure on the fresh rank-4 seed block.

## Claim-bearing result artifacts

| Artifact | Source SHA-256 | Portable package SHA-256 |
| --- | --- | --- |
| rank-4 classification | `d1eedbba12c3bcdc61a3b64a4bc5866316fc21e57d9de6fddf89b44eeae00c7d` | `cbfb0708b255133b747a14df7e5ebf8750fa531841c81d7d081401cbd4d2ed09` |
| matched rank-8 classification | `09c55c41866f19772ee37ce20e8952d1e7de0a93606c88a9b9df28d038aa698f` | `f476d4eed5a7cc9d71c79f7342b2675a5fcd0d3fce616a2805c70be3ff793129` |
| terminal integrated result | `07ab41bbc7bb84730d65fa3b2b2ad10f9924b7da4223f089413b0413eb2ce1e9` | `a26f40bb7d3d90e29d3946d1d446f1fdbc095e0f3055a96133e68b0c82489006` |

The portability transform replaces only the analyzer's machine-local run-tree
path and records the exact source-classification hash. Scientific fields are
unchanged. The terminal result embeds and fingerprints both portable
classifications plus the immutable historical result.

The final `MANIFEST.sha256` covers every distributable file after the terminal
result, independent-implementation audit, and review were fixed. The manifest
excludes only itself, as verified by the package fixture.

The compact representative-record export is bound to the exact source
classification SHA-256. Its 12 raw-file fingerprints must equal the analyzer's
accepted `evidence_fingerprints`; the final package verifier recomputes that
cross-artifact correspondence. It is mandatory for every substantive rank-4
result. It may be absent only when rank 4 is `INCONCLUSIVE_INVALID` and the
recorded integrity failure makes the fixed export impossible; both
`RESULTS.md` and `REVIEW.md` must then carry an exact
`REPRESENTATIVE_SAMPLE_UNAVAILABLE:` explanation.

## Independent-implementation audit

A second checker that does not import the claim-bearing analyzer recomputed
both rank blocks from raw receipts, logs, selections, teacher-forced records,
generation records, and file hashes. Its source SHA-256 is
`869a1cc3da5ff31806ac93c76221a049da346c142eb8b2010774e65ad6769ac9`;
the full local receipt SHA-256 is
`87965e55483cd822ded2f53eb710122554f6ce7484f8a37f6585548f3294171f`.
The packaged summary is
`validation/independent-implementation-audit.md`. The checker was written and
run by the replacement initiative leader, so this is implementation
independence rather than separate-owner verification.

## Post-hoc descriptive mechanism follow-up

The concise package artifact `POST-HOC-MECHANISM.md` is derived from a frozen,
model-free follow-up. Its local source fingerprints are:

| Artifact | SHA-256 |
| --- | --- |
| frozen analysis plan | `bcfb838ace85368d83268e20f5f67d80a9e0c96f455e2631e53b525271addccf` |
| analysis script | `9167dc2dfcc0c6b68b438a1e8ae12e4ef24a9551b9da324024905dfcecfbead9` |
| full result JSON | `f70469cbb16e3c1723708c103a63c7362a4e1985a72ca0586ba846222d33bade` |
| full rendered report | `daf05c7157bbde2bbc8ed116dd7eaa4e221590e4dc617b9a1c55e1184d4239e2` |

Its analysis fingerprint is
`119362426ae77387b7ae33dc1c9f3f52d70a76092e0d0099ee6a04a1cfbb8163`.
A clean rerun was byte-identical, and the initiative leader independently
recomputed the central selection and raw-test contrasts without importing the
follow-up analyzer. This follow-up is explicitly post-hoc, descriptive, and
non-causal; it does not alter the frozen protocol or terminal outcome.
