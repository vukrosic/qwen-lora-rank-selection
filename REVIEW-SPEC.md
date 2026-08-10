# Frozen result inspection and independent-review specification

Status: **FROZEN BEFORE RANK-4 OUTCOMES**  
Frozen: 2026-08-10 04:04 Asia/Singapore  
Interpretive-margin amendment: 2026-08-10 05:04 Asia/Singapore, before outcomes  
Applies to: rank-4 stage and any conditionally earned matched rank-8 stage

This document fixes what must be inspected after execution. It does not add or
change a scientific gate in `PROTOCOL.md`; the analyzer and synthesizer remain
the decision authority for the frozen rules.

## Evidence snapshot to inspect

For every executed seed and arm, inspect rather than merely check existence:

1. launch receipt, exact command, start/end timestamps, exit status, stdout,
   stderr, resource record, adapter config, and adapter-weight fingerprint;
2. trainer reports through update 576, including finite loss and validation
   values and the frozen settings/hashes;
3. selection record contents and timestamp, confirming both arms completed
   before selection and both tests started only after sealing;
4. all 96 raw test records, including unique IDs, prompts, targets, raw
   generations, normalized predictions, per-record losses, and condition;
5. recomputed summary metrics from raw records, with exact agreement to the
   saved evaluator summary; and
6. analyzer inputs and output fingerprints.

Any missing, malformed, non-finite, hash-mismatched, setting-mismatched,
timestamp-invalid, or summary-inconsistent item is an integrity failure. It
must produce `INCONCLUSIVE_INVALID`, not a scientific pass or failure.

## Decision audit

Recompute and inspect each frozen rank-4 gate separately:

- selected NLL strictly beats the other arm on all three seeds;
- selected exact is within 5 percentage points of the other arm on each seed;
- selected mean and worst-seed NLL beat both fixed policies;
- selected mean and worst-seed exact beat both fixed policies; and
- the anti-floor condition holds on at least two selected arms.

Confirm that no seed, endpoint, arm, metric, threshold, or retry was changed
after any test outcome. Record every failed gate without averaging it away.
For every strict exact or NLL comparison, report the observed margin; express
exact-match margins as both percentage points and test-record counts. Do not
interpret a gate pass as a significance test or confidence interval.

## Conditional-control audit

- A valid rank-4 `TRANSFER_SUPPORTED` result must stop without fresh rank 8.
- An invalid rank-4 block must stop without fresh rank 8.
- Only a valid rank-4 `NONTRANSFER_OR_MIXED` result may earn matched rank 8.
- The earned-control record must match the exact rank-4 classification content
  and SHA-256, frozen protocol identity, seeds, and failed substantive gates.
- If matched rank 8 runs, repeat the complete evidence and decision audit above
  with rank as the only changed setting.

## Independent review request

The separate reviewer receives the frozen protocol, this specification, source
fingerprints, raw run tree, analyzer output, synthesized result, and canonical
package snapshot. The reviewer should answer independently:

1. Is the executed evidence valid under the frozen protocol?
2. Does the analyzer's classification follow from the raw evidence and gates?
3. Was the conditional rank-8 branch handled exactly as predeclared?
4. Does the synthesized claim remain within the same-fact synthetic boundary?
5. Does the canonical package reproduce the evidence and avoid unsupported
   novelty, natural-data, unseen-fact, or general-LoRA claims?

Approval requires exact inspected support, not trust in owner-written prose.
Disagreements preserve both readings and block a stronger terminal claim until
resolved from the recorded evidence.
