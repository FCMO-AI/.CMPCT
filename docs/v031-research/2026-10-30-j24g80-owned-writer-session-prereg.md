# J24G80 — Owned Writer Session as a charged research oracle (FROZEN BEFORE EXPERIMENT)

Date: 2026-10-30 UTC. Branch parent: #826 exact `42d60372fb71e574e1271f14402b5ca325ed1147`; inherited Writer source Git blob `71bbc8a989d1da79d0f0dbe44f7f5c39f3304854`. This is **research-only**, not a shipping Writer feature or a release candidate. See issue #824, Writer stage attribution #826 and multiwriter negative #289/#290. All authoritative parser/release/format/benchmark law remains unchanged.

## Evidence, question and competing actions

J24G78 physically attributed ~88–90% of 63 sequential public deletes at 8,192/32,768 members to repeatedly constructing the Reader; deferring a copy saved only 8.45–8.73% versus a fixed 10% materiality bar. J24G74/#820 and J24G76/#823 are separately owned experiments for Reader replay on each open, not this question. Concurrent PR #828 handles Windows hardlinks; do not touch its sources.

**Primary question H1 (bounded no-concurrent-writers oracle):** if exactly one operator owns a revision-24 archive across 63 distinct public-equivalent journal commits and can retain the decoded index plus current footer identity between commits, does a research-only session reproduce *every physical archive byte after every commit* while eliminating most of the observed reopening cost? This tests information-ownership headroom, not a public API or cross-process correctness. The strongest simpler control is unchanged public `tx.append_delete` on the same Builder base files, names and host.

**Strongest alternative H2:** the apparent Reader savings could be consumed by maintaining signed metadata identity, reserializing checkpoints, hardlink guard scans, footer fsync, or expensive initial construction. Check real full Writer wall/CPU and actual byte parity, not just stage microtimes. The earlier #826 copy-elision result already rejects copying as a primary path.

**Safety disqualifier H3:** unguarded retained state is *not* generally safe when independent writers can change the archive. PR #289 reproduced lost logical updates from stale predecessor pointers even when physical appends were serialized. This study MUST NOT claim general concurrency or promote a session cache without a transaction-wide lease and current-fd/path/alias identity. Historical PRs #295/#304/#409 own cross-platform Writer leases/source admission; do not reimplement their shipping scope here. A session oracle under explicitly exclusive, quiescent conditions does not fix that problem.

## Prospectively frozen physical design

- Same source-exact installed package, single Builder source archive for each family, 63 public-equivalent one-op distinct deletes; families 8,192/middle and 32,768/tail; 64th extra delete triggers a full checkpoint. Ubuntu 24.04/Python 3.11 is the first, limited host. Do not claim macOS/Windows.
- A = unchanged public `tx.append_delete` called 64 times. B = isolated *research-only* in-memory owned-index method using original `_apply_journal_ops` and `_append_generation` for every individual commit; no skipped fsync, compressed footer or generation. Each delete must have its own separately authenticated footer and its own intermediate valid Reader state. No batching of several operations into one transaction.
- Run balanced A/B/B/A, each trial on an identical copy of one Builder base. Preserve per-call wall+CPU, whole 63-call wall+CPU, initial base SHA, after-each-generation physical SHA, total bytes, final exact MessagePack index, strict preflight, strong full verify, checkpoint64 and corrupt-tail recovery. Hash all outputs after mutation *outside* the timed region identically for A/B; do not silently count digesting as Writer time.
- Require *all 64 per-generation SHA-256 and physical-byte lengths to match exactly* across all trials before performance credit. Verify no new format, codec, declaration, indexes or release test rules. Attest exact parent/prereg HEAD ancestry and Git blob identity.
- Measure optional traced Python allocation peak separately from full Writer wall; do not treat tracemalloc as process RSS or data on other hosts. Report stored bytes, create/setup cost separately, and note no independently exported physical wire archive until actually available.
- Keep source files, Reader, native core, frozen benchmarks, official performance gate, release numbers, Discovery STATE and all competing owners unchanged. No paired archive can be regenerated between A/B.

## Prediction, kill and interpretation

1. **Semantic gate:** any mismatch in a single physical post-generation SHA or length, logical files/index, recovery, strict preflight, checkpoint64, successful public control, or source custody is a hard H1 failure, regardless of speed. An infrastructure failure is not scientific loss.
2. **Mechanism headroom:** prospectively require B/A full 63-commit wall ratio <=0.25 (>=4x acceleration) in **both** sizes, with at least 20% of A's measured time attributable to Reader reopen in already preserved #826, and no additional bytes. This is a high-upside *oracle* result, not shipping product credit; any B/A >=0.25 in a family narrows/retire this specific mechanism as a primary high-leverage path. Preserve raw observations, no threshold edits.
3. **Concurrency veto:** even perfect H1 physical equality in a quiescent sequential experiment is ineligible for productization until demonstrated transaction-wide cross-process ownership, immutable archive inode/path identity, fsync/crash recovery and correct hardlink/xattr semantics. If the owner cannot show these without a pathological lock lifetime or portability regression, retire or reframe the session proposal.
4. The next fork is either: (a) if H1 passes, explore smallest lease-scoped public session architecture as a different preregistered experiment coordinated with #295/#304/#817/#795; (b) if B fails, return to per-call Reader ownership #820/#823 or checkpoint bytes economics; (c) if safety debt dominates, prioritize corrections rather than timing. The baseline is permitted to win.
5. A successful GitHub workflow is only test-execution evidence. No merge, release, performance headline, or mutable Discovery-policy credit results from H1 alone.

## Concurrency / custody / priority

This branch is an independent **oracle** on #826, not an implementation competing with #795/#817 or a claim against #295/#304. Existing PR #826 owns the causal Writer stage result; record the result back to #826/#824 when the exact-head execution completes. Check neighboring PRs and relevant target Git ref immediately before any shared write. Preserve J24G78 raw negatives. Do not amend this prereg after outcome; supersede by separately named prereg if necessary.
