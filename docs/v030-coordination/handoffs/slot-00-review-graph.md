# Slot-00 adversarial review — T03 graph/productization

Resolve these before T03 enters REVIEW. The current architecture is promising; these are product-boundary correctness issues, not a request to retreat to research-only facades.

## P0 — canonical r25 must compete against genuine canonical r24 bytes

Current `canonical.build()` can publish an r25 candidate as soon as it beats the accepted-v0.29 **research floor on the staged profile tree**. That staged tree includes the reserved filesystem manifest and is not byte-equivalent to a genuine r24 build of the original filesystem tree.

Therefore `research_bytes < staged_v029_bytes` does **not** prove `r25_product_bytes < genuine_r24_product_bytes`.

Release invariant:

- final product selection must compare complete canonical r25 bytes against complete genuine canonical r24 bytes for the **same original user filesystem tree**;
- exact tie conservatively retains r24;
- no r25 archive may publish if it is larger than genuine r24, even when it beats the staged research floor;
- preserve creation-speed work by building the independent r24/r25 candidates concurrently or by sharing byte-identical analysis; do not skip the product floor to save encoder time;
- report both `r24_product_bytes` and `r25_product_bytes` in product selection stats;
- add a regression test where a mocked/staged r25 beats its staged v0.29 floor but loses to genuine r24 and require exact r24 publication.

Footnote: the frozen 137,501,815 B research frontier remains useful causal evidence. It is not a substitute for the canonical product no-regression floor once r25 adds filesystem framing that r24 represents differently.

## P0 — user-tree identity vs internal graph-tree identity

The canonical product adds `FS.FILESYSTEM_MANIFEST` to the staged content graph. `canonical.treehash(source)` still returns the historical **user-content tree** hash, while `canonical.strong_verify(r25_archive)` currently forwards the underlying graph verifier's `tree_sha256`, which includes the reserved internal manifest.

A public pack/verify pair must not use one field name for two different trees.

Required resolution:

- define and test both identities explicitly, e.g. `user_tree_sha256` and `content_graph_tree_sha256`;
- keep the public/common `tree_sha256` contract consistent with `canonical.treehash(user_source)` if that is the cross-version comparison identity;
- canonical strong verification must prove the user-visible tree, not merely trust a manifest-declared digest;
- keep `filesystem_manifest_sha256` as the independent filesystem-semantics identity;
- add a regression test: `canonical.strong_verify(canonical.build(source))["tree_sha256"] == canonical.treehash(source)` for an r25 archive containing empty dirs + links + manifest.

## P0 — signed filesystem timestamps

`capture_filesystem_manifest` stores `st_mtime_ns`, which is signed on real filesystems, but `decode_manifest` rejects every negative mtime. A pre-1970 file can therefore be encoded and then rejected by the same r25 reader.

Match r24's timestamp domain: admit a bounded signed i64 nanosecond value (or fail r25 admission before writing, but do not emit self-unreadable bytes). Add a negative-mtime round-trip test where the host filesystem supports setting it.

## P0 — delimiter nomination regression

The exact-head Geometry failure is correctly fixed in the current branch: `_delimiter_rank` now scores complete inter-occurrence intervals only and retains exact pricing as the admission authority. Preserve that implementation and its regression tests during final integration.

## P1 — remove process-wide research-module mutation from canonical import

`install_revision25_profiles()` currently mutates G04/PrefixGraph/release-reader module magic globals and `RC` globals at import time. This can make test/benchmark behavior depend on import order and is unsafe for concurrent long-lived processes.

Before promotion, make canonical profile identity/dispatch deterministic without process-global mutable installation. Preferred solutions, in order:

1. parameterize the single semantic owner/writer/reader with an immutable profile descriptor;
2. move the owning integration modules themselves to canonical r25 identities and keep old research magics only in historical/research compatibility modules;
3. another design that is demonstrably thread/import-order safe.

A temporary mutate-and-restore context is not sufficient if parallel builds/readers can overlap.

## P1 — metadata restoration policy must be explicit

Best-effort `chown`/xattr/mtime behavior mirrors existing r24 portability policy and is acceptable if documented accurately: archive metadata remains authenticated even when the destination filesystem/user cannot represent/apply it. Do not describe successful extraction as proof that every host applied every metadata attribute. Preserve exact file/link content identity separately from best-effort metadata application.
