# CMPCT v0.30 research handoff V2 — Geometry IR / CMPNX14

**CANONICAL PICKUP DOCUMENT FOR THE CURRENT CAMPAIGN.**  
Status: **ACTIVE RESEARCH — DO NOT MERGE — DO NOT VERSION-BUMP**  
Branch: `agent/lattice-v030-breakthrough`  
Research PR: #45  
Production floor: **CMPCT v0.29.0**  
Canonical public format: **r24 unchanged**

V2 supersedes `docs/GEOMETRY_V030_RESEARCH_HANDOFF.md` as the current-state handoff. The older file remains
valuable historical evidence for how G3/G4 were derived, but it predates the self-contained CMPNX14 grammar.
A future session should read this file first, then the PR body, then the machine-readable evidence records.

---

## 1. Mission / merge lock

The user explicitly requested continued breakthrough-first research and **DO NOT MERGE YET**.

Therefore:

- do not merge PR #45;
- do not enable auto-merge;
- do not mark the PR ready for release review;
- do not bump `pyproject.toml` above 0.29.0;
- do not change canonical `src/cmpct/__init__.py` away from r24 / 0.24.0 semantics;
- do not publish v0.30 website/release claims;
- do preserve research wins, failed mechanisms, exact trees, resource debt and falsification thresholds.

A research mechanism may temporarily export creation CPU under the breakthrough-rehabilitation doctrine.
Safety, integrity, byte-exactness and promotion gates are never tradeable.

---

## 2. Current hypothesis: compression as bounded byte-layout compilation

CMPCT v0.29 reasons mostly about relationships **between objects**. The v0.30 campaign adds relationships
**inside byte layout**.

The durable abstraction is now a small **Geometry Intermediate Representation (GIR)**:

`logical bytes -> bounded reversible layout program -> entropy codec`

Current transform ladder:

- **G0 Direct** — original bytes;
- **G1 Byte Lanes** — 2/4/8/16-byte fixed-stride transpose;
- **G2 Flat Delimiter Geometry** — one recurring separator, exact segment lengths, segment-position transpose;
- **G3 Hierarchical Geometry** — discover record separator, then a second recurrent separator inside records,
  then transpose discovered field positions;
- **G4 Prefix Planes** — within each synthetic field column, front-compress the next value against the prior
  value using exact common-prefix length plus suffix;
- **G5 Field-local symbol coding** — deliberately deferred until G3/G4 complete-artifact evidence survives;
- **R1 PrefixGraph** — orthogonal depth-1 version-family raw-prefix/patch representation, kept causally separate.

No extension, MIME type, JSON/CSV/log parser, schema, field name or workload identity authorizes G1-G4.
Candidate separators may be printable or arbitrary binary bytes. Measured stored cost decides admission.

---

## 3. External prior art / what is and is not novel

Do not claim that byte transposition, columnar storage or front compression are novel in isolation.

Primary/official references already reviewed:

- Apache Parquet encodings (`BYTE_STREAM_SPLIT`, delta length and delta byte arrays/front compression):
  <https://parquet.apache.org/docs/file-format/data-pages/encodings/>
- Apache Parquet Variant Shredding for columnizing semi-structured values:
  <https://parquet.apache.org/docs/file-format/types/variantshredding/>
- Masui et al., Bitshuffle: <https://arxiv.org/abs/1503.00638>
- Chehaidar et al., OptFSST (2026): <https://arxiv.org/abs/2607.11271>

The CMPCT research contribution under test is the composition/policy:

**arbitrary bytes -> bounded structure inference -> reversible layout program -> exact stored-cost audition ->
node-level incumbent fallback -> complete accepted-v0.29 archive fallback.**

---

## 4. Strongest complete evidence before CMPNX14

### Flat Geometry complete ML artifact

Exact public workload `09_ml_artifacts`:

