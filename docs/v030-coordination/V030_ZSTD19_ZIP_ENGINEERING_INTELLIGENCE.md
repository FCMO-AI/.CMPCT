# CMPCT v0.30 — Zstd-19 / ZIP Engineering Intelligence

**Purpose:** turn the external competitor red into an engineering map. This is not a benchmark summary. It records *why* CMPCT loses on each remaining workload, which part of CMPCT owns the loss, why ZIP or solid Zstd-19 has the advantage, which hypotheses have already been falsified, and what the next implementation should attack.

**Release law remains unchanged:** every frozen workload must be strictly smaller **and** strictly faster to create than both normal ZIP/Deflate and solid Zstd-19. Ties lose. v0.29 byte no-regression, <=8x selective-read amplification, <=8 MiB decode units, integrity/recovery, native/Android parity and exact-candidate evidence remain mandatory.

## Evidence discipline

This document uses three confidence labels:

- **MEASURED** — established by exact repository evidence/oracles on the frozen workload or by a promoted product result.
- **STRONGLY INDICATED** — component accounting and A/B evidence isolate the cause, but the final shipping selector has not yet reproduced the complete win.
- **HYPOTHESIS** — plausible engineering explanation that still requires a causality oracle before product work.

Do not convert HYPOTHESIS into production policy. Do not use workload names, paths, frozen hashes, pack hashes, or benchmark identity as selector/compression inputs.

---

# 1. Executive diagnosis

CMPCT's remaining losses are **not one problem**.

There are four distinct failure classes:

1. **Canonicalization gap:** CMPCT already has an internal/research representation much smaller than Zstd, but the shipping canonical product cannot yet publish it. Office and analytics are the clearest examples.
2. **Speculative-search tax:** a cheap candidate is already good enough, but v0.30 spends seconds or minutes building losing G0-G4 / PrefixGraph / r25 candidates before publishing the cheap result. Shifted versions, boundary churn, media-like rows and several r24-fallback families suffer this.
3. **Rich-container/control tax:** CMPCT deliberately carries more semantics than tar+Zstd or ordinary ZIP: per-member identities, filesystem metadata, recovery copies, selective-read structure, index/control framing. Tiny-files, developer-tree and encrypted-like expose this overhead strongly.
4. **Reader graph tax:** the selected archive is smaller, but extraction/verification walks a reconstruction graph with caches, records, transforms and hashes rather than one native linear decompression stream. ML/G0-G4 is the dominant case.

The key strategic rule is therefore:

> **Do not try to beat Zstd by globally turning compression effort up. Identify which failure class owns each row, then remove that exact tax.**

---

# 2. Current complete wins — preserve, do not destabilize

These rows have demonstrated shipping complete wins (smaller + faster creation than ZIP and Zstd-19) in the latest completed frontier available to this campaign:

- `logs_and_telemetry`
- `large_mixed_binary`
- `false_neighbors`
- `incompressible` / hostile high-entropy

These are useful architectural exemplars:

## Logs — structural inversion, not brute compression

**Why CMPCT wins:** compressed sidecars are treated as retained originals and loose logs are derived reversibly. This removes duplicated semantic content instead of recompressing it.

**Lesson:** where two files are exact transforms of one another, represent the relation. Do not independently compress both.

## Large mixed binary — terminal cheap winner

**Why CMPCT wins:** locality-safe wide r24 chunks are already smaller/faster than competitors. The previous hundreds-of-seconds r25 search was pure speculative waste.

**Lesson:** when a source-derived structural envelope has proven the cheap representation is the exact winner, terminate before research search.

## False-neighbors / incompressible — bounded medium-binary packing + terminal admission

**Why CMPCT wins:** existing r24 S_PACK grammar amortizes metadata/compression context over medium `.bin` files while remaining locality-safe; a proven high-entropy structural envelope prevents losing r25 search.

**Lesson:** high entropy should trigger *less* research effort, not more.

---

# 3. Workload intelligence map

## A. Office documents — **largest size loss; representation is solved, production policy is not**

**Observed shipping problem**

- Shipping office is roughly 15.4 MiB while solid Zstd-19 is roughly 8.3 MiB.
- Shipping creation has historically spent tens of seconds in the full candidate machinery.
- This single row dominates much of the aggregate Zstd deficit.

**Why Zstd-19 does well** — **MEASURED / structural interpretation**

