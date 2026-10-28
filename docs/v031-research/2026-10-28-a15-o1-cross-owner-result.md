# A15-O1/O1b — Cross-member physical ownership: scientific result and promotion boundary

Date: 2026-10-28 UTC.
Status: **O1 ownership-byte falsifier and O1b same-process cost court DECIDED at exact branch HEAD; product promotion not warranted**.
Classification: Foundry oracle, **no product, released-format, version, benchmark, shared Discovery state or policy changes**.

## Problem / inherited baseline

A15-O0 PR #677 proved that a small typed inversion vocabulary can represent member-local reversible transforms with 0–3 B extra per 32-member cohort, but no decrease in real Reader source complexity and no physical owner-reference semantics. Source-locked O0 result `40694211153` was Ubuntu scientific evidence only. The actual released CMPCT r24 Reader supports richer storage relationships, including shared owners/chunks and Virtual ZIP. The risk was mistaking the low serialization cost of a toy language for a universal decoder substrate.

A15-O1 asks whether the **specific independent-frame O0 grammar**, not some future grammar extended with references, can preserve cross-member physical reuse economically. It compares the O0 direct fallback with a stronger simple dedicated chunk-reference control, both with the same member-selective full decode semantics and no free owner bytes.

## Hypothesis and preregistration

The first child commit `b28bcdf86d9ef90c0b706f827aa77a49960fc590` froze the 32-member × 16-chunk × 4 KiB method and three regimes (identical, 12 common + 4 unique, all distinct) over independent seeds 20261028/20261029. The member-local A15-O0 direct-typed envelope contains one independent Zstd-19 frame, source length and SHA-256 per member. The CHUNKREF control contains one Zstd-19 frame per SHA-unique physical owner, a fully charged 36-B owner descriptor (length + SHA-256), 32 charged member records and their 16 reference indices. Every selected member's exact content SHA is validated. The prediction was REF <=70% of A15 in the two shared regimes and no >=5% REF win in the distinct regime.

The separate O1b preregistration `a3c2f8741584e80f7e0be9fd6c5381a842c17816` asks whether REF's per-member CPU/wall disadvantage persists when **both** representations use identical libzstd in one process, no CLI process launch, with ABBA sampling. This is distinct from the stored-byte question and does not amend its thresholds.

## Evidence / original first hosted court

