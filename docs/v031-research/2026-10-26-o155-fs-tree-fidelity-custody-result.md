# O155 — Static filesystem topology evidence result
Date: 2026-10-26 UTC
Decision: **POSITIVE EVIDENCE-ORACLE RESULT**, not product code, representation, format, Reader/Writer repair, or release.

## Source and preregistration custody
- Original canonical v0.31 head: `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Unchanged original comparator `src/cmpct/transactions.py` Git blob: `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.
- Preregistered question and acceptance before implementation: commit `d1fed795d7d26dd19efdd46cb45b3cc6027e5739`.
- Tested **code** head `280b3c1a93391526aa6c271905f6afd29b5f2343` (exact `git rev-parse HEAD==EVIDENCE_HEAD` and original comparator blob).
- Independent manifest helper SHA-256 (actual bytes, across both hosts): `90a6ab07a26c490816d597f38558e33dd8b32e8a3952a1ee511d94f724dbdd60`.
- [Source-exact hosted run #40276526074](https://github.com/FCMO-AI/.CMPCT/actions/runs/40276526074): Ubuntu job `121420331591` **SUCCESS**, macOS job `121420331355` **SUCCESS**. Original JSON results retained as [Ubuntu artifact #12630147859](https://github.com/FCMO-AI/.CMPCT/actions/runs/40276526074/artifacts/12630147859) and [macOS artifact #12630636292](https://github.com/FCMO-AI/.CMPCT/actions/runs/40276526074/artifacts/12630636292).
- Artifact ZIP outer SHA-256: Ubuntu `79f296d90f164ba48682076a57746d6479975bcf9d9504fad01266fbd2ed05f6`; macOS `8931e1eda4d996d98be4a246c09cd8a33752247ca7cb976de9c6c2a60476d8f5`.
- Two original job logs were independently parsed into JSON and checked for source identity, scoped controls and semantic differences. Workflow SUCCESS alone was not substituted for the research result.

## Original false equivalences — witnessed again on both hosts

| Real difference | Historical legacy digest, same left/right | New strict witness |
|---|---|---|
| `alias -> target.txt` symlink vs separate regular copy | `3d9b63021f32865c7a1b7393306a0ae3c63a7b33dbd8a5aac6d411410985299d` | LEFT ≠ RIGHT |
| `dirlink -> adir/` vs independent empty directory | `7da44e1610dce31d993cb8fe69891cd7e77d9c317053ce474a5961a343a68f21` | LEFT ≠ RIGHT |
| hardlink alias to `original` vs distinct byte-identical regular copy | `fdc39517d84525ac88d0706f57932aef5f6dfdbb8c12e1290ec315560b1e448d` | LEFT ≠ RIGHT |

The new canonical witness encodes raw relative path bytes (hex), lstat type, mode bits, file content SHA-256, raw symlink target, and deterministic in-tree hardlink equivalence **partitions of relative paths**; physical inode numbers never enter its hash. Original legacy `tree_digest` function is loaded verbatim by compiling its actual AST from original source, rather than copying its implementation into the challenger.

## Independent controls and measured limits

Both hosts:
- Two equivalent synthetic trees created with different actual inode identities yield **equal** new digests and equal canonical manifests.
- A changed regular payload and a changed permission bit each produce **different** witnesses.
- A symlink that initially points to a missing external file continues to have identical witness after its referent is created **outside** the selected root (no dereference).
- A pre-existing FIFO under the tree raises `UnsupportedTreeEntry` instead of silently dropping a special entry.
- A hardlink-class partition is preserved for a two-member group and absent for two independent equal-byte regular files.

**Host-scoped negative:** earlier [run #40276259131](https://github.com/FCMO-AI/.CMPCT/actions/runs/40276259131) had Ubuntu PASS, macOS FAIL when creating raw invalid-UTF8 POSIX filename `b'file-\\xff'`: macOS APFS returned `OSError(EILSEQ)`. It was a *fixture prerequisite*, not a strict witness failure. The instrument was corrected to preserve all three original falsifiers while marking this auxiliary file-name test **SUPPORTED_PASS** on Ubuntu and **HOST_REFUSED_EILSEQ** on macOS. No false claim of macOS support. Original failure remains a negative receipt.

New helper's whole-tree witness differs between the two OS fixture variants because the raw non-UTF8 file was only representable on Linux; that is expected, not cross-host reproducibility failure. The *per-host independent clone* invariant is the one being tested. Filesystem permissions and metadata policy should be specified before claiming parity across hosts.

## Strongest self-critique and promotion boundary

This is a **static-tree / evidence-only** discriminator, not a snapshot-capable trust root or a proof of CMPCT Reader/Writer fidelity. It does not serialize ACLs, xattrs, uid/gid, time, sparse allocation, NTFS alternate streams, Windows mode interpretation or cross-root hardlink ownership; a future tool must separate those feature claims. The walker is `lstat`-based and may race with malicious concurrent renames despite checking regular fd inode and timestamps. The helper's byte streaming avoids `read_bytes()` O(full-size) memory but its manifest memory grows with path count; no CPU/RSS/throughput product measures were taken.

Existing historical digests remain untouched and retain their narrower logical-byte interpretation. Do **not** retroactively invalidate size/create benchmark receipts absent workload-specific dependence on these semantics. No format/release state or product source changed.

## Decision and next highest-leverage path

Issue #312 can now use the stronger source-exact two-host witness as optional future filesystem-extraction **evidence**, while native/Builder/Reader semantic correctness remains an independent court. The cheapest next unclaimed product-discriminator is to apply this oracle to an authentic same-platform Builder→Reader extraction containing symlinks and hardlinks and compare it against an *independent* lstat manifest; but prioritize currently owned high-severity Reader/Writer product-integrity questions instead if they unlock promotion sooner. Resist rewriting frozen historical hashes in place. Keep this draft proof independent and coordinate with owner before adopting into common test utilities.

Discovery: primary O155 evidence question changed from missing comparative proof to **source-exact hosted positive**; no competing claim or shared-state write was made, and no Discovery Engine policy update is earned. Counterfactual prospective lesson: the three minimal pair controls plus canonical inode-independent partition caught the old helper's weak topology semantics without changing any historical test, and testing APFS's filename admission first would have prevented one host-prerequisite failure.