Office files are themselves ZIP-based containers with repeated XML schemas, filenames, central-directory framing and similar compressed streams. A solid native Zstd stream gets broad cross-file/container context with very little per-file framing and extremely optimized C/native loops.

**Why shipping CMPCT loses** — **MEASURED**

1. The mature canonical product cannot simply publish the historical CMPNX/EntropyGraph research archive, even when that archive is much smaller.
2. Genuine r24 therefore becomes the outer fallback and is far larger than the strongest internal representation.
3. Canonical filesystem semantics, recovery and authenticated control initially added just enough framing to break the strict v0.29 floor even when the inner graph was excellent.
4. C25EG02→EG08 work progressively removed duplicated path/identity/control/container framing. Candidate-level EG08 has crossed the v0.29 byte floor and can be below ZIP and Zstd.
5. The remaining difficulty is **generic pack-effort selection and execution**. A frozen pack-hash schedule can win but is forbidden. Simple identity-free policies either miss the byte floor or send too many packs to high Zstd levels and lose ZIP creation speed.

**Already falsified / deprioritize**

- Globally raising Zstd level.
- One simple monotone `(raw_bytes, level1_ratio)` policy.
- Two-region variants of the same weak feature family.
- Python thread-level parallel verification.
- Verifier tmpfile placement as the dominant remaining office tax.
- Repeated filesystem-control micro-encoding as the main frontier after EG08; that path was squeezed down to tens of bytes and then solved by lower-level compact framing.

**What to attack next**

1. **Generic effort-policy distillation, but optimize makespan, not only bytes.** Use cheap pack statistics only; freeze rule complexity before looking at sealed outcomes.
2. **Single-pass selected pack emission.** Do not level-1-compress a final pack and then recompress it at the selected high level.
3. **Native final-pack compression.** Once Python graph discovery is complete, final independent pack compression should move to bounded native workers; ZIP's advantage is largely low-overhead native execution.
4. **Reduce graph-construction wall-clock as a separate phase.** Current evidence has shown final compression and graph construction are both meaningful contributors. Profile them independently.
5. **Selector admission only after policy generalizes.** Office does not need new compression science; it needs a production-safe way to choose the already-proven representation.

**Success criterion:** actual shipping office archive < v0.29, < ZIP, < Zstd, and verified-create time < ZIP and < Zstd, with no benchmark identity in policy.

---

## B. Analytics / tabular — **structure wins, CPU budget loses**

**Observed shipping problem**

- Shipping is roughly 10.39 MiB vs ~9.34 MiB Zstd-19.
- Historical shipping path has spent very large time in r25 research construction.

**Why Zstd-19 does well** — **MEASURED / structural interpretation**

Analytics data is broad, homogeneous and repetitive. One native solid stream gets excellent long-range context and amortizes framing almost completely.

**Why CMPCT loses** — **MEASURED**

- Federated C25EG candidate at low effort is already ~7.1 MiB and creation can be sub-second, so the representation itself is stronger than Zstd.
- But the immutable v0.29 floor is much smaller than that low-effort candidate. Crossing it requires high effort on many physical packs.
- Selective per-pack effort can cross the v0.29 floor, but measured serial effort is far beyond ZIP's creation budget.
- Exact parallel repack improved the high-effort phase substantially, but still remained multiple times slower than ZIP.

**Root cause:** **too many independently compressed packs need expensive effort**. CMPCT has enough structural compression, but its per-pack compression execution model fragments the CPU work compared with one highly optimized Zstd stream.

**Already falsified / insufficient**

- Serial selective high-level recompression.
- Parallel recompression layered *after* a complete initial level-1 physical build.

**What to attack next**

1. **True single-pass pack compression:** graph/search determines final pack policy first; each final pack is compressed once at its final level.
2. **Native bounded parallel pack compressor:** remove Python scheduling/copy overhead.
3. **Pack-count reduction where locality permits:** fewer, larger independently decodable packs can reduce repeated Zstd frame setup and improve context. Must remain <=8x and <=8 MiB.
4. **Cross-pack reusable dictionary only if exact locality accounting proves benefit.** The generic segmented shared-dictionary experiment was poor overall; do not resurrect it globally. A narrowly trained analytics-specific *structural* admission may still be worth a new oracle if pack-count/single-pass work is insufficient.

**Success criterion:** retain ~7 MiB-class representation, cross v0.29, and fit complete verified creation inside ZIP time.

---

## C. Many tiny files — **metadata/control amortization problem**

**Observed shipping problem**

- Roughly +0.2 MiB versus Zstd-19.
- Thousands of files magnify every per-member byte.