Initial PR-event Github Actions scientific court [#40702873448](https://github.com/FCMO-AI/.CMPCT/actions/runs/40702873448) and sibling [#40702800244](https://github.com/FCMO-AI/.CMPCT/actions/runs/40702800244) both **SUCCESS**, with 192/192 actual source members exact, 42/42 constructed hostile envelopes rejected and 6/6 forged receipts rejected by a separately implemented source-independent Zstd CLI referee. Original raw artifact #12822815801 has SHA-256 `201788c81ed856d1959708ad770b1887623db743791b1673a21c0c7bff0823ec`, 22 entries, ZIP CRC PASS. A third independently written libzstd/ctypes parser redecoded both original archive structures and all 192 source members, matching per-case hashes, identities, owner counts and exact full stored sizes.

**Important provenance limitation discovered during external audit:** the original PR-event `actions/checkout@v4` default checked out synthetic PR merge commit `19f5c311a425bf0c2123b82e9d2719fecc8ab387`; the Actions run metadata's `head_sha=4c87d0f1...` by itself did NOT prove code executed at that exact branch HEAD. The data above are valid **PR-merge-source scientific evidence**, not source-exact branch HEAD credit. The workflow was repaired in a later commit to check out `github.event.pull_request.head.sha || github.sha` explicitly and compare `git rev-parse HEAD` before running. Require a new exact-branch-head court before calling any later HEAD tested.

### Full charged bytes, per 32 × 64 KiB group

| Regime (two deterministic seeds, same results) | Unique 4 KiB owners | O0 direct typed B | CHUNKREF B | REF/direct | Decision |
|---|---:|---:|---:|---:|---|
| Identical members | 16 | 2,098,924 | 68,572 | 0.032670 | Shared-owner wins 96.733% |
| Twelve common + four unique chunks/member | 140 | 2,098,924 | 582,552 | 0.277548 | Shared-owner wins 72.245% |
| All unrelated chunks | 512 | 2,098,924 | 2,124,492 | 1.012181 | Direct typed wins 1.218% |

The identical results across both seeds follow from an exact high-entropy uncompressible frame size (64 KiB frame = 65,549 B; 4 KiB frame = 4,109 B) and the fully charged fixed descriptors, not statistical tuning. The full-byte formula independently reproduces every observed value:

```
A15 O0 direct = 9 + 3 + 32*(42 + 65549) = 2098924 B
CHUNKREF = 12 + 32*(38 + 16*2) + U*(36 + 4109) = 2252 + 4145*U B
```

This is the main scoped negative: **O0's original independent member frames cannot express cross-member owner reuse without storing/recompressing those bytes for each member.** An added authenticated REF instruction might extend A15; this experiment does not disprove a future representation with that richer information model.

## Repaired exact-source O1/O1b hosted evidence (same 2026-10-28 UTC)

Workflow was corrected to check out and assert the actual PR HEAD. Two **SUCCESS** three-stage O1/O1b courts on unchanged experimental source `23a6498c270c5168c9b25945277130f53870efab`:

- [Actions #40703899812](https://github.com/FCMO-AI/.CMPCT/actions/runs/40703899812) — 192/192 exact byte reconstructions, 42/42 hostile cases rejected, 6/6 O1 forged receipts rejected; O1b **864 raw ABBA timing observations**, independent auditor PASS and 6/6 further forged receipts rejected.
- [Actions #40703914232](https://github.com/FCMO-AI/.CMPCT/actions/runs/40703914232) — independently repeated and **SUCCESS** at identical branch source; same O1 byte/hostile/referee outcomes and O1b raw count/referee outcomes. This **repairs the original synthetic-merge source-custody limitation** for the code/guarded workflow as at that exact branch SHA. Documentation-only later HEAD must still get its own checks.

Original exact-source raw artifact from #40703914232: GitHub artifact **#12822588405**, downloaded 30,750,865-byte ZIP SHA-256 **`3fc34caab537ecceb7b996a817d8c796f77e9d1df6ad5e3787489bce57e22f60`**, 24 files, ZIP CRC PASS. An additional independent local audit of `result.json` and `inprocess.json` recomputed source linkage, all six case identities and raw median wall/CPU values from **864 observations**, without importing either producer. `head.txt` inside the artifact confirms actual checked-out SHA `23a6498c270c5168c9b25945277130f53870efab`. This validates the stated source-exact result for that SHA, not automatically any later documentation HEAD.

The O1b wall ratios are REF/full-member-A15, same archived bytes and source, in-process system libzstd and identical SHA validation. Higher means CHUNKREF's 16 small frames are slower for full-member decoding:

| Regime | Seed 20261028, repeat #40703899812 | Seed 20261029, repeat #40703899812 | Seed 20261028, repeat #40703914232 | Seed 20261029, repeat #40703914232 |
|---|---:|---:|---:|---:|
| All identical | 2.829× | 2.915× | 2.980× | 2.962× |
| Twelve common, four unique | 2.843× | 2.844× | 2.820× | 2.926× |
| All distinct | 2.869× | 2.864× | 2.911× | 2.759× |

CPU ratios likewise pass the prospective ≥1.5× criterion, ranging **2.776–2.981×** across the corresponding cells. O1b therefore confirms a structural *product tradeoff* at the in-process decoder-component tier: CHUNKREF can save 72–97% of complete research envelope bytes where owners repeat, but 16 guarded frames and Python-loop calls cost about 2.76–2.98× for full-member read. Source-authenticated reuse of decoded physical owners could change this, but its immutable lifetime, RAM, and amortization have **not** been established.

Limit: the experiment's "strong same decoder" comparison is within one Python process using libzstd via ctypes in both arms; it does not measure installed CMPCT Reader, heterogeneous real files, cold/open, complete CPU/RSS, range-selective work, updates, or native portability. No product score or universal reader advantage is claimed. The O1/O1b runtime cases are currently Ubuntu hosted only.

## Losses, alternatives, and performance debt

The CHUNKREF reference table necessarily pays 16 physical frame decodes for a complete 64 KiB member, versus one 64 KiB frame for A15. The original oracle's per-member latency included multiple Zstd **child process launches** and cannot provide product-relevant CPU or same-process decoder comparison. In an explicitly exploratory local pre-O1b check, same-process ctypes/libzstd over one member (300 alternating samples/arm) observed 17,676 ns direct versus 165,089 ns per-chunk median, 9.34×; this is **NOT** source-exact hosted O1b proof, nor complete product Reader time.

O1b's new same-archive one-process ABBA court and independent raw referee completed successfully in two exact-source hosted executions; see table above. Neither architecture globally dominates; REF buys bytes and potential physical reuse/locality but exports per-frame work/proof. Direct wins on unique owners and may win on member-decode throughput. Memcached/cross-query reuse would require immutable source custody, independent invalidation rules, and charged memory; neither study grants it.

No full CMPCT Builder/Reader, actual r24 byte comparison, source/maintenance complexity reduction, user data, realistic generic corpus, peak RSS, streaming, source mutation, selective authenticated ranges, platform interoperability, recovery, cold opening, or release-level performance was measured. Program selection is deliberately only the direct fallback, not the full O0 transform search. The experiment establishes a **representation-capacity boundary**, not a new compression mechanism.

## Safety, integrity, and portability

The two small scientific envelopes use bounded counts, exact original lengths, per-member SHA-256; the dedicated REF format adds per-owner SHA-256 and rejects invalid owner indices. The independent referee does not import the experimental producer and checks actual bytes. It checks six deliberate falsifications of result metadata; producer rejects seven different envelope mutations per case. No changes to CMPCT product source, native code, format revision 24, emitted canonical bytes, frozen comparators, version, release lock or discovery policy.

The scientific workflows were Ubuntu-only; remaining OS portability is untested. The workflow's provenance flaw is an **evidence custody issue**, not a demonstrated byte-decoding bug.

## Alternative hypotheses and decision

- A simple enum/owner-reference switch already expresses this control. Extending A15 with REF does not automatically reduce total Reader code or security complexity.
- A whole-member Zstd frame maximizes member-local simplicity and can beat CHUNKREF on distinct chunks.
- A sealed shared-owner table may preserve dedup with read amortization, but safety and source lifecycle must be proven and priced; no free cache.
- Real CMPCT storage variants also require multi-member graphs, physical layout, selective range semantics and transactional integrity beyond either research envelope.

**Decision from original court:** CHUNKREF is a Pareto byte winner under high cross-member reuse and loses under unrelated chunks. O0's restricted grammar is narrowed to member-local inverse transforms; A15's broader research hypothesis remains open but requires a bounded authenticated REF and a true simpler enum control before further investment. Do not promote the restricted IR as universal based on O0's positive toy cost.

## Concurrency, discovery, counterfactual, and next executable action

No narrow ownership collision was discovered with #653 (VZIP), #662/#676 (native S_CHUNKS), or #574 (Discovery state). All work is isolated to this child of #677; Discovery `STATE.json` was not edited. The counterfactual discriminator is the full-charged byte equation above: it would have predicted all three outcomes much earlier; the executed independent court was valuable for confirming exact inverse and hostile bounds. No evidence-backed reason to alter the existing Discovery Engine BONK filters or frozen evaluators.

**Next:** maintain the scoped rejection of O0 as a universal Reader and decide whether to retire this member-only IR as a Reader simplification route or invest one bounded O2 court in authenticated REF + two *actual* r24 storage contracts against the simpler direct enum. If no deletion/subsumption of reader work is demonstrable, park the family. No release, merge, product or version authority is requested.

disproof: invented same-source equivalence, false SHA, accepted malformed refs, omitted carrying bytes, a weakened comparator, or a claim that process-instrument latency measures CMPCT Reader performance.
quality-ratchet: published v0.30.0 / r24 unchanged; all gains/losses research-only.
