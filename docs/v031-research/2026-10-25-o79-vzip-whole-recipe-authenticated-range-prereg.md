# O79 — one-pass authenticated VZIP selective range from whole-recipe SHA-256

Date: 2026-10-25
Status: PREREGISTERED BEFORE INSTRUMENT OR RESULT

## Authority and separation
Source-exact parent O76/O76b PR #433 at `d654c54da1a0351721318f1d365b45e54ae232d7`, whose historical development Builder/Reader/Codec blobs are `663ef0922992b1fbb8f19e6eea88d55c10a56044`, `e716233403dabd0966863c45635e18fa5ac6afb8`, `29526db4203723d83523fc95d074c346b63d7587`. Shipping v0.30.0/r24, benchmark, release and product source remain untouched. This independent O79 researcher owns only a research oracle and a dedicated CI route, not VZIP product implementation; O76 source/negative are immutable controls. Repo discovery cache is not a claim.

## Baseline / question
O76 measured 265–1064× faster 64B reads from retained mode-0 Deflate than regenerated mode-2, but O76b rejected integrity-tier equivalence because mode-0 direct mmap slices skip the decoded blob CRC. The r24 VZIP recipe already stores the **exact entire original nested ZIP SHA-256**, and retained mode-0 reconstructs its original physical compressed bytes directly. Can a tiny selected read be returned **only after one complete SHA-256 of the logical ZIP's assembled already-compressed representation**, without inflating the large raw member, preserving a materially better timing than mode-2 and refusing corrupted physical record bytes?

## Mechanism and strong controls
Reference: unchanged installed r24 `CMPCT.read_range()` on regenerated mode-2, which validates `_blob` CRC on its raw content. Candidate is RESEARCH-ONLY pure-Python function that streams the physical retained VZIP recipe's skeleton + retained compressed streams in exact logical order into SHA-256, verifies both original logical ZIP size and recipe digest before returning 64B copied from those same observed immutable Python bytes. Reuse exact O76 corpus source generator, identical source ZIP, same Builder/Reader, and same mode/stream selection. Also measure unchanged mode-0 unchecked path as an explicit **weaker-integrity** reference, never an equivalent control. If a member has mode-2, the oracle is permitted to recompress through the original `_stream`; report the cost instead of claiming bounded locality. Compare complete archive bytes and full read/verify/extract on original archives. Reproduce O76b one-byte physical payload changes on independent copies, plus out-of-selected-range and skeleton corruptions; decisive claim requires fail-closed in both modes and never silently wrong data. No fabricated signing, independent external hash, or trusted previous verify.

## Prospective decision and falsifiers
Perform ≥6 fresh Reader calls per arm in alternating ABBA order for repeat2m, periodic8m, mixed2m, random2m, include wall + process CPU, exact selected sha, full stored bytes, logical bytes hashed and decoded/materialized, bounded memory/RSS, single-host scope. Original source and corpus hashes must be recorded. A potential **research headroom** exists only if ≥2 distinct eligible mode0 families have median authenticated range-read wall ≥8× faster than mode-2 regular range and ≤64 KiB additional complete archive bytes; SHA-256 covers the *entire original ZIP*, and targeted/out-of-range physical corruptions are rejected. Otherwise classify correctly as negative/narrowed. A genuine arbitrary modification which causes silently incorrect output, a weakened source bound, a size/identity mismatch, or inability to execute authentic installed-product CI defeats the corresponding scientific claim regardless of timing. Do not assume one all-recipe hash provides streaming sublinear I/O, concurrency mutation immunity, or equal semantics on every other read path. Retained mode0 adds encoded bytes and reads all compressed members for strong auth. Separate ZIP compressed-storage bytes from expanded member size and physical OS disk traffic.

## Better alternatives and implications
Alternative A: authenticate source Blob's expanded raw CRC by full Deflate inflation — safer but likely erases most speed headroom. B: add per-physical-extent SHA/Merkle — smaller selective verification but on-disk revision and reader carrying cost; defer until a no-format solution is tested. C: caller invokes a prior full `verify()` — not valid without immutable file ownership. D: label range weak/unchecked — no equivalent integrity-tier product win. Our oracle is a new *physical proof ownership* frame: reuse already-authoritative whole-logical ZIP SHA to authenticate directly retained compressed bytes while avoiding re-inflation.

## Evidence/release boundaries
Hosted source-exact install under Ubuntu only, no product edits or official benchmark claims. Preregister outcome history immutable; preserve source SHA/CI run/artifacts and unfavorable cases. If result is positive, owner-reviewed product design and hostile filesystem/size/RSS/portable official exact-head gates are still required. Three consecutive same-family activations without decisive evidence should retire/reframe. No claim of general-purpose product domination from this experiment.

**Primary scientific question:** SHA-authenticated retained-stream selective read versus true mode-2 read under authentic r24.

**Next discriminator:** an installed-product adversarial run with a single physical byte flip and full-recipe SHA checked before returning the selected 64B.

**Admission:** scientific decision only; never merge/release on the basis of this document.