**Why Zstd-19 does well** — **MEASURED / structural interpretation**

Tar/solid-Zstd effectively turns thousands of tiny files into one long stream. Path patterns, metadata-like text and contents share one compression context. Zstd pays very little framing per file.

**Why CMPCT loses** — **STRONGLY INDICATED**

CMPCT intentionally pays for:

- per-member authenticated identity,
- paths,
- sizes and reconstruction recipes,
- recovery-capable control state,
- bounded S_PACK grouping for locality,
- canonical filesystem semantics.

With 5,000 tiny files, a handful of bytes per entry becomes tens or hundreds of KiB.

Evidence from compact-control experiments:

- numeric path deltas help somewhat;
- suffix-table encoding was selected primarily by the tiny-file row, confirming repeated path tails are real overhead;
- S_PACK continuation/run compaction saves control bytes on some rows;
- no individual path trick is large enough alone.

**What to attack next**

1. **Generalize C25CC01-style compact authenticated control to tiny-file trees.** This is the strongest existing mechanism for removing duplicated r24 control while retaining physical payloads and recovery.
2. **Batch per-slice identity representation.** Investigate authenticating a pack once plus a compact authenticated table of slice identities, rather than paying repeated full-width fields per file. Per-member SHA semantics must remain exact.
3. **Path dictionary + prefix/suffix coding as one representation, not isolated micro-oracles.** The important metric is compressed total control plane, not raw path-token bytes.
4. **S_PACK recipe run encoding.** Contiguous slices should inherit pack-id and prior end offset when exact reconstruction proves it.
5. **Avoid r25 research search if compact r24-derived profile already wins.** Tiny-file creation speed will not beat ZIP if the product still builds expensive graph candidates afterward.

---

## D. Developer repository — **solid-context advantage + rich metadata tax**

**Observed shipping problem**

- Roughly +0.1 MiB vs Zstd-19.
- Repair-v6 source identity is deterministic: 1,266 files / 2,624,373 logical bytes.

**Why Zstd-19 does well** — **STRONGLY INDICATED**

Developer trees contain repeated source syntax, identifiers, paths, generated text and neighboring versions of small files. Solid Zstd obtains broad context with almost no per-file framing.

**Why CMPCT likely loses** — **PARTLY MEASURED, partly HYPOTHESIS**

- Many small entries incur the same control/index/recovery tax as tiny-files.
- Embedded executable/binary material is comparatively incompressible and can make trained dictionaries or sophisticated transforms dead weight.
- Locality-bounded packing prevents using arbitrarily large solid context.
- The full product may still pay candidate-search work that does not improve the final bytes.

**Required next causality work before product changes**

Build a developer-specific *decomposition oracle* that reports, in bytes and CPU:

- primary/tail control bytes,
- path bytes after compression,
- per-file hash/recipe bytes,
- physical record headers,
- dictionary payload + whether any selected record uses it,
- S_PACK payload vs direct payload,
- r24 build time vs r25/G0-G4/PrefixGraph time,
- final selected profile.

Do not guess which of these dominates. The encrypted-like campaign showed that decomposition can overturn an intuitive explanation.

**Likely implementation if control dominates:** compact-control + path/recipe amortization.

**Likely implementation if search dominates:** structural terminal r24/compact-control admission.

---

## E. Encrypted-like — **compression solved; shipping integration is the blocker**

**Observed shipping state**

In the external-normalized domain, shipping r24 was only about 7 KiB larger than Zstd and was already faster than ZIP. Full product time was much worse because it still constructed losing r25 work.

**Measured decomposition**

- 58 physical records.
- all final records RAW.
- only ~3.7 KiB physical record headers.
- no useful codec metadata.
- no case where selected compressed payload was larger than raw.
- a trained dictionary could exist even when no selected physical record used `CODEC_ZSTDDICT`; post-selection dead-dictionary elision recovered ~24 KiB class savings.
- numeric path / suffix path / S_PACK continuation tweaks were too small to explain the whole deficit.

**Why Zstd had the advantage** — **MEASURED**

The data itself is mostly incompressible. Zstd's advantage came from *lower container/control overhead*, not better compression of payload bytes.

**CMPCT solution already demonstrated** — **MEASURED candidate-level win**

C25CC01 compact control keeps the r24 physical payload unchanged and replaces duplicated verbose control with two compact authenticated recovery copies. Candidate evidence is ~10.196 MiB-class and both smaller and faster than Zstd and ZIP.

