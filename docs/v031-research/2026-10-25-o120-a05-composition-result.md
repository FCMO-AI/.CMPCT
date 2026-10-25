# O120 — A05 two-stage reversible-program oracle: positive bounded headroom, no product promotion

Date: 2026-10-25  
Status: **DECISIVE RESEARCH-LEVEL POSITIVE within frozen small byte-geometry grammar; NOT a CMPCT product win.**

## Authority and provenance

- Canonical parent: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; released v0.30.0/r24 untouched.
- Immutable preregistered prediction commit: `e0865e4d1a2211d7de994e0b976c34dda0a3efb5`; prereg blob `69baaf976c269548050022c48fb75c49763e618f`.
- Measured research source blob: `058f14e8b50e6de764b4ecab877abd6e44add6fd`.
- Result-bearing PR head: `bf8e16491e09a881cb91198260595a21e2adb2f3`; hosted PR merge checkout `665b9ccceb345e1bf3a64e17999bf3e2f091fc9e` (same code/prereg source blobs).
- [Actual independent GitHub Actions run 40235537602](https://github.com/FCMO-AI/.CMPCT/actions/runs/40235537602): **SUCCESS**; Ubuntu 24.04.5, Python 3.12.3, Zstd CLI 1.5.7; source-prereg exact blob assertions and independent summary arithmetic auditor passed.
- [Raw JSON, stdout, instrument, prediction, provenance artifact 12614558643](https://github.com/FCMO-AI/.CMPCT/actions/runs/40235537602/artifacts/12614558643), ZIP SHA-256 `1c0ce4e72c7ffc1622fe6759b4526bef91ec07145802f22c870da1f8d6dec422`, internal JSON SHA-256 `5ba04bda993a532859b9a8801bff6e0c12626da3bfffef3de2a0bebea93867d3`. Artifacts have finite retention; this record and source preserve the durable research decision.

## Primary question and decisive evidence

Frozen A05 question: does exhaustive composition of two reversible byte operations compress materially better than the *best* 0/1-operation alternative, after charging all decoder-visible descriptors, original length and SHA-256, and complete Zstd-19 frame? The program search examined S(w) byte shuffle with w=2/4/8/16, D(s) modulo-256 original-lag differences and X(s) original-lag XOR with s=1/2/4/8/16, at depths 0/1/2. This is a research container with 45 fixed bytes plus 2 bytes/op, **not actual CMPCT revision-24 archive bytes**.

| Frozen family | Programs | Depth 0 charged B | Best depth 1 charged B | Best depth 2 charged B | 2 vs best <=1 | Selected 2-stage program |
|---|---:|---:|---:|---:|---:|---|
| A: interleaved smooth 16-bit lanes | 211 | 32,826 | 5,783 | **4,502** | **-1,281 B / -22.15%** | S(8) -> D(1) |
| B: held-out 32-bit lane geometry | 211 | 21,940 | 7,848 | **4,749** | **-3,099 B / -39.49%** | D(16) -> S(16) |
| C: 8-byte records with sparse shocks | 211 | 5,818 | 2,885 | **2,077** | **-808 B / -28.01%** | D(8) -> S(8) |
| D: variable-length UTF-8 logs | 111 | **4,537** | 5,530 | 6,207 | **+1,670 B / +36.81%** | X(1) -> X(1) (loses) |
| E: seeded noise | 211 | **32,826** | 32,828 | 32,830 | **+4 B / +0.012%** | D(1) -> D(1) (loses) |

**955** exhaustively enumerated candidates; all candidate transforms were forward/inverse tested for byte equality, and the best result at each depth was independently decompressed/inverted and SHA checked. Source/input SHA-256 and full best-by-depth program descriptors are preserved in the raw hosted JSON. All datasets and grammar were fixed before results, without per-corpus rule changes.

The two prespecified acceptance cohorts **A and B** both exceed the >=1% AND >=64 B complete-storage rule. This preserves **BOUNDED_HEADROOM_SEED**, not a production compressor promotion. C is additional transfer within related record geometry; D and E sharply demonstrate that the family is not generically beneficial without bounded admission and direct fallback.

## Economic and causal limits

Per-cohort exhaustive creation/search wall was A 7.288s, B 8.766s, C 7.943s, D 6.657s, E 5.857s (total **36.511s** to search five tiny streams). Startup from calling the zstd CLI hundreds of times is included; this is *research exploration cost*, not a production encoder runtime measurement. It demonstrates that brute-force, program-by-program audition is not an acceptable online admission strategy without major cost reduction or proof shortcuts. Unmeasured: peak RSS, selective physical bytes/read amplification, cold read, filesystem metadata, reader/native implementation, cross-platform decoding, native ABI, full archive integration, recovery/durability and release-parity costs. No archive-internal bytes or performance gate earned.

The winning two-stage programs exploit low-order numeric continuity and regrouping, not arbitrary-file semantic understanding. The held-out cohort changes lane width and data law but remains synthetically constructed. This does **not** show generalization to unstructured real files. No corpus recognition or fixture identifiers are allowable admission features.

## Stronger external prior art and anti-novelty check

A composed byte-shuffle/delta-like filter chain is not a novel primitive. [Blosc2's physical format supports ordered multi-filter pipelines and explicit shuffle/delta metadata](https://blosc.org/c-blosc2/format/chunk_format.html). [HDF5's existing filter pipeline](https://portal.hdfgroup.org/documentation/hdf5/latest/_h5_d__u_g.html) is mature prior art. More fundamentally, [OpenZL's September 24, 2026 Compression Transformer](https://openzl.org/blog/2026-09-24-compression-transformer/) selects codec graphs dynamically and documents stronger real-world numeric reference comparisons. Those systems must be treated as serious alternatives, not dismissed because this synthetic Zstd-only oracle succeeds. This result shows *headroom relative to frozen simplified controls*, not superiority to these systems, inventive novelty, nor product dominance.

## Counterfactual, disposition, next discriminator

The prospective simplest control (depth 0/1) already captured substantial redundancy; however, on A/B/C it would have missed an additional 22–39% of charged bytes. The fully charged two-operator rung earned useful evidence without changing product code. The cheaper next action is a **source-exact comparison against mature filter/graph implementations on held-out, real numeric and nonnumeric files** with matched stream/container/integrity semantics, followed by an admission predictor that can reject non-beneficial cases *without exhaustively compressing 211 candidates*. The product fork should be closed early if generic admission plus search overhead consumes the gain.

No Discovery Engine self-policy change was earned by one positive synthetic result. No `docs/discovery/STATE.json` update: ongoing owner #440, and this research-only result must not overwrite shared cache. No format/version/benchmark threshold changes; no merge, no release.

**Verdict: A05 two-stage composition headroom ADVANCED (bounded research seed), novelty UNPROVEN, product economics UNPROVEN, arbitrary-data generality UNPROVEN. The direct baseline wins D/E.**

## Hosted CI classification and correction receipt (2026-10-25)

The initial PR-head hosted oracle ran and passed before this report. Its first CI topology run correctly rejected missing deep-lane declaration and top-level cancellation; the workflow was repaired without weakening the validator. The subsequent source-head `ededaf07d5aa4dfd9febc82aff89026da5f4433d` reported O120 scientific **SUCCESS**, CI topology **SUCCESS**, Version Discipline **SUCCESS**, and R36 Attribution **SUCCESS**. Engineering Evidence returned **FAILURE** because the PR event snapshot did not contain exact canonical dossier headings; the PR description was updated to include all required literal headings before this new synchronization. The source-exact scientific result remains the original run 40235537602, and any checks newly generated by this documentation-only commit must be evaluated on their own HEAD. General Tests and release-performance claims are not credited from the specialized oracle.

Engineering Evidence on previous head `555b4f8661363f4d1bc2304bd5aeee5ca3cfd587` remained **FAILURE** because the literal headings were at Markdown level 3; the current PR body now uses the validator's required level-2 headings. This documentation-only synchronization requests a new exact-head receipt, not a presumptive pass. All previous red evidence remains preserved in GitHub Actions.
