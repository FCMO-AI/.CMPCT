# CMPCT v0.30 research handoff — Geometry Compiler

**Canonical cross-session status document for PR #45.**

Status: **ACTIVE RESEARCH / DO NOT MERGE / DO NOT VERSION-BUMP**  
Branch: `agent/lattice-v030-breakthrough`  
PR: `#45` — `research: v0.30 Geometry Compiler breakthrough campaign`  
Accepted production floor: CMPCT **v0.29.0**, research attempt-5 portfolio, canonical format revision **r24** unchanged.

This document is intentionally redundant with the PR description. A future session should be able to recover
the entire campaign from this file plus the committed benchmark records without needing chat history.

---

## 1. Mission lock

### Requested

- Continue the post-v0.29 compression research with an "Oppenheimer" / breakthrough-first philosophy.
- Prefer representation changes that can create large new gains over incremental parameter tuning.
- Preserve exact fallback and all safety/integrity invariants.
- Document the work so another session can resume immediately.
- **Do not merge yet.**

### Inferred

- Numeric v0.30 is earned only after the breakthrough survives complete-artifact generalization and the
  exported creation/extraction/memory/native/portability debt is rehabilitated.
- A spectacular local transform is useful research evidence but is not a public release claim.
- Negative results remain first-class evidence; failed mechanisms are not silently deleted.

### Non-goals

- no canonical-r24 grammar change in this research stage;
- no website/release headline claiming v0.30;
- no extension/MIME-specific codec routing;
- no lossy semantic conversion;
- no merge to `main` until explicitly authorized after promotion gates are green.

---

## 2. Core conceptual breakthrough: compile byte geometry

CMPCT v0.29 mainly reasons about **relationships between logical objects**: resemblance roots, Mosaic
placements, residual programs and packs. The v0.30 research direction adds a second axis:

> Before choosing an entropy codec, synthesize a bounded reversible layout in which the bytes expose their
> latent regularity more clearly.

The writer is therefore treated as a tiny **byte-layout compiler**. It may propose several reversible
physical views of the same logical node, but only measured stored cost can admit one.

### Geometry ladder

| Stage | Research primitive | Purpose |
|---|---|---|
| G0 | direct bytes | inherited control |
| G1 | fixed byte lanes (2/4/8/16) | expose fixed-stride byte planes |
| G2 | flat delimiter transpose | expose repeated segment positions |
| G3 | **Hierarchical Geometry** | discover records, then fields inside records, then transpose field positions |
| G4 | **Prefix Planes** | front-compress adjacent values inside each discovered field column |
| G5 | future field-local symbol tables | only if independently profitable after G4 |
| R1 | PrefixGraph / raw-prefix edges | orthogonal version-family representation; kept causally separate |

The important refinement is that G3/G4 do **not** require a schema. The same machinery may discover newline,
comma, `=`, `:`, `.`, `}`, or arbitrary binary separator bytes purely from measured recurrence. Human ideas
about what a delimiter "means" are irrelevant.

---

## 3. Relationship to external prior art

The campaign is not claiming that transposition, front compression or columnar storage are new ideas.
Relevant primary/official references are recorded here so future sessions do not rediscover them:

- Apache Parquet `BYTE_STREAM_SPLIT` separates fixed-width values into byte streams before compression:
  <https://parquet.apache.org/docs/file-format/data-pages/encodings/>
- The same Parquet encoding specification defines delta-length byte arrays and delta byte arrays / front
  compression, separating length/control streams from payload bytes.
- Apache Parquet Variant Shredding demonstrates the storage benefit of turning semi-structured values into
  columns when structure is known or inferred:
  <https://parquet.apache.org/docs/file-format/types/variantshredding/>
- Masui et al., *A compression scheme for radio data in high performance computing*, describes Bitshuffle:
  <https://arxiv.org/abs/1503.00638>
- Chehaidar et al., *OptFSST: Optimized FSST String Compression* (2026), shows that field-local static-symbol
  coding still has meaningful headroom and that optimal encoding for a fixed symbol table can be improved:
  <https://arxiv.org/abs/2607.11271>

CMPCT's research distinction is the composition and admission policy: **arbitrary bytes -> bounded structural
inference -> reversible layout program -> exact cost audition -> workload-level fallback**, without requiring
an external schema or file type to authorize the transform.

