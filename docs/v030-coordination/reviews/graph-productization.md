# Adversarial review — T03 graph/productization

Resolve these before T03 becomes `DONE`. These are product-boundary correctness issues, not a request to retreat to research-only facades.

## P0 — canonical r25 must compete against genuine canonical r24 bytes

A canonical r25 candidate must not publish merely because it beats an accepted-v0.29 research floor on a staged profile tree. The staged r25 tree includes reserved filesystem framing and is not byte-equivalent to a genuine r24 build of the original filesystem tree.

Release invariant:

- final product selection compares complete canonical r25 bytes against complete genuine canonical r24 bytes for the **same original user filesystem tree**;
- exact tie conservatively retains r24;
- no r25 archive may publish if it is larger than genuine r24, even when it beats a staged research floor;
- preserve creation-speed work by building independent r24/r25 candidates concurrently or sharing byte-identical analysis; do not skip the product floor to save encoder time;
- report both `r24_product_bytes` and `r25_product_bytes` in product selection stats;
- keep a regression test where a staged r25 beats its staged research floor but loses to genuine r24 and require exact r24 publication.

Footnote: the frozen 137,501,815 B research frontier remains useful causal evidence. It is not a substitute for the canonical product no-regression floor once r25 adds filesystem framing that r24 represents differently.

## P0 — user-tree identity vs internal graph-tree identity

The canonical product adds `FS.FILESYSTEM_MANIFEST` to the staged content graph. Public verification must not use one field name for two different tree identities.

Required resolution:

- define and test both identities explicitly, e.g. `user_tree_sha256` and `content_graph_tree_sha256`;
- keep the public/common `tree_sha256` contract consistent with `canonical.treehash(user_source)` if that is the cross-version comparison identity;
- canonical strong verification must prove the user-visible tree, not merely trust a manifest-declared digest;
- keep `filesystem_manifest_sha256` as the independent filesystem-semantics identity;
- keep a regression test: `canonical.strong_verify(canonical.build(source))["tree_sha256"] == canonical.treehash(source)` for an r25 archive containing empty dirs + links + manifest.

## P0 — signed filesystem timestamps

`st_mtime_ns` is signed on real filesystems. r25 must not encode a negative timestamp and then reject its own archive. Match r24's timestamp domain with a bounded signed i64 nanosecond value, or fail r25 admission before writing. Keep a negative-mtime round-trip test where the host filesystem supports setting it.

## P0 — cross-platform safe-symlink validation

Safe-symlink policy must reject escape targets under **both POSIX and Windows lexical semantics**, independent of the host running the verifier.

Required resolution:

- reject POSIX absolute paths, Windows drive/UNC/rooted paths, and any `..` component after either slash spelling is interpreted as a separator;
- retain `--unsafe-symlinks` as an explicit caller choice, not an implicit platform exception;
- keep hostile tests for `../x`, `..\\x`, `/x`, `C:\\x`, `C:/x`, UNC/rooted forms and benign relative targets.

Footnote: an archive validated safely on Linux must not become traversal-capable merely because the same bytes are extracted on Windows later.

## P0 — delimiter nomination regression

Geometry delimiter regularity must score complete inter-occurrence intervals only. Censored prefix/suffix edge fragments are nomination bias, not complete recurrence observations. Preserve occurrence/segment/search bounds, deterministic tie-breaking, and exact transformed payload/archive pricing as the admission authority.

## P1 — remove process-wide research-module mutation from canonical import

Canonical profile identity/dispatch must be deterministic without import-time mutation of research-module magic/global state. Preferred solutions, in order:

1. parameterize the single semantic owner/writer/reader with an immutable profile descriptor;
2. move owning integration modules to canonical r25 identities and keep old research magics only in historical/research compatibility modules;
3. another design that is demonstrably thread/import-order safe.

A mutate-and-restore context is insufficient if parallel builds/readers can overlap.

## P1 — metadata restoration policy must be explicit

Best-effort `chown`/xattr/mtime behavior may mirror existing r24 portability policy if documented accurately: archive metadata remains authenticated even when the destination filesystem/user cannot represent or apply it. Successful extraction is not proof that every host applied every metadata attribute. Preserve exact file/link content identity separately from best-effort metadata application.
