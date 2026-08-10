# Verification review

Review date: 2026-08-10 Asia/Singapore  
Terminal outcome reviewed: `RANK_SPECIFIC_BREAK`

## Verification level

The protocol and conditional-control logic received a separate-owner,
model-free Luna review before execution. That review passed the then-current
integrity gate and specifically endorsed the rule that a valid rank-4
substantive failure earns fresh rank-8 controls on the same seeds, while
historical rank-8 evidence is not a causal control for failure.

After that review, the initiative leader further hardened the analyzer to pin
additional source hashes, raw evidence, exact commands/settings, and
train-selection-test chronology. All such changes were made before outcomes
and exercised by corruption fixtures. The claim-bearing analyzer hash is
`158b62e9f56fce3ef2eb6a080198387077a4f42ad7b93a92479bf44ab87c67b8`.

The final outcome snapshot below received a complete same-owner evidence
inspection plus a from-scratch second implementation that independently
recomputed raw metrics, selections, aggregates, gates, chronology, commands,
and all 126 evidence fingerprints without importing the claim-bearing
analyzer. That audit passed with `errors: []`; see
`validation/independent-implementation-audit.md`. A separate owner did not
inspect the post-outcome package. This artifact is therefore locally
reproducible and GitHub-ready, but the result is not labeled separate-owner
outcome-verified or publication-ready.

## Frozen review questions

### 1. Is the executed evidence valid under the frozen protocol?

**PASS.** Both rank blocks have `errors: []` and `all_valid: true`. All 24
training/evaluation receipts are `COMPLETED` with exit code 0. Every arm has
96 unique generation records and 96 unique teacher-forced records. The
analyzer verified finite update-576 reports, settings, commands, interpreter,
MLX versions, model/data/code hashes, adapters, logs, metrics, raw-to-summary
agreement, and selection fingerprints.

Chronology passes on every seed: both trainings ended before the selection
file was sealed, and the seal predates both tests. No retry, seed, endpoint,
threshold, metric, or arm changed after outcomes. Maximum training peak was
0.8167 GB at rank 4 and 0.8311 GB at rank 8, with one Qwen process at a time.

The first rank-4 analyzer invocation failed closed because a relative run-tree
argument was compared with absolute paths recorded by the launcher. The
analyzer and evidence were unchanged; supplying the absolute run directory
resolved only that representation mismatch. The canonical source result hash
is recorded in `PROVENANCE.md`.

### 2. Does each classification follow from the frozen gates?

**PASS.** Rank 4 is `NONTRANSFER_OR_MIXED`: anti-floor headroom passes, but all
six substantive gates fail. On seed 20260843, the selected token arm loses by
11/96 exact records and 0.0820269357 NLL. At the policy level, selection loses
to always-example on mean and worst exact and NLL.

Matched rank 8 is `TRANSFER_SUPPORTED`: every gate passes. Selected arms beat
their paired arms by 58, 7, and 45 exact records and by 0.3674828210,
0.0241954118, and 0.4405646545 NLL. The selected policy also strictly beats
both fixed policies on mean and worst exact and NLL. Exact aggregate margins
are reproduced in `validation/matched-rank8-margin-audit.md`; rank-4 margins
are machine-readable in `evidence/margins.json`.

These are descriptive decision-rule margins, not significance tests.

### 3. Was the conditional rank-8 branch handled as predeclared?

**PASS.** The valid rank-4 failure was first preserved and hashed. The earned
record content identifies that exact classification, frozen protocol, seeds,
failed gates, rank 8, and rank as the only changed factor. A new explicit slot
grant preceded the matched run. Rank 8 used the same fresh seeds and frozen
settings, with LoRA rank as the only intervention.

### 4. Is the synthesized claim within the data boundary?

**PASS.** `RANK_SPECIFIC_BREAK` means only that the selector failed at rank 4
and passed at matched rank 8 on this synthetic same-fact prompt-template
holdout. It does not claim unseen-fact generalization, natural-data transfer,
a universal rank threshold, or general LoRA robustness.

### 5. Is the canonical package internally reproducible and bounded?

**PASS for local package integrity.** The package includes frozen data,
protocol, methods, source snapshots, portable analyzer/synthesizer, both
classifications, terminal integration, exact margins, 24 representative raw
records bound to analyzer-accepted hashes, tests, provenance, and limitations.
It excludes model/adapters, transient logs, caches, secrets, private data, and
machine-local paths. After this review was fixed, the final manifest was
regenerated and the package verifier passed with `errors: []` both in place
and in an isolated copy.

## Verdict

**ACCEPT as a bounded, same-owner-inspected and independently recomputed local
result and canonical GitHub-ready artifact.** The evidence supports
`RANK_SPECIFIC_BREAK` under the frozen design. “Independently recomputed” here
means a second implementation, not a second owner. Separate-owner post-outcome
verification remains desirable and would increase verification status, but
its absence is disclosed and does not change the deterministic classification.
