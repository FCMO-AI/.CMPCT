# O221b — Lazy-versus-eager random-range checkpoint crossover (preregistered)

Date: 2026-10-27 UTC. Source parent: O221 result `d5094e0297fcd91a822f272da52cd3ac29a6545b`; original instrument blob `d5b97d8a75707243e49d79c4561ad9e40072939d`, owner Reader J24C02 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f` / blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. Science-only new question; O221's already decided Q=64 gate, source, comparator and raw artifacts remain immutable.

## Question, prediction, controls

O221 observed eager indexing losing Q=1 and winning Q=64 by 3.2–6.6x. A two-point linear interpolation predicts break-even around Q=2–3, but this is **not observed**. Would a lazy policy that only constructs the index when a second range is actually requested preserve one-shot economics, and is it still profitable for short interactive sessions? Compare on the same physically authenticated r24 bytes:

1. **baseline** — unchanged installed Reader per query;
2. **eager** — out-of-tree stride-256 checkpoints after Reader open, before first query;
3. **lazy-second** — first query uses unchanged Reader, and checkpoints are created once only before second query; subsequent queries use exact original O221 indexed slicing. At Q=1 this *must not* build a checkpoint.

Test S_CHUNKS and S_CDC at N=262,144 authenticated repeated physical refs, same 17-byte randomized non-monotone tail lookups; Q=1,2,3,4,8,16 with 3 paired fresh-process repeats per alternative. Measure wall+CPU of complete Reader constructor+strict admission+optional index construction+all queries, per-process Linux peak RSS, separately process startup, source SHA, original archive size/digest and identical selected bytes/range-digest across all three methods. Stronger simpler control is genuine baseline and eager O221. The lazy implementation may lose even if eager wins because it pays one O(N) linear range before building.

**Prospective decision:** lazy is worth another product-adjacent test only if its Q=1 median wall and CPU are within 5% of unchanged Reader in both types, and its Q=4 medians save >=10% wall **and** CPU versus unchanged Reader in both types, with no >8 MiB median kernel HWM increment and exact byte equality on all queries. If any fails, report `LAZY_SHORT_SESSION_NOT_PROVEN` without changing thresholds. Also report whether eager wins Q=2/3 but loses Q=1. Non-green scientific result is a valid outcome; no evaluator weakening.

## Threats / scope / exit

- The extremely compressible one-byte RAW repeated-reference fixture is an **upper-bound-like metadata-heavy regime**, not representative mixed-codec workload. No general product claim even on positive result. Journal changes, source mutation, platform parity, index ownership/lifetime and physical I/O are independent.
- Reuse the exact independently installed unmodified Reader/fixtures; scientific adapter exists only outside product. Never mutate `src/cmpct/reader.py` or `research/o221_chunk_range_strided_oracle.py` for this episode. No archive format, optimizer, gate, release or threshold change.
- Do not infer break-even from interpolation after direct Q measurements are available; raw repeated observations and negatives outrank model expectation.
- If hosted results exist, independently audit raw structure and arithmetic, then publish truth and notify #569. If host fails, keep pending; do not claim wins.
