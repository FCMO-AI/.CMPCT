# O19 — Post-write stage integrity versus a late publication mutation

Date: 2026-10-24 UTC. **PREDICTION REGISTERED BEFORE O19 PRODUCT-TIED RESULTS.** Research only. Source parent O18 PR #363 at `5cdbd00af01a3caa35c18357ac2e859b6cc05f02`; native Rust/C ABI inherited from PR #359, untouched. No released product, format, version, promotion policy, evaluator, or benchmark semantics may change.

## Baseline and decision
O18 hashes the **bytes sent to write()**, fsyncs the predictable named stage inode, then links it under the final name. Its limitations already acknowledge absent on-disk post-write verification and destination concurrency protection. What remains unmeasured is the relative effectiveness of the smallest stronger control: a post-fsync read-back digest versus a mutation at the very publication boundary. An unconditional claim that a read-back hash makes the staged file secure would be false if a distinct process can modify the inode afterward.

**Primary question:** Can a second digest of the actual staged file catch a deterministic one-byte corruption occurring inside a successful write call, without losing the O18 negative publication gate? Does the same addition also protect against a mutation inserted at linkat, or must the threat boundary change?

## Competing controls
1. O18 unchanged: hash of submitted bytes, fsync, linkat.
2. O19 minimal read-back client: same O18 source and public API, plus O_RDWR stage and a streaming post-fsync digest over exactly the stage inode bytes; no archive-sized buffer.
3. Fault-free runs: both must produce exact SHA-matching CDC outputs.
4. Two **separate** deterministic shared-library fault hooks with successful syscall return: `write` hook corrupts the stage byte immediately after a successful write; `linkat` hook corrupts immediately before creation of final name. No external races or nondeterministic sleeps.
5. Independent Python oracle: compare final physical output bytes to original SHA, not to consumer's stdout alone; assert corruption is exactly one flipped first byte. Verify stage cleanup and final exposure.

## Prospective prediction
- Baseline O18 + fault-free: exact published file.
- O19 read-back + fault-free: exact published file.
- Baseline O18 + write-corruption: **exit 0 but corrupted final content** (the original digest measured only caller bytes).
- O19 read-back + write-corruption: **exit 5 with zero final/stage entries**.
- Both clients + linkat-corruption: **exit 0 but corrupted final content**. A rehash just before linking is not a time-of-check/time-of-use defense against a mutator acting after its check.
- SHA absent for RAW remains unsupported; O18's original existing negative suite is inherited, not silently claimed for the new O19 client without retest.

**Disproof:** wrong fault origin; injector does not fire; altered bytes differ from the registered one-byte mutation; O19 publishes write-mutated output; a supposed baseline weakness disappears; or linkat mutation is caught for an unexplained reason. Preserve unexpected results and diagnose; never weaken checks.

## Accounting and claim limit
Record archived physical CMPCT bytes, original and reconstructed SHA, output visibility, exit code, stage cleanup, exact native source blob identities, submitted chunk size (64 KiB), fault identity, and elapsed observations (single-run diagnostics only). Postwrite readback adds a complete staged-file read, 1x logical bytes of **additional I/O**, an additional SHA pass and extra wall/CPU; quantify on full-product before any integration. No claim of whole-process memory or performance improvement. The fault injector itself simulates a capable same-UID or fault-capable mutator, not a naturally occurring filesystem condition; resulting product relevance is conditional on the threat model.

**Decision boundary:** a successful O19 write-corruption rejection permits the narrow claim “post-fsync stage readback protects against corruption before the readback.” If linkat injection succeeds against O19, do NOT productize readback as a complete adversarial-concurrency solution; evaluate unlinked/private stage ownership or an explicit no-concurrent-mutator assumption instead. Neither indexed SHA nor self-resealed r24 index is an external provenance signature.

## Concurrency and authority
Open PR #363 owns O18. O19 is an independent downstream falsification on a distinct test-only implementation/client + isolated workflow, not an in-place rewrite of O18, and does not touch #351/#359 source ABI or #240 discovery state. Before any late write, recheck exact base and open PRs; do not duplicate any active same-narrow owner. No merge, release, discovery-policy edit or format change is authorized.

## Expected evidence
Dedicated Ubuntu GitHub Actions run on exact PR-head; O18 source custody must be byte-identical to its owner, Rust/header identity pinned, strict `-Wall -Wextra -Werror` compilation and independently inspected JSON. A standalone local shim/fixture can validate fault delivery but earns **zero CMPCT product credit** until the genuine Builder archive and native O18/O19 clients are exercised.

**Status: preregistered, result still unknown.**
