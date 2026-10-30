# J24G82 — prospective Writer-session prefix crash-cut parity court

Status: **PREREGISTERED / BEFORE IMPLEMENTATION**, 2026-10-30 UTC. Source is existing draft J24G80 PR #829 at exact commit `d29c8b6b64017ab912cfd219d598501e00b62a72`. This is **explicit independent safety replication**, not a duplicate Writer implementation or a shipping change. No code under `src/`, `native/` or the release/format/benchmark gates may change in this lane.

## One question
Does the existing private sequential retained-index Writer oracle of #829 produce the **identical recoverable committed state for every physical generation prefix and every physically torn final-generation footer**, rather than merely the same completed 64-generation archive and final corrupt-tail fallback?

## Prior evidence and why this is not already answered
J24G80 #829 compares SHA and length of all 64 *valid* prefixes, validates the completed checkpoint64, and corrupts the **final** footer. It does not independently exercise the Reader/preflight rollback at *each* intermediate generation when the payload/footer is torn. J24G79 #827 covers 63-generation signed mixed extraction and a final-tail corruption, but not each predecessor in the same source and not this retained-index Writer mechanism. J24G78 #826 shows Reader reopen dominates Writer mutation time, but is not a crash-cut court.

## Baseline, mechanism, simpler control and alternative explanation
- **Baseline:** unchanged public `tx.append_delete`, same Builder-created revision-24 base archive and 64 unique deletion names.
- **Candidate:** exactly the *existing* J24G80 private retained-index algorithm, importing its instrument rather than reimplementing a new Writer.
- **Mechanism:** signed append-only commits and durable per-generation footers make each valid prefix independently readable. A physically incomplete final generation must not erase or misrepresent the preceding authentic state. Retaining index state should preserve the same physical stream as the public Writer on a sequential quiescent session.
- **Simpler control:** compare every complete prefix's original bytes directly, not only the final logical index.
- **Alternative explanation / risk:** two final archives can share valid SHA sequences while a torn intermediate footer produces a different Reader/preflight fallback; a checkpoint64 boundary can have distinct recovery behavior. A benign error in the test's chosen cut offsets may confound this. Validate offsets from footer size and original per-generation lengths.

## Frozen prediction, evidence rung and disproof
Use a deterministic Builder archive with **192 members, 64 distinct deletes**, and **one physical base** for both variants. Save each prefix's exact length, SHA-256 and expected surviving names. For **every generation 1–64**, the public and private variant must have exactly the same bytes/length at that prefix; for each variant assert:
1. a fully committed prefix opens in the original CMPCT Reader and strict preflight with exactly the expected state, member count and strong content verification;
2. cuts at the first appended byte (where possible), last payload byte, beginning of footer, middle footer, and last footer byte, plus one SHA-flipped fully written footer, must expose exactly the *previous* committed generation and strong contents (never a false latest generation);
3. the 64th generation checkpoint must be recoverable from torn tails back to the 63-deletion predecessor and readable when complete.
4. assert the actual cut bytes are distinct, in the intended region, below the valid committed prefix. Record every checked cut and recovery result as raw machine-readable evidence.

**Disproof:** one prefix-byte mismatch, false acceptance, wrong member/index, wrong rollback, unexpected exception, wrong physical offset, or failed strong verification invalidates equivalence. CI success without test execution is not evidence. No threshold adjustment after a failure.

## Scope/carrying cost
First rung: small physical Builder archive, true public and private Writer commits, deterministic corruption, 64-generation exhaustive per-prefix boundary checks, same-code Reader and preflight, source attestations, exact artifacts. Actual crash process interruption, OS durability barriers, cross-process concurrent Writers, inode replacement/ABA, physical xattrs/hardlinks, sparse/cdc, hostile CPU/RSS bounds, Windows network filesystems, entire product benchmarks and native Rust remain **unmeasured**; even a green test is no release/performance credit. This is a **fault-injection approximation**, not a proof that power-loss durability or interprocess leases are solved.

## Concurrency/ownership decision
#829 owns the private Writer-session implementation; #795/#815/#817 own journal/hardlink correctness; #828 owns Windows physical link composition; #574 owns Discovery state. This lane changes none of those surfaces. `docs/discovery/STATE.json` remains untouched. Proceed only as an explicitly preregistered independent replication with a separate research script/workflow and a draft stacked PR; communicate result to #829/#824 without modifying their source.

## Decision unlocked
A green result removes the narrow **per-prefix torn-footer recovery** uncertainty from #829's *quiescent-session oracle*. A red result refutes a safety assumption and blocks session productization until repaired. Neither outcome authorizes a public Writer session API or release.