---

## 4. Surviving complete-artifact seed: flat Geometry on public ML

Exact public ML tree:

- workload: `09_ml_artifacts`
- logical bytes: **18,172,774 B**
- tree SHA-256: `efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d`
- accepted v0.29 archive: **13,836,439 B**
- complete Geometry research archive: **13,394,449 B**
- saving: **441,990 B / 3.194391273650684%**

The complete research artifact includes physical record headers, CRC32/SHA-256 integrity, Merkle leaves,
duplicated compressed metadata and transform descriptors. This is the strongest complete-artifact evidence
currently preserved in the campaign.

The most extreme causal sub-result remains the public `tokenizer.json` stream:

- logical bytes: **2,810,845 B**
- direct Zstd-19: **166,909 B**
- fixed-width lane best: **51,634 B**
- flat delimiter Geometry: **2,782 B**

That result is exactly reversible and used no JSON parser or filename/MIME admission.

Durable machine record:
`benchmarks/history/2026-08-17-geometry-v030-seed-preci.json`

---

## 5. New refinement: Hierarchical Geometry + Prefix Planes

Flat delimiter geometry can fail when one record contains several distinct structural scales. Logs are the
canonical example: line length varies because of free-form tails, while the leading fields remain highly
regular. G3/G4 explicitly model that situation.

### G3 — Hierarchical Geometry

For one bounded logical node:

1. collect occurrence positions for all byte values in one O(n) pass;
2. nominate at most four primary separators from recurrence/gap statistics;
3. split records by one primary candidate;
4. sample at most 1,024 records and nominate at most six secondary separators from cross-record coverage and
   multiplicity stability;
5. store exact row/field lengths;
6. transpose field position `j` across records into column-major order;
7. screen candidates with a cheaper compressor level;
8. exact-price only a bounded finalist set at Zstd-19;
9. retain direct bytes if the finalist does not earn the minimum saving.

### G4 — Prefix Planes

For each discovered field position, adjacent values are front-compressed against the previous value in that
same synthetic column. Only the common-prefix length and suffix need to be stored; exact field lengths are
already part of the reversible layout descriptor.

This is especially effective for repeated identifiers, timestamps, keys and lexical scaffolding, but no
semantic interpretation is needed to discover them.

Implementation:
`experiments/entropygraph_v030_hierarchical_geometry.py`

Independent vectors / hostile bounds:
`tests/test_v030_hierarchical_geometry.py`

Focused public-corpus probe:
`benchmarks/hierarchical_geometry_v030_probe.py`

Isolated workflow:
`.github/workflows/v030-hierarchical-geometry.yml`

---

## 6. PRE-CI detached payload evidence for G3/G4

**Claim boundary:** every number in this section is an exact-generator / Zstd-19 payload probe, not a
complete CMPCT archive result. It exists to decide whether integration work is justified.

Environment used for this exploratory measurement: system Zstd **1.5.7**, balanced nodes <=512 KiB.

### 6.1 Public logs raw streams

The six deterministic raw logs generated by `corpus_logs` were measured as 30 balanced nodes.

- concatenated raw-log SHA-256: `4efd4d815bd672ad4af0184f47300f52815b0e9f96cdc542ae18a713ac637175`
- historical repaired full-workload tree SHA-256 expected by CI:
  `7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931`
- direct Zstd-19 payload aggregate: **2,533,213 B**
- Hierarchical Geometry finalist aggregate: **1,836,378 B**
- G3 saving: **696,835 B / 27.507951%**
- after Prefix Planes: **1,810,136 B**
- G3+G4 saving: **723,077 B / 28.543869%**
- additional G4 saving beyond G3: **26,242 B**

In the local prototype, all 30 nodes independently improved. The committed workflow freezes a deliberately
lower but still material disproof gate: **>=640 KiB total**, **>=16 KiB on every selected chunk**, exact source
identity, exact inverse, 0 payload regressions.

### 6.2 Exact generator `events.csv`

