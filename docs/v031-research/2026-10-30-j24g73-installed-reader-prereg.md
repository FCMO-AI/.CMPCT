# J24G73 — preregistration: installed Reader mixed physical A/B

Date: 2026-10-30 UTC. **Frozen before implementation/host observations.**
Science only; no product, Reader, Writer, format, benchmark, release, version, threshold or Discovery-state mutation.

## Authority, lineage and ownership

- Released main: `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24.
- Exact source parent: #808 `41cd7f88d9fede55a495f36e78126b26eff85880` (research-only), factored oracle blob `7657a41d11f2b3c8136c0b69cfe62401f9b19ccb`, Reader blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`, replay blob `03743ca2a06c022c2ec64243a90fe373cf91e899`.
- #795 owns shared journal product integration; #808 owns the general in-memory mechanism; #810/#813 own signed-xattr/checkpoint physical conformance; #814 already settled same-input simple-vs-general helper economics; #815/#817 own hardlink Writer and prospective source custody. This independent rung owns ONLY a read-only installed-Reader full-open A/B on unchanged physical Writer archives.
- `docs/discovery/STATE.json` on main is a stale cache, #574 owns its reconciliation. No shared-state edit.

## Primary question and mechanism

Does using #808's source-exact **conservative** factored replay within a research-only subclass of the installed CMPCT Reader materially reduce full Reader open latency on actual 63-single-delete and 63 mixed Writer archives, while returning exact index/MessagePack, all member bytes, signed physical fsmeta and inherited corrupt-tail recovery? This is NOT a shipping patch.

Baseline: original `CMPCT(path)` unchanged. Candidate: subclass overrides ONLY `_index_from_footer`, keeping identical footer search, SHA, payload decode, Reader downstream and public Writer output, but defers journal application to the unmodified #808 `factored(base, deltas)`. Stronger simpler control: original Reader with same physical bytes; specialized bisect #811 is not reimplemented and is retained as lower-rung alternative under #814.

Alternative explanation: physical footer decoding, source installation or deep copies consume all observed savings; the synthetic #808 speedup may vanish at full Reader boundary. Other possible disproof: sparse xattr identity silently changes or recovery changes despite index parity for ordinary files.

## Prospective tests and decision

1. Build two genuine r24 archives from generated public data, using Builder and public Writer ONLY: (a) 2,111 initial / 2,048 surviving members after 63 valid deletions; (b) 128 initial / 63 mixed one-op generations (rename/delete/put). On POSIX explicitly capture at least two real xattrs at build; Windows tests legitimate no-xattr fallback and is not counted as physical xattr evidence.
2. Authenticate physical footer chain (64 footers: base checkpoint + 63 one-op updates) and checksum on both archives, using inherited independent J24G62 wire helper, not Reader alone. Assert same immutable physical bytes within A/B.
3. Run 8 alternating A/B/B/A blocks (32 raw open samples per route/host) after common warmup, time only opening/closing the Reader (no process startup). Require identical effective index and exact MessagePack bytes, read/verify checks over all members; check preflight on the identical archive. Report complete archive bytes, cold/open semantics, Python traced allocations, and process peak RSS in independent child probes if portable. No conclusion from one median without the raw measurements and host variability.
4. Signed-file metadata and positional identity must match after rename, delete and replacement; require strict native restore on Linux/macOS when supported. Exercise checksum-corrupt latest footer and truncated tail on disposable copies and compare the recovered logical state against original Reader, not an invented expected state.
5. Prospectively label **`FULL_READER_SPEED_SEED`** only if original-vs-candidate open median gain >=2.0x **on the 2,048-delete case on >=2/3 hosts**, with zero semantic/control failures and no >+2MiB traced memory penalty; otherwise **`NARROW_OR_RETIRE`**. Mixed+xattr correctness cannot be traded for speed. Record all host-specific negative outcomes. Any positive result remains unmerged candidate evidence; real RSS, hardware cold-open, hardlinks, native ABI, full release gates and hostile recovery remain separate.

## Risk, cost and anti-cheating

Preserve exact source hashes, original/variant input archive SHA, full archive byte count, all 64 footer identities, source install identity, baseline behavior on malformed/corrupt input, and unchanged public codec/format semantics. Use independent receipt arithmetic and provenance checks. Do not alter baseline source or benchmark harness, drop failing cases, suppress xattr provider errors to earn a pass, or equate an instrumentation error with algorithmic loss. If the candidate cannot be safely integrated under subclass semantics, stop and retain the negative rather than patching production during this lane.

## Counterfactual and promotion

A cheap installed-Reader A/B can falsify whether replay-only results transfer to the real product boundary before a risky production integration. A success is scientific product-path evidence, not release speedup. #795 remains sole integration owner; #808/#810/#813/#814 receive results by reference. No inference of merge, promotion or v0.31 release.
