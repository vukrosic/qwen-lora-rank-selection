# Analysis code

`analyze_rank.py` is the frozen fail-closed analyzer with only path discovery
made portable. The claim-bearing run is analyzed first by the source file with
SHA-256 `158b62e9f56fce3ef2eb6a080198387077a4f42ad7b93a92479bf44ab87c67b8`.
This packaged copy has SHA-256
`8bd29a0846587018323234bb89560c3851016c6ebb0dd7a5008f232603e2cb0a`.

For a fresh reproduction, set these environment variables before invoking the
analyzer:

- `RANK_ROBUSTNESS_SOURCE_PROJECT`: folder containing the frozen protocol,
  trainer, runner, and run tree;
- `RANK_ROBUSTNESS_REPO_ROOT`: repository root containing imported assets;
- `RANK_ROBUSTNESS_HISTORICAL`: imported trainer/evaluator/capture folder;
- `RANK_ROBUSTNESS_MODEL`: local model folder;
- `RANK_ROBUSTNESS_DATA`: frozen data folder;
- `RANK_ROBUSTNESS_RUNS`: run tree to inspect; and
- `RANK_ROBUSTNESS_PYTHON`: interpreter recorded in receipts.

The analyzer still enforces the original source and asset hashes, commands,
settings, ordering, raw records, summary recomputation, and scientific gates.

`train_rank_condition.py` and the three files under `imported/` are byte-exact
copies of the frozen claim-bearing trainer plus its inherited loss/data,
evaluator, and process-capture sources. Their hashes are listed in
`PROVENANCE.md` and enforced by the package verifier. They preserve their
original Open Discovery path resolution, so a standalone adaptation must
record new hashes and is a reproduction attempt rather than the original run.

`run_rank_stage.py` is the frozen serialized runner with the same path-only
portability adaptation as the analyzer. It intentionally retains the original
protocol-hash refusal, rank-8 earned-record validation, seed/order plan, and
no-overwrite behavior. Set the documented path variables to a source project
containing the byte-exact frozen protocol and trainer; package-local defaults
fail closed because this repository's protocol is a portable transcription.
Its package SHA-256 is
`a3e756f17399530aed6ecaf32cb57c6a9c04aa6f4ca7882acc3a3ed6ffbe10a5`;
the claim-bearing source SHA-256 is
`d2d13c3dd532932d170599805894a661f9e6bbeca1ca3648aa1046174223c2d3`.

`synthesize_result.py` is a portable copy of the pre-outcome synthesizer. Its
only changes are package-relative default input/output paths. Its packaged
SHA-256 is
`7615f111dccce12ce228daba1c92ea98953d52eabf739787ea2add66476d1042`;
the claim-bearing source SHA-256 is
`6486388fb0263ac3b300b2dceee23a14e64f6648202575a7ecd4d8d15bf2b7dd`.

`export_classification.py` removes only the source analyzer's machine-local
`provenance.runs` value, changes it to the package-relative `runs`, and adds the
exact source-classification SHA-256. It rejects any other absolute path. This
portable classification is the synthesizer input included under `evidence/`;
the source hash keeps it traceable to the inspected claim-bearing output.

`export_evidence.py` applies a pre-outcome sampling rule to analyzer-validated
raw files: the first two lexical IDs for each seed, arm, and short/long kind.
The resulting 24 records expose prompts, targets, generations, exact-match,
NLL, token accuracy, and all 12 source-file hashes without bundling adapters or
the full transient run tree. Export additionally requires the exact source
classification, verifies every sampled raw-file hash against its
analyzer-accepted evidence fingerprints, and records the source
classification SHA-256.

`audit_margins.py` accepts only a clean substantive rank-4 classification. It
converts exact rates back to their exact 96-record, 48-record, and 288-record
count grids; reports selected-versus-other and selected-versus-fixed-policy
NLL margins; fingerprints the classification; and labels the output as
descriptive rather than inferential. Off-grid scores and invalid rank-4 blocks
are rejected by model-free fixtures.