- SHA-256: `cc4563fbedc4eeda2547a2bf8d0f0cad0d5f3ecc99af2c17b4eb72fa30d13d4a`
- balanced-node direct Zstd-19 aggregate: **868,156 B**
- G3 aggregate: **223,547 B**
- G3 saving: **644,609 B / 74.250365%**
- G3+G4 aggregate: **150,145 B**
- G3+G4 saving: **718,011 B / 82.705297%**

### 6.3 Exact generator `events.jsonl`

- SHA-256: `60d216d826ce65f4de7e652ed44a5ea9babad75611b47dd7bc3407d9be791ec2`
- balanced-node direct Zstd-19 aggregate: **1,046,102 B**
- G3 aggregate: **207,696 B**
- G3 saving: **838,406 B / 80.145722%**
- G3+G4 aggregate: **155,278 B**
- G3+G4 saving: **890,824 B / 85.156514%**

### 6.4 Exact public ML text streams, bounded-node probe

`tokenizer.json` SHA-256:
`b3edcea04b7e9b9346ac309662449a806de437ed35a125a42948a14146ac9c41`

- bounded-node direct Zstd-19: **212,673 B**
- G3: **97,146 B**
- G3+G4: **13,582 B**
- saving: **199,091 B / 93.613670%**

`training.log` SHA-256:
`e1e2daa89012e46ef3d4001932498a09d42adbdf1e22d42935314cfff69cadb9`

- bounded-node direct Zstd-19: **180,772 B**
- G3: **104,055 B**
- G3+G4: **69,120 B**
- saving: **111,652 B / 61.763990%**

These bounded-node figures are a different accounting surface from the earlier whole-file flat-Geometry
`tokenizer.json -> 2,782 B` spotlight and must not be directly substituted for it.

---

## 7. Orthogonal PrefixGraph evidence

A separate depth-1 Zstd raw-prefix / patch representation remains causally separate:

- shifted versions: **1,723,056 -> 1,699,988 B** complete prototype, **23,068 B smaller**;
- boundary churn: **79,876 -> 75,276 B**, **4,600 B smaller**.

Both reconstructed their exact historical source trees. The mechanism attacks version relationships, not byte
layout, so it should only be combined after Geometry has its own full-artifact causal result.

---

## 8. Negative evidence and killed mechanisms

- Multi-View HyperPack: **0 B** complete-artifact saving versus accepted v0.29 on the fixed hostile aggregate;
  portfolio construction was roughly **672 s**. Rejected as a size breakthrough.
- HyperPack did expose a locality bug in weighted-average accounting: an inherited plan could hide a
  ~53.7x worst-member outlier. Future elastic packing uses **per-member <=8x** as the admission law.
- Flat Geometry originally produced no payload win on the deterministic logs probe under its one-separator
  regularity model. G3 exists specifically because that negative result revealed the missing hierarchy.
- Independent per-column Zstd frames were briefly checked during G3 exploration and were worse than keeping
  the transposed columns in one bounded Zstd stream on the sampled logs node. Separate frames are therefore
  not automatically assumed to be better.

Negative evidence must stay in the campaign; do not prune it from later summaries merely because G3/G4 win.

---

## 9. Geometry IR — proposed architecture after the seed

The durable design direction is a small **Geometry Intermediate Representation (GIR)** rather than an
unbounded collection of special-case transforms.

A GIR candidate should be a bounded transform program such as:

`SOURCE -> SPLIT(primary) -> SPLIT(secondary) -> FIELD_TRANSPOSE -> PREFIX_PLANE -> ZSTD`

or

`SOURCE -> BYTE_LANES(width=4) -> ZSTD`

Each operation must declare:

- exact inverse;
- maximum input/output bytes;
- worst-case operation count;
- temporary-memory bound;
- dependency depth;
- selective-read amplification implications;
- descriptor cost;
- portable implementation requirement.

The compiler may search a small grammar, but search itself also has a resource budget. This prevents
"compression ratio by combinatorial CPU explosion."

### Admission vector

Research-seed admission may temporarily optimize stored bytes while exposing timing debt, but release
promotion is multi-objective. Track at minimum:

`(stored_bytes, create_cpu, extract_cpu, peak_memory, read_amplification, dependency_depth, parser_risk)`

Hard safety/integrity bounds are never tradeable. A byte winner that exceeds them is not a candidate.

---