- tree SHA-256: `efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d`
- logical bytes: **18,172,774**
- accepted v0.29: **13,836,439 B**
- complete CMPNX13 Geometry archive: **13,394,449 B**
- saving: **441,990 B / 3.194391273650684%**

Machine record:
`benchmarks/history/2026-08-17-geometry-v030-seed-preci.json`

Whole-file mechanism spotlight, exact public `tokenizer.json`:

- direct Zstd-19: **166,909 B**
- fixed-width lane best: **51,634 B**
- flat delimiter Geometry: **2,782 B**

This was byte-exact and semantic-blind.

---

## 5. G3/G4 pre-CI mechanism evidence

**Claim boundary: detached Zstd-19 payload measurements, not complete archive sizes.**

Machine record:
`benchmarks/history/2026-08-17-hierarchical-geometry-v030-preci.json`

### Public repaired logs, six raw streams / 30 <=512 KiB nodes

- expected full workload tree: `7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931`
- direct Zstd-19: **2,533,213 B**
- G3: **1,836,378 B**
- G3+G4: **1,810,136 B**
- saving vs direct: **723,077 B / 28.543869%**
- additional G4 saving vs G3: **26,242 B**

Focused independent gate:
`.github/workflows/v030-hierarchical-geometry.yml`

Frozen disproof threshold:

- exact historical source identity;
- 6 raw streams / 30 balanced nodes;
- all 30 nodes must improve;
- each selected node >=16,384 B saving;
- aggregate >=655,360 B saving;
- 0 payload regressions;
- exact inverse and bounded exact-finalist count.

### Exact public generator analytics text streams

`events.csv`:

- direct: **868,156 B**
- G3+G4: **150,145 B**
- saving: **718,011 B / 82.705297%**

`events.jsonl`:

- direct: **1,046,102 B**
- G3+G4: **155,278 B**
- saving: **890,824 B / 85.156514%**

These numbers exclude SQLite/NPY/NPZ members and therefore are not full analytics-workload claims.

### Exact public ML text streams, bounded-node accounting

- tokenizer: **212,673 -> 13,582 B**, saving **93.613670%**;
- training log: **180,772 -> 69,120 B**, saving **61.763990%**.

Do not conflate the bounded tokenizer result with the earlier whole-file 2,782-byte spotlight.

---

## 6. CMPNX14 — self-contained Geometry IR archive

Implemented research grammar:
`experiments/entropygraph_v030_gir.py`

Hardened execution entrypoint:
`experiments/entropygraph_v030_gir_safe.py`

Tests:
`tests/test_v030_gir.py`

CMPNX14 exists to answer the question detached payload oracles cannot answer: **do G3/G4 still win after
complete archive framing?**

### Node tournament

For every unique balanced <=512 KiB logical node:

1. CMPNX13 auditions G0/G1/G2 and returns its exact best physical payload;
2. G3/G4 audition independently;
3. G3/G4 may replace the CMPNX13 incumbent only when its exact stored payload is strictly smaller;
4. the winning transformed physical record receives CRC32 + SHA-256 and an authenticated payload leaf;
5. logical node hash remains the final reconstruction oracle.

This gives two fallback layers:

- **node fallback:** new hierarchy cannot make a node worse than G0/G1/G2;
- **archive fallback:** public `build()` emits accepted v0.29 unchanged unless the entire CMPNX14 file is smaller.

### Complete archive contract

CMPNX14 includes:

- new research magic `CMPNX14` / tail `CMN14T`;
- explicit node descriptors for direct/lane/delimiter/hierarchical physical views;
- HGT2/HGP2 parameters embedded only in the authenticated transformed physical stream, avoiding duplicate
  metadata sources of truth;
- physical CRC32 + SHA-256;
- Merkle authentication of physical payloads;
- compressed primary metadata;
- duplicate authenticated tail metadata for recovery;
- exact logical file/node hashes;
- strong tree verification;
- lexical path policy and resolved extraction containment check;
- dependency depth 0 and standalone node read amplification 1.0.

