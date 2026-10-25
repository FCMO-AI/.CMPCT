# O79b — held-out multi-member VZIP whole-recipe SHA generality

Date: 2026-10-25
Status: SECOND PROSPECTIVE EXPERIMENT, written AFTER observing O79 original result; O79 original thresholds/results remain immutable.

Original O79 #436 at source-exact CI run 40190864002 proved 3 one-member families with SHA-verified speedup but exposed a 2 MiB random negative. This follow-up is a new structural-transfer question, not an attempt to improve a disappointing original result.

**Hypothesis:** The existing r24 VZIP whole-recipe SHA proof remains exact and fails closed when a selected range belongs to the *first* Deflate member but physical corruption affects a *different unselected* later member (Deflate or STORED). The reference, unchanged CMPCT.read_range, may skip those later members and return apparently correct selected bytes, distinguishing whole-recipe SHA from local CRC. Use true unchanged historical Builder/Reader from O76, real installed wheel, deterministic ZIP with three members: first repeat Deflate, STORED note, second independently structured Deflate. All original ZIP bytes and extracted entries must be exact.

**Controls:** original retained Deflate threshold 0 (all eligible original streams), existing Reader.read_range and Reader.verify, true selected 64B inside first Deflate. Independently flip one encoded byte in later Deflate physical blob and one in later STORED physical blob; do not change index/footer. The strong oracle must reject both, full verify must reject both, and the original archive must pass read/verify/extract. Record whether original Reader incorrectly *accepts* each corruption, but do not predetermine the observed answer or weaken any assertion to force weak false-green. End-to-end provenance and original archive SHA preserved.

**Kill conditions:** if a true three-member VZIP is not emitted, source SHAs disagree, the SHA oracle accepts any changed bytes from a later member, full verification accepts corruption, or an original valid source cannot be exactly reconstructed, the claimed multistream transfer fails or is narrowed. A contrary weak Reader behavior is valuable; it does not falsify SHA correctness. No prospective generic ≥8× timing threshold on this held-out structure; record wall/CPU but do not cherry-pick against single-member O79.

**Boundaries:** No product changes, no full official benchmark, no new format, no signing/authenticity claim, no memory/cold-I/O/platform claims. Reuse the exact original O79 oracle without changing it; preserve both original positive and random negative. The test earns only held-out scientific evidence and informs owner review.

**Next action:** execute source-exact hosted independent runner from the same branch, preserve raw receipts; notify O76 owner and leave merge/release unapproved.
