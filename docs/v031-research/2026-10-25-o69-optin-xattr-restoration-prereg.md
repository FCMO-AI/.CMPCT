# O69 — Opt-in strict xattr restoration: pre-implementation contract

Date: 2026-10-25 UTC. Status: **PREREGISTRATION / NOT PRODUCT EVIDENCE**.

## Exact authority and ownership
- Canonical base: `FCMO-AI/.CMPCT` / `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, revision 24, published v0.30.0.
- Exact Reader blob: `e716233403dabd0966863c45635e18fa5ac6afb8`.
- O65 Builder capture integrity is owned separately by PR #420. O69 touches only **optional Reader restoration reporting**, not Builder capture, transaction Reader preflight (#303/#305), sparse compression or file-format semantics.
- Existing portable default is documented in `docs/PORTABILITY.md`: unsupported destination metadata restoration is best-effort; cannot retroactively declare the old mode broken or require privilege by default.

## Concrete problem and primary question
Current `CMPCT.extractall(metadata=True)` calls `_restore_extra_metadata`, where xattr `os.setxattr` errors are swallowed, and where absence of `os.setxattr` silently skips authenticated xattrs. A caller seeking explicit **xattr restoration success evidence** has no opt-in failure signal. Does a narrowly scoped `require_xattrs=True` API option expose these failures without perturbing the default portable restoration contract?

## Hypothesis / alternatives / controls
Choose an opt-in keyword-only-like final keyword parameter on `extractall`; maintain exact existing default. `require_xattrs=True` with `metadata=False` is contradictory and must raise before creating destination; when an archive contains xattrs but `setxattr` is unavailable, reject before destination creation. If `setxattr` raises on a given member, propagate contextual `IOError` with chained cause rather than claiming full restoration. When no xattrs exist, strict mode may succeed even without a host API. Preserve best-effort uid/gid and timestamp behavior in both modes; this is **not** full filesystem-identity verification.

Simpler controls: existing default unchanged; raw Python `os.setxattr` error injected deterministically; real Linux `user.*` xattr roundtrip where permitted. Larger alternatives rejected now: making metadata failure fatal by default (violates published portability), a new revision-25 metadata grammar (unnecessary), atomic whole-tree publication (separate Reader safety owner), logging warning only (not machine-actionable).

## Prospective acceptance, falsifiers and exclusions
1. With an authenticated r24 archive carrying xattrs, injected `OSError` produces success in **default** extraction but a clear failure in **opt-in strict** extraction. Exact payload bytes still materialize, and the partial-destination caveat is explicit.
2. A missing `setxattr` API and a contradictory metadata=False flag are rejected before the destination is created; no recorded xattrs means strict succeeds even on hosts without the API.
3. Successful xattr restoration preserves exact value bytes; no new format bytes are emitted, no archive creation behavior changes, existing positional `extractall` calls remain accepted.
4. Only a specialized installed-package, genuinely executed cross-platform test court may support a cross-platform implementation claim. Real xattr proof may be Linux-only, and skips must be counted, not silently passed.
5. Do not count these controls as proof of complete metadata preservation: restore remains nontransactional if a late `setxattr` fails; uid/gid, ACLs, timestamps, root-path races, hardened fsmeta preflight, other platforms, cost and portability remain separate work.

KILL/NARROW if the mode cannot clearly distinguish missing/failing restoration from success without changing the default contract, or if a cheaper owner already implemented the same exact feature. No release/version bump or policy modification. An exact-head CI result, not a passing mock alone, is required before product claim.