**What remains**

- native production dispatch correctness,
- Android/JNI parity,
- benchmark-name-free structural admission,
- then actual shipping selector + 15-workload matrix.

**Do not spend more research cycles on encrypted payload compression.** This row is a productization task now.

---

## F. Shifted versions — **few KiB size gap, enormous losing-search tax**

**Observed state**

- only several KiB larger than Zstd.
- PrefixGraph is the genuine final winner.
- extraction is already around/faster than v0.29 in current runtime evidence.
- creation remains expensive.

**Why Zstd size is competitive** — **STRONGLY INDICATED**

The remaining gap is small enough that fixed PrefixGraph framing/reference metadata likely dominates rather than missing large-scale redundancy.

**Why CMPCT speed loses** — **MEASURED**

- PrefixGraph anchor auditions were independent and historically serial; bounded parallel anchor scheduling has been promoted with exact-byte identity and material speedup.
- Even after PrefixGraph finds a strong result, the exact tournament can spend ~minute-scale time waiting for losing G0-G4 work.
- Simple candidate-derived early-terminal rules were tested across all 15 and produced counterexamples. Therefore heuristic cancellation is unsafe.

**What to attack next**

1. **Exact lower-bound / upper-bound pruning for G0-G4.** Need a mathematical proof that unfinished G0-G4 cannot beat the current PrefixGraph complete-byte floor.
2. **Compact PrefixGraph control/framing by the remaining few KiB.** Measure exact metadata/header/recovery contribution first.
3. **Attempt-5 construction bound:** determine whether a cheap partial statistic can prove its best possible completed archive is already above PrefixGraph.

**Do not:** reintroduce heuristic terminalization. It has explicit counterexamples.

---

## G. Boundary churn — **same architecture as shifted versions**

**Observed state**

- only a few KiB above Zstd.
- PrefixGraph is the real winner.
- large creation time is dominated by waiting for losing G0-G4.

**Root cause:** identical class to shifted versions: **small framing deficit + exact-tournament search waste**.

**Action:** share the same bound/pruning campaign. A successful proof should generalize to both rows and unseen related families.

---

## H. Deflate-family — **repeated ZIP framing is the size opportunity; canonical milliseconds are the speed problem**

**Corpus shape**

14 deterministic ZIP bundles with related Deflate members.

**Why Zstd-19 does well** — **MEASURED / structural interpretation**

Solid Zstd sees repeated ZIP local-header, central-directory and member-layout structure across the bundle family and compresses that repetition in one native stream.

**Why mature r24 loses** — **MEASURED**

- Historical nested-container packing placed all 14 ZIPs into one decoded pack, causing ~14x selected-read amplification.
- Locality-safe repartitioning reduced this to ~7x but split compression context and added bytes.
- Exhaustively testing all 1,716 legal 7+7 partitions recovered only hundreds of bytes: partition choice cannot solve the gap.

**Experiments that bracket the solution**

- raw DEFLATE segmentation: **fast enough** (few ms), **too large** (~19 KiB).
- XOR compressed-stream delta: worse.
- full preflate/reinflate normalization: **small enough**, **far too slow**.
- reversible ZIP framing factorization: **small enough and inherently fast** because it never inflates inner DEFLATE streams.

C25Z3/binary-control candidates have reached ~14.0 KiB, below Zstd's ~14.25 KiB, but complete canonical verified creation has remained a few milliseconds slower than ZIP.

**Already falsified**

- Python-thread parallel builder as the solution.
- parallel verification.
- streaming SHA verifier micro-optimization.
- simply changing Zstd level.

**Root cause now:** **fixed Python/canonical construction + verification overhead is too large relative to a ~3–5 ms ZIP baseline.** Compression science is no longer the main problem.

**What to attack next**

1. Native C25Z3 builder/parser for the tiny fixed-control path.
2. Fuse source parse + control construction + integrity accumulation so bytes are read/hashed once.
3. Avoid building generic canonical filesystem machinery when the bounded ZIP-factor profile already owns all required facts; preserve equivalent authenticated semantics, not duplicate work.
4. Benchmark process startup/allocation/path I/O separately; millisecond-scale rows cannot tolerate Python object churn.

---

## I. ML artifacts — **size wins, reader architecture loses badly**

**Observed state** — **MEASURED**

ML/G0-G4 saves roughly 160 KiB versus v0.29 and is a Zstd size win, but recent authority has shown roughly:

- ~1.4x creation vs v0.29,
- >2x verification,
- ~2.5–2.8x extraction.

**Why ZIP/Zstd extraction is fast**

Their full extraction path is essentially linear native decompression + sequential writes. There is little graph traversal or dependency resolution.

**Why CMPCT extraction is slow** — **STRONGLY INDICATED, active A/Bs**

G0-G4 extraction may require:

- loading/authenticating physical records,
- reconstructing logical nodes,
- applying delta/mosaic/transforms,
- following node dependencies,
- hashing reconstructed output,
- interacting with a 32 MiB node LRU and 64 MiB record LRU.

A large graph with many one-shot derived nodes/records can pollute the LRUs and evict heavily reused bases. Primary/tail metadata can also duplicate parse/hash work.

**Active exact-byte-neutral experiments**

- cache only nodes proven by authenticated graph references to be reused;
- avoid caching physical records proven one-shot;
- reuse already-validated metadata copy when the second authenticated copy is physically identical, with corruption fallback proving recovery still works.

**What to do with results**

- Promote only mechanisms that materially reduce both verify/extract and do not increase physical reads or cache limits.
- If cache-policy gains are insufficient, move G0-G4 node/record decode into native code. At ~2.7x, Python graph execution itself is a likely remaining tax.
- Fuse reconstruction + output hash + publication where possible so verification does not require a second logical traversal.

**Do not trade the size win away.** This is a decode-engine problem.

---

## J. Media — **size is good; speculative construction likely owns speed**

**Observed state**

Media is already a Zstd size win but has not consistently been a complete speed+size win. Historical external diagnostics showed r25 construction can consume orders of magnitude more time than the cheap mature path.

**Likely cause** — **STRONGLY INDICATED**

Media compressors already remove much of their own redundancy. CMPCT's useful representation is often cheap packing/container handling, while expensive graph research candidates have little chance to pay back their construction cost.

**Required next step**

Add a media-specific *causality oracle*, not a heuristic selector:

- r24 build bytes/time,
- r25/G0-G4/PrefixGraph bytes/time,
- final winner,
- exact delta from every losing branch.

If r24 or another cheap profile wins repeatedly under a structural envelope, build an adversarial terminal-parity proof analogous to large-mixed/medium-binary. Do not special-case media filenames/extensions unless the rule generalizes.

---

## K. Incremental backups — **size win; avoid dead CPU**

**Observed evidence**

- Already a Zstd size win.
- Dead-dictionary elision removes ~24 KiB-class pure payload overhead on this family.
- A no-dictionary-training A/B showed some byte-identical CPU opportunities on frozen data, but the generic skip rule failed adversarial generalization. Therefore early skip is not production-safe.

**Why speed can still lose**

Dictionary training or research candidate work may be performed even when the final selected archive does not benefit.

**What to attack next**

- **Overlap**, rather than skip, dictionary training with independent mandatory work when possible. Exact bytes remain unchanged and no prediction is needed.
- Lazy/abortable training is only acceptable if a mathematical condition proves no selected codec can still require the dictionary; current heuristic skip evidence is insufficient.
- Measure whether final release path still constructs losing r25 candidates after an already-good r24 result.

---

# 4. Cross-cutting reasons ZIP/Zstd are beating us

## Zstd-19 advantage 1: native, single-stream execution

Zstd's hot loop is highly optimized native code. On homogeneous or broadly redundant corpora it gets one large context, few allocations, few framing decisions and almost no Python-level orchestration.

**CMPCT response:** move final-pack compression/decompression and graph hot loops native where profiling proves Python orchestration is material. Do not move research policy into native prematurely; move the deterministic hot path.

## Zstd-19 advantage 2: almost no rich archive semantics in the comparator

The solid comparator primarily pays tar-like framing + one Zstd stream. CMPCT additionally provides indexing, random access, per-member integrity, recovery, filesystem semantics and bounded locality.

**CMPCT response:** remove *duplicated* ownership, not semantics. C25CC01 and EG08 are the model: one semantic fact should have one authenticated owner, with compact references elsewhere.

## ZIP advantage: extremely cheap creation

Deflate-9 often compresses worse, but its creation path is brutally simple and native. On tiny or already-compressed inputs, fixed Python/candidate-selection costs dominate.

**CMPCT response:** terminal cheap winners, native tiny-profile builders, and exact pruning. A 3 ms ZIP workload cannot tolerate a 2 ms generic verification wrapper plus candidate tournament.

