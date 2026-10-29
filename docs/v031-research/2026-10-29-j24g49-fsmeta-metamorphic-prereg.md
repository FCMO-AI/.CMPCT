# J24G49 — independently rooted positional fsmeta replay state-machine oracle

Date: 2026-10-29 UTC. **SCIENCE/TEST ONLY; NO MERGE, RELEASE OR SOURCE PATCH.**

## Authority and ownership
Target is existing product correctness owner J24G47 [#773](https://github.com/FCMO-AI/.CMPCT/pull/773) at exact parent SHA `893aac3f6b7b54e89d71af6970405ff5fc71aef7`, Reader blob `84f1c0602c7a9679cd79a0a5de984b169a467903`, transactions blob `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`. J24G48 [#775](https://github.com/FCMO-AI/.CMPCT/pull/775) owns physical cost; we will not modify its instrument or any product path. J24G46 [#770] preserves original physical negative. Shared discovery STATE belongs to #574. Research branch only changes a new independent test, workflow and result notes.

## Strong control / opportunity
J24G47 already passes a deterministic 500-step path-identity state machine and physical three-host xattr restoration. That strongly supports its repaired logic. This independent lower-rung state-machine oracle aims to cover a wider set of initial path/metadata configurations and operation orderings, including mixed `put` / `del` / `ren` batches and each operation applied separately, with a name-keyed ground truth independent of row ordinal rekeying. This is optional evidence reinforcement, not an excuse to defer safety convergence.

## Prospective *hosted* hypothesis
Using the real imported J24G47 `_apply_journal_ops`, 100,000 deterministic random trials with a fixed source seed, 0–9 initial files from a 15-name pool, independent optional owner/xattr metadata, and 1–9 legal operations per trial will preserve exact name-keyed owner/xattr identity. Comparing the whole operation batch to sequential per-op application with **independent deep copies of the original operations** will produce the same full index. Require >=400,000 executed operations and >=10,000 distinct operation-class traces. Distinct malformed-receipt and corrupted-index controls must be rejected by the independent oracle. Parent source is immutable and must match Git blobs on each platform.

## Earlier local exploratory evidence and correction (not preregistered)
A detached *copied-function* local oracle executed 100,000 random trials / 499,536 operations / 16,439 trace classes without finding a metadata counterexample. A first batch-vs-split diagnostic falsely failed on trial 4 because **the instrument replayed operation lists that the function had mutated by reference**. That error was corrected by deep-copying commands before each route, after which the same 100,000 trials yielded no counterexample. This exploratory result is not hosted installed-source proof and cannot earn CI or product credit. The signed operation-input alias observation itself is not claimed as a product defect; per-generation normal Writer ops are one command, and the replay helper has no published pure-function contract.

## Kill / narrow conditions
Any genuine path/metadata mismatch, batch-vs-split discrepancy on legal deep-copied commands, false acceptance of an intentionally corrupted observed index, imported-source identity drift, or underfilled test portfolio invalidates the positive. A valid negative changes the parent #773 correctness decision and must be handed to its owner without silently patching it. If all tests pass, claim only a new bounded deterministic in-memory regression corpus, **not** authenticated archive/full filesystem/CPU/size/portability release parity.

## Economic and concurrency accounting
No Builder/Reader/transactions/native/format/benchmark/release/threshold changes, no private data, no spending. Test-only O(100k small states) runtime and peak RSS must be measured on the host, no claim beyond the tested seed. Adjacent concurrent owners #773/#775 remain authoritative. New checks must be integrated under separate claim, never overwrite shared STATE.
