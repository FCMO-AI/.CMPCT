# J24G68 — public 64th-generation checkpoint preserves physically signed mixed xattr identity

Date: 2026-10-30 UTC. **PRE-RESULT / SCIENTIFIC REPLICATION, NO PRODUCT OR RELEASE CREDIT.** Immutable research parent is J24G66 #810 at `f9246d33748fb97532d711f0a81760c3505a7a4a`, inherited signed journal replay blob `03743ca2a06c022c2ec64243a90fe373cf91e899`. This prediction must be committed before research instrument/workflow implementation.

## Exact scientific question / baseline
J24G66 source-exact physical evidence demonstrates 63 public mixed signed one-op generations with 8 originally Builder-captured real xattr identities, ending with 5 tagged identities and 117 logical members, and strict extraction on Ubuntu/macOS. **The 64th public mutation is a different execution owner:** the Writer switches from a delta to a complete signed checkpoint. Does that checkpoint retain the identical path-keyed sparse fsmeta identity after a tagged member is renamed, and can an independent parser authenticate the actual new physical checkpoint and recover the prior genuine 63-delta chain if the latest footer is corrupt?

Existing J24G47/#773 has a checkpoint repair and tests, but does not settle the precise **J24G66 physical mixed 63-generation and same-name-delete/put xattr fixture**. This is replication across a previously untested composition, not a competing Writer implementation. J24G64/#808 owns replay optimization; J24G67/#811 owns a simpler DELETE read-performance control. No overlap with these narrow implementation claims.

## Hypothesis / predicted observable
Run unchanged J24G66 physical Writer fixture as an imported prior test on each host, then perform `transactions.append_rename` from the tagged `r0000.dat` to new `z-checkpoint-owner.dat` as exactly operation 64 on a disposable physical copy. Predict:
- 65 physically SHA-256-authenticated footer records are linked, last footer kind=checkpoint (0) and previous pointer equals the actual 63rd-delta footer.
- Same file inode and full original archive prefix are retained (append-only), with checkpoint-specific stored-byte increment explicitly charged.
- The shipping Reader reports `delta_depth==0`, correct 117 final members and byte-identical unpacked effective index to independent name-keyed replay from original primary plus 64 public operations.
- Sparse `fsmeta.xattrs` follows the renamed tagged identity, never resurrects on the deleted/reintroduced same name `f0042.dat`; strict physical extraction restores each expected xattr value and every final content byte.
- Corrupting only the final checkpoint footer digest on a **copy** recovers the previous signed 63-delta generation intact, including its original path-keyed xattrs and payloads.
- Linux and macOS must independently satisfy these claims. Lack of actual xattr support is **not** a pass.

## Stronger / cheaper controls
Control A: unchanged public Builder/Writer/Reader and preregistered J24G66 parent court; no synthetic checkpoint writing shortcut. Control B: source-exact old `_apply_journal_ops` applied once to a deep-copied pre-checkpoint index, compared at MessagePack byte level. Control C: detached Python interpreter that imports *no CMPCT product code*, decodes primary/63 genuine signed physical delta footers from the immutable prior archive, replays names/xattrs by logical path identity, independently reads the 64th newly emitted checkpoint footer, and verifies exact physical MessagePack equality, SHA-256 and prefix bytes. Control D: strict extracted xattr readback plus corrupted checkpoint-footer recovery.

Existing release v0.30.0/r24, format, benchmark gate, security claims and prior experiment are kept unchanged. This is a correctness falsifier, not a performance productization.

## Kill / narrow conditions
Any wrong physical footer kind/prev pointer/hash, digest/header/index mismatch, file-count/depth mismatch, output byte difference, wrong tracked xattr, same-name resurrection, source mutation, source SHA drift, side effect on the original archived fixture, failure to recover the previous authenticated generation, or detached-referee false acceptance **kills/narrows** the hypothesis. Host filesystem xattr incompatibility is an infrastructure limitation, not a pass. If the underlying J24G66 physical fixture fails here, preserve that root failure rather than weakening it. If a valid counterexample appears, save the original and minimal changed archive, exact HEAD and host, and route it to #795/#808 owners.

## Accounting and scope
Report complete original/after archive bytes, append/checkpoint byte premium, logical content bytes, member counts, sparse xattr identities, wall/CPU for *checkpoint generation only* (no causal A/B), and exact hashes of physical artifacts/results. Python traced memory and CPU/wall startup are not claimed as real RSS or product speedups. Native Windows xattr, privileged owner overrides, hardlink inode sharing, full cold-open A/B, hostile simultaneous publication, full ZIP/Zstd matrix, release gates and complete recovery matrix remain **unmeasured**.

## Concurrency and prospective decision
An isolated child of #810; no change to `src/`, `docs/discovery/STATE.json`, PR #810/#808/#795/#811, benchmark fixtures, published `main` or version. If both hosts pass the exact-head source-authenticated court and independent physical audit, mark **J24G68_PHYSICAL_CHECKPOINT64_FIDELITY_PASS** limited to those hosts/corpus and hand evidence to #795 and #808. No product promotion. If negative, retain original full evidence before fixing only the instrument or candidate owner. No Discovery Engine policy lesson is presumed.