### Safety inheritance correction

During the reader audit, CMPNX14 was found to import raw CMPNX13 and could therefore bypass the later G2
ragged-transpose work bound. That is preserved as a caught regression, not hidden.

`entropygraph_v030_gir_safe.py` now imports `entropygraph_v030_geometry_safe` **before** GIR, patching the shared
G2 module object so flat Geometry and hierarchical Geometry both obey bounded writer/reader work. Tests and
benchmarks use the hardened entrypoint.

Before any promotion, this import-order safety dependency should be folded into the final owning module so a
raw research import cannot bypass it.

---

## 7. CMPNX14 adversarial / recovery tests

`tests/test_v030_gir.py` adds:

- complete structured + deterministic-hostile round trip;
- requirement that at least one hierarchical/prefix node actually appears;
- strong tree hash agreement;
- extraction byte equality;
- primary metadata corruption with successful authenticated duplicate-tail recovery;
- rejection of hierarchical resource-budget escalation;
- rejection of compressor-identity drift in authenticated metadata;
- assertion that the G2 cell-work guard is installed by the hardened entrypoint;
- path traversal / absolute path / Windows separator / NUL rejection.

These tests are run before the focused complete benchmark.

---

## 8. Frozen three-workload complete-artifact gate

Harness:
`benchmarks/gir_v030_focused_complete.py`

Workflow:
`.github/workflows/v030-gir-focused-complete.yml`

The gate was frozen before independent execution. Exact workloads:

1. `05_logs_and_telemetry` — tree `7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931`
2. `04_analytics_and_database` — tree `6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d`
3. `09_ml_artifacts` — tree `efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d`

For every row, the harness builds accepted v0.29 and raw CMPNX14 from the **same live exact tree**, then strong-
verifies both.

Frozen survival threshold:

- GIR itself must be smaller than v0.29 on **all 3**, without using workload fallback to fake a win;
- each row must save at least **262,144 B**;
- aggregate saving must be at least **2,097,152 B (2 MiB)**;
- 0 regressions;
- all six strong-verification results must match their source tree;
- hierarchical nodes and Prefix Plane nodes must both occur.

Passing this gate means only that complete framing survives three preregistered categories. It does not make
CMPNX14 a release.

---

## 9. Orthogonal PrefixGraph evidence

Keep separate until GIR has independent full-artifact evidence:

- shifted versions: **1,723,056 -> 1,699,988 B**, saving **23,068 B**;
- boundary churn: **79,876 -> 75,276 B**, saving **4,600 B**.

Both depth-1 prototypes reconstructed exact historical trees. PrefixGraph attacks version relationships;
Geometry attacks byte layout. Combining them too early destroys causal attribution.

---

## 10. Negative evidence / killed paths

Preserve these in all later summaries:

- Multi-View HyperPack: **0 B** complete-artifact saving; ~**672 s** portfolio creation. Rejected as size path.
- Weighted read-amplification accounting was unsafe; it hid ~53.7x member outliers. Future elastic packs use
  **per-member <=8x**.
- Flat G2 originally found no win on deterministic logs. This negative result directly motivated G3.
- Independent per-column Zstd frames were worse than one bounded transposed stream on sampled G3 log nodes.
- G5/OptFSST-like field symbol coding has **not** earned implementation yet.
- Search CPU remains debt; compression ratio may not be purchased with unbounded combinatorial audition.

---

## 11. Resource contract

Current G3/G4 search/reader envelope:

- max logical node: **524,288 B**;
- max primary candidates: **4**;
- max secondary candidates per primary: **6**;
- max rows: **65,536**;
- max fields/row: **256**;
- max field descriptors: **131,072**;
- max rectangular cell scans: **4,194,304**;
- max high-effort exact finalists: **3**;
- screen compressor level: **6**;
- final compressor level: **19**;
- writer over-budget proposal: reject candidate and preserve incumbent;
- reader over-budget descriptor: fail closed before materialization/work;
- byte-exact inverse required before a transform is eligible as benchmark evidence.

