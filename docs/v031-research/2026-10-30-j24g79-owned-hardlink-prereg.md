# J24G79 — Prospective private-decoder ownership transfer × authentic hardlink / xattr journal court

Date: 2026-10-30 UTC. **Research-only immutable preregistration; no shipping code/format/version/release/CI gate change.** Exact source parent PR #820 `c15459f70001800f3781925efc7356409eb03ffe`; authoritative published main remains v0.30.0 / revision 24. This child owns only its new J24G79 research/CI/note surfaces. No overlapping edits to #795/#817/#820/#823 or shared discovery STATE.

## Decision and alternatives (before any instrument)

J24G74 / #820 showed a large complete Reader-open improvement when freshly decoded MessagePack checkpoint/deltas are transferred rather than copied; J24G76 / #823 extended delete-only sizes. The remaining **distinct** proof question is whether the ownership boundary preserves a real signed physical `K_HARDLINK` topology with sparse inode xattrs during ordinary 63-generation mixed public Writer history, rather than only synthetic rows or regular-file xattrs.

Primary H1: For a physically created owner + alias (same inode on POSIX), sparse xattrs and 63 unrelated public one-operation ren/del/put generations, the unmodified shipped Reader, inherited copy-preserving `FactoredCMPCT` and `OwnedCMPCT` must reconstruct identical complete MessagePack indices and all file bytes, while strong verify, strict preflight, hardlink extraction identity and exact xattrs remain correct. The owned/factored conservative admission must either explicitly select the owned route or both produce exactly equal fallback/explicit-error semantics; **no success if semantic correctness is lost**. No numeric performance claim is solicited.

Strongest controls: identical physical archive input, inherited Reader, inherited copy-preserving Reader, independent reference replay from authenticated physical generations, SHA fingerprint of retained archive before/after, and POSIX physical inode/link observations. The only code introduced is a separate research harness and hosted evidence workflow, not a Reader patch.

Prospective kill/narrow: any mismatch in logical index, serialized index, bytes, hardlink inode, POSIX native xattr, footer recovery, source fingerprint, Reader/preflight, or malformed committed data means not productizable on that scope. If Windows cannot represent the same physical hardlinks/xattrs under the inherited Builder, mark that host NOT_COVERED rather than invent proof. If inherited Builder/Writer itself fails before candidate comparison, isolate **baseline blocker**, do not classify it as an owned replay regression. If the candidate falls back, this court may prove compatibility but earns zero optimization admission credit.

Second negative control: after publication `index/files/by/fsmeta` descriptors are mutable public aliases. Mutating an exposed descriptor in one completed Reader is explicitly *not* evidence that the private decoded graph remains unique later. Reopen an untouched physical archive from fresh Reader and verify it remains unchanged. Public post-open mutation is not an authorized candidate optimization.

## Cost and evidence rung

Run the cheapest honest host physical test: one small multi-operation real archive per OS, not the already-saturated 32K latency matrix. Preserve physical archive, original SHA/MessagePack index, raw receipt and exact source Git blobs/HEAD; benchmark none. Linux and macOS POSIX xattrs, Windows logical semantics only if native hardlink actually captured. Distinguish no-product-import independent wire checks from inherited Reader checks. Tail truncation/CRC corruption test recovery of previous authentic generation; checkpoint-64 and hostile owner-rename are outside initial claim (already owned #813/#817).

## Decision criteria and handoff

Verdict only after an exact-head hosted result: `H1_PHYSICAL_PASS`, `OWNER_SOURCE_BLOCKED`, `FALLBACK_NOT_ELIGIBLE` or `H1_FALSIFIED` per platform, with no cross-platform overclaim. External physical interpreter preferred; source-side verification alone is weaker. Notify #795/#817/#820 only with result-changing evidence. Product/release credit remains zero until actual integration and official gates. No policy change, no shared discovery write on speculative findings.