## 10. Resource/safety contract for G3/G4

Current transform/oracle limits:

- logical node <= inherited **512 KiB**;
- primary candidates <= **4**;
- secondary candidates per primary <= **6**;
- rows <= **65,536**;
- fields per row <= **256**;
- total field descriptors <= **131,072**;
- rectangular cell scans <= **4,194,304** (8x logical-node ceiling);
- exact finalist count <= **3**;
- over-budget writer shape: reject transform and preserve fallback;
- over-budget reader descriptor: fail closed before materialization/transpose;
- byte-exact inverse required before a candidate is priced as evidence.

The committed test suite includes independent hand-derived HGT2/HGP2 vectors and a tiny-input / huge-rectangle
adversary specifically designed to defeat a simple total-byte safety check.

---

## 11. Research debt — intentionally open

1. **Complete-artifact integration:** G3/G4 are not yet represented inside a self-contained CMPCT research
   archive. Payload wins must survive headers, descriptors, duplicate metadata and integrity structures.
2. **Mosaic integration:** the correct long-term boundary is likely Mosaic's authenticated physical-record
   compiler, not a parallel whole-artifact build. Reuse already-computed logical graph decisions.
3. **Creation CPU:** current transform search still performs bounded multi-candidate compression auditions.
   Reduce this with predictor/screening work without losing the winning bytes.
4. **Extraction CPU and memory:** exact measurement pending.
5. **Native/shared reader:** no promoted native decoder exists for HGT2/HGP2.
6. **Portability/recovery:** research grammar only.
7. **15-workload complete-artifact matrix:** mandatory before any numeric release discussion.
8. **External competitor matrix:** rerun solid Zstd, 7z and ZPAQ only after exact new CMPCT artifacts exist.

---

## 12. Next experimental ladder

Run in this order unless new evidence falsifies the premise:

1. **Independent logs oracle** — `.github/workflows/v030-hierarchical-geometry.yml`; retain G3/G4 only if the
   frozen 640 KiB / 16 KiB-per-chunk threshold passes on the historical repaired tree.
2. **Exact HGT2/HGP2 research archive** — add authenticated descriptors, duplicate metadata and recovery;
   full strong-verify back to source tree.
3. **Focused complete archives:** logs + analytics + ML; prove the detached gains survive framing.
4. **15-workload same-live-tree portfolio:** accepted v0.29 exact fallback on every row; zero byte regressions.
5. **Internalize Geometry into Mosaic:** transform eligible physical direct records in-place instead of
   building a second archive; preserve deltas/residual packs/Preflate untouched where they already win.
6. **Rehabilitate search CPU:** use cheap structural sketches / cached compression / pair screening. Every
   rehabilitation step must retain the winning archive bytes.
7. **Only then test G5 symbol tables:** OptFSST-like field-local symbolization is attractive, but it does not
   get implementation complexity unless it clears its own preregistered complete-cost gate.
8. **Then combine PrefixGraph:** only after both mechanisms have independent causal evidence.
9. **Promotion:** unchanged ordinary release performance, native, version-discipline, site and engineering
   evidence gates. Numeric v0.30 remains blocked until all confirmed debt is closed.

---

## 13. Session pickup checklist

A future agent/session should begin by reading, in order:

1. this file;
2. PR #45 body and latest commits;
3. `docs/BREAKTHROUGH_REHABILITATION.md`;
4. `docs/LATTICE_V030_EVIDENCE.md`;
5. `benchmarks/history/2026-08-17-geometry-v030-seed-preci.json`;
6. `experiments/entropygraph_v030_hierarchical_geometry.py`;
7. latest focused workflow artifacts for `v030-hierarchical-geometry.yml` and `geometry-v030-breakthrough.yml`.

Do not infer that a queued/cancelled GitHub run falsifies the mechanism; inspect whether the engine actually
ran. Conversely, do not promote local measurements merely because CI is congested.

---

## 14. Merge lock

**User instruction for the current campaign: DO NOT MERGE YET.**

The PR may remain/reopen as a **draft research PR** for discoverability and cross-session continuity. Do not
mark ready, enable auto-merge, merge, bump the project version, or publish v0.30 site claims until the user
later authorizes promotion and the normal release gates independently support it.