## CMPCT self-inflicted tax: exact portfolio without early impossibility proofs

Building multiple complete candidates guarantees compression quality but can be catastrophically slow when one branch is obviously bad only *after* completion.

**CMPCT response:** develop **mathematical candidate bounds**. The next generation of speed work should prove `best_possible_remaining_bytes >= current_complete_winner_bytes` and terminate safely. Heuristic confidence is not enough.

---

# 5. Priority queue for hourly agents

This is the recommended order based on expected release leverage, not implementation convenience.

## P0 — Finish already-solved candidate promotions

1. **Encrypted-like / C25CC01:** native dispatch -> Android -> selector admission -> genuine external matrix. Stop compression research on this row unless productization changes its measured bytes.
2. **Office / EG08:** solve generic effort execution/policy. Representation bytes are already strong enough.

## P1 — Remove catastrophic runtime taxes

3. **ML/G0-G4 extraction:** finish node-cache, record-cache, metadata-copy A/Bs; promote exact-byte-neutral winners; if insufficient, build native decode prototype.
4. **Shifted + boundary:** exact G0-G4 impossibility bound after PrefixGraph winner; do not use heuristic cancellation.
5. **Analytics:** single-pass native selected-pack compression; no double level1+repack.

## P2 — Close small size gaps

6. **Deflate-family:** native/fused ZIP-factor creation path; compression ratio already solved.
7. **Tiny-files:** compact-control generalization + batched path/recipe/identity representation.
8. **Developer repo:** first build a full byte/CPU decomposition; do not choose a fix before knowing whether control, payload or search dominates.

## P3 — Preserve existing size wins while fixing speed

9. Media terminal-parity investigation.
10. Incremental-backup dead-work overlap/elimination.

---

# 6. Required evidence format for future optimization work

Every new optimization oracle should emit, where applicable:

- source logical bytes and frozen source identity;
- current shipping archive bytes;
- candidate archive bytes;
- ZIP bytes + create time;
- Zstd-19 bytes + create time;
- v0.29 bytes;
- r24 bytes/time;
- r25 total bytes/time;
- G0-G4 bytes/time;
- PrefixGraph bytes/time;
- final winner;
- search/construction/verification/publication time decomposition;
- control bytes, metadata bytes, physical-record framing bytes, dictionary bytes;
- number and total bytes of physical packs;
- codec distribution;
- max member-read amplification;
- max decode unit;
- verify time and extract time;
- physical record reads / logical node materializations for graph readers;
- exact reason a rejected candidate cannot publish.

This should become the standard artifact shape. A red row without this decomposition is insufficient engineering evidence for the next optimization decision.

---

# 7. Stop-doing list — falsified paths

Agents should not spend new hourly runs repeating these without materially new evidence:

- heuristic PrefixGraph early cancellation after a strong candidate — counterexamples exist;
- generic shared-dictionary segmented solid format — 0/15 complete wins in prior evidence;
- unrestricted whole-stream solid results as product evidence — locality destroys many apparent wins;
- deflate-family 7+7 partition search — exhaustive optimum still misses Zstd;
- deflate-family raw-DEFLATE XOR — worse;
- deflate-family Python thread parallel verification/build as primary fix — slower or insufficient;
- office global Zstd level tuning — cannot satisfy byte+CPU contract;
- office simple one/two-region effort policy families — insufficient or too slow;
- encrypted-like numeric path, suffix table, or S_PACK continuation as the main missing mechanism — measured too small;
- early dictionary-training skip based only on the frozen suite — adversarial generalization eliminated the surviving rules;
- increasing ML cache budgets — current campaign requires same-memory improvements first.

---

# 8. Definition of victory

Do not report a workload as solved merely because a research candidate beats Zstd.

A workload is solved only when the **actual promoted product path** on one exact fingerprint:

1. emits fewer bytes than v0.29 (where required by the no-regression law), ZIP, and Zstd-19;
2. completes the frozen verified creation boundary faster than ZIP and Zstd-19;
3. preserves <=8x locality and <=8 MiB decode units;
4. strongly verifies and recovers correctly;
5. has Python/native/Android semantic parity where the profile requires it;
6. is selected by a benchmark-name-free/content-identity-free production rule;
7. survives the full 15-workload zero-counterexample matrix.

The strategic objective is not to make CMPCT's research engine more elaborate. It is to make the **shipping decision path cheaper, more compact and more structurally intelligent than the single-stream competitors while retaining the features they do not provide.**