CMPNX14 currently remains depth 0 / node read amp 1.0. Any later Mosaic/pack integration must preserve the
separate **per-member <=8x** locality law.

---

## 12. Open regression debt

Do not convert any of these into implicit success:

1. focused CI is still required for the logs payload gate and three-workload complete gate;
2. creation/search CPU remains intentionally expensive during discovery;
3. current G3/G4 audition screens plain and prefix variants separately for nominated pairs — a future
   rehabilitation should screen separator pairs once, then exact-price both views only for finalists, but
   this optimization is **not implemented yet**;
4. extraction latency and peak memory need measured accounting;
5. no promoted native/shared reader exists for CMPNX14/HGT2/HGP2;
6. recovery/malformed fuzzing is incomplete beyond current unit adversaries;
7. 15-workload complete-artifact generalization has not yet run;
8. Geometry is still standalone rather than integrated into Mosaic's physical compiler;
9. external 7z/solid-Zstd/ZPAQ matrix must be rerun only after exact candidate artifacts exist.

---

## 13. Next experiment ladder

Do not skip causal stages merely because detached numbers are large.

1. Let the frozen logs payload oracle finish. Do not weaken >=640 KiB / >=16 KiB-node thresholds.
2. Let the frozen three-workload CMPNX14 gate finish. Do not weaken >=256 KiB each / >=2 MiB aggregate.
3. If either fails, inspect exact failing rows/test boundaries; repair implementation bugs without changing the
   benchmark contract. A true mechanism miss goes back to representation research.
4. If CMPNX14 survives, commit its CI artifact as a durable machine evidence record.
5. Run complete 15-workload same-live-tree CMPNX14 vs accepted v0.29, with exact v0.29 fallback and 0-byte
   regression tolerance.
6. Move winning Geometry transforms **inside Mosaic's authenticated physical-record compiler**, preserving
   Mosaic/residual/Preflate decisions where they already win.
7. Rehabilitate creation CPU using bounded structural sketches, pair-level screening, cached compression and
   exact finalist pricing. Every speed improvement must retain winning archive bytes.
8. Measure extraction, selective read and peak memory.
9. Only after G0-G4 are stable, preregister a G5 field-symbol-coding experiment.
10. Only after independent Geometry and PrefixGraph evidence, test their composition.
11. Promotion remains blocked until ordinary release performance/native/version/site/engineering gates pass
    unchanged **and the user explicitly authorizes merge/release work**.

---

## 14. Session pickup order

A future session should read:

1. `docs/GEOMETRY_V030_RESEARCH_HANDOFF_V2.md` (this file)
2. PR #45 current body and latest head
3. `docs/BREAKTHROUGH_REHABILITATION.md`
4. `benchmarks/history/2026-08-17-geometry-v030-seed-preci.json`
5. `benchmarks/history/2026-08-17-hierarchical-geometry-v030-preci.json`
6. `experiments/entropygraph_v030_hierarchical_geometry.py`
7. `experiments/entropygraph_v030_gir_safe.py` then `experiments/entropygraph_v030_gir.py`
8. `tests/test_v030_gir.py`
9. latest artifacts/status for `v030-hierarchical-geometry.yml`
10. latest artifacts/status for `v030-gir-focused-complete.yml`

Queued/cancelled Actions are not mechanism evidence unless the engine actually ran. Local numbers remain local
until independently reproduced. Never turn a detached payload result into a complete archive or release claim.

---

## 15. Final lock

**DO NOT MERGE.**  
**DO NOT VERSION-BUMP.**  
**DO NOT PUBLISH v0.30 CLAIMS.**

This research branch exists to accumulate falsifiable breakthrough evidence until the user later authorizes a
promotion campaign.
