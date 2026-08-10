# Independent-implementation raw evidence audit

Status: **PASS**  
Audit time: 2026-08-10 Asia/Singapore

A second implementation, written without importing the claim-bearing
`analyze_rank.py`, independently checked both rank blocks from the raw local
run tree. It verified:

- all 24 training/evaluation receipts, exact commands, exit codes, frozen
  ranks, seeds, conditions, update count, batch size, layer count, learning
  rate, sequence length, and generation limit;
- train completion before selection sealing and sealing before both tests for
  every seed;
- 96 unique teacher-forced rows and 96 unique generation rows per arm;
- row-level NLL arithmetic, generation normalization, exact-match flags,
  balanced per-kind summaries, selected arms, policy aggregates, and every
  frozen gate;
- all 126 analyzer-accepted raw evidence fingerprints across rank 4 and
  matched rank 8; and
- the deterministic terminal mapping from valid rank-4
  `NONTRANSFER_OR_MIXED` plus valid matched-rank-8 `TRANSFER_SUPPORTED` to
  `RANK_SPECIFIC_BREAK`.

The independent implementation returned `errors: []`. Its source SHA-256 is
`869a1cc3da5ff31806ac93c76221a049da346c142eb8b2010774e65ad6769ac9`;
its full local audit receipt SHA-256 is
`87965e55483cd822ded2f53eb710122554f6ce7484f8a37f6585548f3294171f`.

This is implementation independence, not owner independence: the replacement
initiative leader wrote and ran the second checker. It strengthens protection
against a shared analyzer-code error but is not a separate-team replication or
publication review.

