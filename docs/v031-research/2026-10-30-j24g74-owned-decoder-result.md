# J24G74 — physically hosted owned decoder replay court

Date: **2026-10-30 UTC**. Outcome: **`OWNED_REPLAY_RESEARCH_SEED`** (not shipping, not promotable, release credit **0**).

## Authority, source and immutable prediction
- Released CMPCT still `main@80c358f8824ec1b20d349c92ed94c898090969b0` = v0.30.0, on-disk revision 24.
- Child [#820](https://github.com/FCMO-AI/.CMPCT/pull/820), based on [#818](https://github.com/FCMO-AI/.CMPCT/pull/818) `2bd44b03a37360b4c59af3bb6445553b2435ffff` (experimental Reader-open transfer), itself inheriting #808. The original signed Reader blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`, #808 factor oracle blob `7657a41d11f2b3c8136c0b69cfe62401f9b19ccb` and #818 physical experiment blob `9b2fa7c2d625cce84597212673c35fba29dcafd5` are unchanged.
- Preregistration at **`59c74a86cb87b715da91bd8207c7ce2282256766` before code**; original measured source/workflow HEAD **`43bd660655663f6fb2205d547dd182c775711480`**.
- Complete original hosted [GitHub Actions #41032961573](https://github.com/FCMO-AI/.CMPCT/actions/runs/41032961573): **SUCCESS Ubuntu 24.04/macOS 14/Windows 2022**. Original raw reports + physical archives retained. This does not imply General Tests or promotion are green.

## Primary scientific result
Question: Can the fresh msgpack checkpoint and generation payloads, which are owned only inside experimental Reader `_index_from_footer`, transfer into factored replay rather than be deep-copied, without changing signed bytes, grammar, fallback or reconstructed data?

**Yes, in the measured research-only ownership boundary.** The prespecified >=1.10x incremental Reader-open criterion over #818's copy-preserving factored route was met on all three operating systems, with lower Python-traced peak on all three and no semantic/recovery failure in the tested cases.

All below are **medians of complete warm-process Reader-open** in milliseconds on *exactly the same physical file per variant per host*. Each case has 4 blocks × 6 balanced ABC permutations × 3 variants = 72 observations/host/case; 432 direct observations total across both cases and three hosts.

| OS | Family | Original Reader (ms) | #818 copy-preserving factored (ms) | Owned fresh-decoder (ms) | Marginal factored / owned | Median traced peak reduction |
|---|---|---:|---:|---:|---:|---:|
| Ubuntu 24.04 | 63 DELETE, 2,048 live | 28.898941 | 8.411284 | **2.480983** | **3.3903×** | **1,098,584 B** |
| macOS 14 | 63 DELETE, 2,048 live | 69.835375 | 18.971291 | **4.775209** | **3.9729×** | **1,098,368 B** |
| Windows 2022 | 63 DELETE, 2,048 live | 52.262050 | 14.092300 | **4.272300** | **3.2985×** | **1,098,584 B** |
| Ubuntu 24.04 | MIXED 21/21/21, 118 live | 1.924719 | 1.092566 | **0.536999** | **2.0346×** | 89,408 B |
| macOS 14 | MIXED 21/21/21, 118 live | 3.163417 | 1.763292 | **0.802812** | **2.1964×** | 89,408 B |
| Windows 2022 | MIXED 21/21/21, 118 live | 3.129650 | 1.880250 | **1.024200** | **1.8358×** | 88,352 B |

The **incremental benefit is versus an already experimental Reader**, not an additional released-product speedup. macOS cross-run timings differ materially from earlier #818; same-run three-way controls are the valid comparison. CPU measurements are retained raw; no precision claim for Windows short-case CPU ticks.

## Exact physical evidence and independent review
- Each host produced two real revision-24 Builder/public-Writer archives: 2,111 original members then 63 independent deletes, and 128 original then 21 rename/21 delete/21 put generations. Exactly 64 SHA-authenticated physical footers per archive. Archive bytes are constant across Reader A/B/C within a host; different OS metadata yields different physical archives.
- All final member bytes, complete `verify()`, MessagePack index byte identity, signed preflight, retained archived member recovery on corrupt/truncated footer and strict POSIX signed-xattr extraction (Linux/macOS only) passed. Windows native xattrs remain **unmeasured**.
- The inherited independent **no-CMPCT** Zstd/MessagePack/footer/SHA physical parser executed on each hosted evidence package and reported `PASS`, including physical SHA corruption rejection, exact final path-keyed xattrs, and index digest reconstruction. It uses no CMPCT Reader and was not modified by J24G74.
- Original packages (downloaded back for second-party audit): [Ubuntu artifact #12966866778](https://github.com/FCMO-AI/.CMPCT/actions/runs/41032961573/artifacts/12966866778) SHA-256 `ad977ac4b63eada63b18686e203b743799eca9f5043625bea22faedc05f5ef4c`; [macOS #12966996504](https://github.com/FCMO-AI/.CMPCT/actions/runs/41032961573/artifacts/12966996504) SHA-256 `b2ed9969a57bd7d70f0a44df138612407cb3929e786b35ab018920d56695db78`; [Windows #12967151052](https://github.com/FCMO-AI/.CMPCT/actions/runs/41032961573/artifacts/12967151052) SHA-256 `0c97f450cac4fae763ff66db401714191bc8a6fabc0b8761c443b651356e8735`.
- Offline independent analysis of the **original downloaded ZIP bytes** confirmed provider digests, per-host physical file digests and sizes, independent no-CMPCT index digests, 72-record balanced coverage per family, all source HEAD identities, raw median recomputation, recorded ratios, tracked-peak deltas, and three RSS samples per variant. Six distinct hostile receipt modifications per platform (fabricated median, missing observation, corrupted order, wrong source head, fake Python memory peak, wrong physical member count) were rejected: **18/18**. This second audit does not imply cryptographic signatures of origin beyond GitHub-hosted artifacts and checked hashes.

## Main negative and exported-cost honesty
- **The optimized helper is intentionally NOT safe for retained mutable caller input.** It mutates the fresh `base` and its rows; the named adversarial `retained_caller_alias_hazard` test confirms the mutation. Shipping would require proof that decoding has uniquely owned, non-exposed objects and no paths retain aliases. Merely deleting `deepcopy` from a public helper is rejected.
- Original 500 deterministic differential *cases repeated on three hosts* admitted the owned route for **214** cases, and fell back for the rest; these are not 1,500 independent structural cases. Error/fallback/index/MessagePack parity survived the test family but is not a universal proof.
- DELETE fresh-process peak RSS median: Ubuntu 36.914 MiB for both routes (no detectable change); macOS 29.484 to 28.297 MiB; Windows 28.039 to 26.457 MiB. RSS is highly confounded by imports, allocator and OS; **do not claim RSS dominance from these probes**. The traced peak reduction is stronger mechanism evidence, not total process memory proof.
- No extra stored bytes because this is read-only. No measured improvement to create/extract cold disk, checksum full verification throughput, native Rust, mutable public-reference lifetime, hardlink privilege, resource ceilings on large indices or official full product gate.
- Published v0.30.0 Reader is **unaltered**; no product source, byte format, release threshold or evaluator weakened.

## PARETOBONK decision and next owner-controlled discriminator
**Decision changed:** #818's dominant incremental memory cost is at least partly eliminable by transferring decoder ownership instead of copying it, in the strictly private Reader-open experimental boundary. Preserve the #808 single general architecture; do not add #811's separate DELETE-only path for these results. This removes a measured ~1.1 MiB traced allocation *without sacrificing the observed replay gain*.

**Next cheapest decisive test:** prove or falsify no lingering aliases across public Reader descriptors, reference mutation and native/Python ownership; use held-out 8,192/32,768-member indices and hardlink/xattr/privileged metadata with fresh-process peak RSS and hostile tail recovery. Then integrate under #795/#808 only if strict resource/recovery invariants and exact-head general/performance gates hold. Strong baseline is always allowed to win.

No concurrency collision observed on J24G74's isolated experiment paths; #795 owns product replay, #808 owns general oracle, #818 owns previous full Reader experiment, #574 owns Discovery STATE. No Discovery policy change earned; `STATE.json` unchanged. Product credit **0**, research evidence only.
