# v0.30 Logs decoded-pack hash ownership — productization preregistration

Status: **productization attempt earned; release credit unpaid**.

## Authority and evidence

Parent authority is `agent/v030-authoritative-integration@e9028dd9e9e6a6c47c1228d9da32a37bf5fc378e` / PR #56. Production remains v0.29.0 / r24.

Research provenance is PR #147. Exact-head run `35439104672` / artifact `10582709135` (`sha256:99a88c989965f494a79ffd57759b543ac92a1dfe9a7a56aaf0aac3566f9b4a9d`) measured four balanced fresh-process Logs pairs at 13.6079%, 7.1196%, 7.6806%, and 9.2170% wall improvement, median **8.4488%**. All seven decoded packs were exact-partition owned (9,638,036 / 9,638,036 decoded bytes), output tree identity was exact, and CPU moved with wall.

The same run rejected gap, overlap, and out-of-bounds ownership; corruption injected after the retained pack CRC was caught by an owning logical-member SHA before publication; ordinary strict reader surfaces retained pack SHA.

Parent exact-head whole-tree runtime authority `35437105192` measures Logs extraction at ~`1.353115x` vs accepted v0.29. The frozen per-workload ceiling is `1.25x`, requiring ~7.62% reduction from this exact parent measurement. Full transfer of the latest 8.4488% oracle projects ~`1.2388x`. The margin is therefore real but narrow enough that product evidence is mandatory.

## Product seam

Implement at the Logs fused full-extraction owner, not in the base Archive reader:

1. derive, from authenticated `reader.files` plus scanned pack `usize`, the set of pack IDs whose direct `pack`/`raw` storage intervals form an exact non-empty, non-overlapping, no-gap partition of `[0, usize)`;
2. only the full fused transactional extraction session may defer `SHA256(decoded_pack)==pack_header_sha` for those pack IDs;
3. retain pack header identity, codec, compressed/decoded size bounds, decompression, exact decoded length, CRC32, every direct logical-member SHA, every derived-member SHA, filesystem-manifest/content identity, output budget, path/symlink policy, staging rollback and final publication semantics;
4. packs without exact ownership remain strict individually;
5. `strong_verify`, `read_member`, `read_member_with_stats`, recovery probes and the ordinary base Archive remain strict and continue executing pack SHA.

No format bytes, writer bytes, selector, threshold, benchmark identity, locality law or release comparator may change.

## Required product proof

Before ready/merge:

- product-scoped regression for exact-partition admission and mixed strict fallback;
- authenticated malformed gap/overlap/out-of-bounds cases fail closed or retain pack SHA;
- post-CRC/pre-member corruption fails before publication and preserves an existing destination;
- selective read and strong verify demonstrably reject pack-SHA corruption;
- fresh-process same-source A/B on frozen Logs with exact tree identity, wall + CPU + RSS/temp-I/O where available;
- product median wall improvement must remain > the exact parent Logs gap; otherwise kill/revert rather than weaken the 1.25x gate;
- exact-head normal CI must remain green.

Even a successful Logs row does not unlock v0.30. Parent runtime authority still has ML create around `1.40x` and aggregate median extraction around `1.19x` (owned by ML after Logs is repaired), while whole-process-tree RSS is already green at 1.0x.
