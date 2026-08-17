# CMPCT v0.30 / canonical r25 — productionization handoff

> **PRODUCTION-CANDIDATE RESEARCH — DO NOT MERGE TO `main`, DO NOT VERSION-BUMP, DO NOT PUBLISH v0.30 CLAIMS.**
>
> Production remains project **v0.29.0**, canonical archive revision **r24**. This document describes the
> evidence path required before any later session may propose changing that statement.

This is the canonical pickup document for turning the v0.30 representation research into a real CMPCT release.
It complements, rather than rewrites, `docs/GEOMETRY_V030_RESEARCH_HANDOFF_V2.md` and PR #45's append-only
research discussion. Historical negative evidence and old research magics remain valid history.

## 1. Mission lock

### Requested

- finish the v0.30 research line to production quality;
- make the strongest verifiable use of every promising idea already considered;
- improve compression materially without regressing correctness, integrity, portability or ordinary archive
  semantics;
- preserve falsification: a mechanism that misses its frozen gate is retained as negative evidence, not rescued
  by lowering the gate.

### Inferred

- “absolute most” means the best *legal measured representation*, not the largest feature pile;
- SOTA mechanisms are welcome, but their prior-art contribution must be separated from CMPCT-specific novelty;
- production must extend the canonical archive product rather than replacing it with a benchmark-only tree
  container.

### Non-goals

- claiming program synthesis, bitshuffle, delta coding, string attractors, facility-location or equality
  saturation as CMPCT inventions;
- format-specific semantic parsing to force a transform;
- a release whose only evidence is a friendly text/ML payload probe;
- trading resource safety, path safety, exact reconstruction, recovery or truthful accounting for size.

## 2. Production architecture selected

The key production decision is now stable:

**Build/preserve the canonical r24 logical archive model first, then compile its physical blob embodiments.**

This preserves the existing semantics already owned by `src/cmpct`:

- directories, symlinks and hardlinks;
- sparse extents;
- fixed and content-defined chunk maps / range reads;
- micro-solid packs;
- exact nested ZIP/WHL virtualization and Deflate-stream reuse;
- uid/gid and xattrs;
- dual indexes / recovery semantics;
- legacy ZIP export compatibility.

Canonical **r25** introduces a new physical Geometry codec only when its fully charged metadata + payload is
smaller than the current physical blob embodiment. Exact Deflate blobs are not rewritten because virtual-ZIP
recipes can intentionally observe their stored Deflate stream.

Current evidence implementation:

- `experiments/canonical_v25_geometry.py` — first r24→r25 physical compiler / Python reader;
- `experiments/canonical_v25_geometry_recovery.py` — production-hardening successor with self-locating recovery;
- `benchmarks/canonical_v25_geometry_safe_entrypoint.py` — routes the frozen focused gate through the hardened
  recovery contract;
- `benchmarks/canonical_v25_full_qualification.py` — preregistered full 15-workload promotion-size gate;
- `.github/workflows/v030-canonical-r25-full-qualification.yml` — manual until focused survival passes.

The research-only CMPNX13/14/15 formats remain mechanism evidence; they are not the intended public archive
format.

## 3. Current local representation compiler

`experiments/entropygraph_v030_representation_compiler.py` is the production-candidate per-node tournament.
Every candidate must invert exactly before exact pricing. Descriptor bytes are charged during local selection.

Current admitted ladder:

- **G0 direct** — inherited raw/Zstd physical bytes;
- **G1 fixed byte lanes** — widths 2/4/8/16;
- **G2 delimiter Geometry** — byte-discovered recurrent separator layout;
- **G3 Hierarchical Geometry** — infer rows and bounded secondary separators, transpose synthetic columns;
- **G4 Prefix Planes** — front-compress adjacent values in inferred columns;
- **G5 adaptive lane ordering** — same fixed-lane grammar plus one bijective lane permutation.

G5's reader-visible descriptor is only `width + permutation`. Writer-only nomination currently tries at most two
non-identity deterministic orders per width:

1. low empirical entropy first;
2. histogram-similarity chain.

Only three G5 finalists receive exact high-effort pricing. Admission requires >=64 complete local stored bytes
versus the original G0-G4 incumbent; every finalist is thresholded against that same incumbent so search order
cannot suppress a slightly better legal finalist.

Frozen incremental G5 gate (`benchmarks/g5_v030_incremental_probe.py`):

- exact public `scales.npy`: >=16 KiB beyond G0-G4;
- exact public `features.npy`: >=8 KiB beyond G0-G4;
- combined >=24 KiB;
- zero node regression / exact inverse;
- high-entropy `model.q4.bin` retained as hostile negative.

Historical local evidence motivating this gate was +18,149 B and +8,800 B respectively for entropy ordering;
the new histogram-chain nomination receives no credit until the frozen gate executes.

## 4. Orthogonal child reactors and admission rules

### 4.1 Bitplane Algebra — `agent/v030-latent-type-supercompiler`

Purpose: numeric/binary residual entropy after byte Geometry.

Candidate families: width/alignment inference, ordinary bitplane transpose, previous-value XOR/subtraction and
small invertible GF(2) xor-shift bases.

Attribution is mandatory: Geometry → plain bitplane → algebra. If plain bitshuffle explains the gain, keep that
SOTA primitive and reject CMPCT's algebraic extra.

Frozen gate:

- >=128 KiB aggregate beyond its Geometry incumbent;
- >=64 KiB on one numeric file;
- zero regressions / exact inverse.

First CI run failed **before benchmark** because a unit-test mock accidentally made the raw transformed fallback
one byte long. Production logic was not weakened; the fixture was corrected on `7442daba...`. The repaired run
`32074067923` is still queued at this handoff.

**Production admission requires a second audition against the full G0-G5 compiler**, because the child reactor's
incumbent predates G3/G4/G5.

### 4.2 Residualized Sequence Microprograms — `agent/v030-sequence-microprograms`

Purpose: turn discovered synthetic columns into tiny exact generators plus sparse exceptions.

Families include raw, period, dictionary, restricted alphabet, lexical integer, FOR, delta, delta², affine and
modular sawtooth models. “Type” is never trusted input metadata: lexical rendering must reproduce exact original
bytes including prefixes, suffixes, signs and zero padding.

Frozen gate:

- >=128 KiB incremental versus G3/G4;
- >=32 KiB on one exact public file;
- >=32 KiB attributable specifically to latent-integer synthesis in a counterfactual run with that codelet
  disabled;
- selected chunks >0, lexical-integer codelets >0, residualized models >0, zero file regressions.

Production audit closed hard reader issues before the next run:

- fixed-width lexical padding allocation bomb;
- decoded integers escaping signed-64 portability;
- affine/sawtooth parameter width drift;
- noncanonical fixed-pack high padding bits;
- duplicate/noncanonical dictionary encodings;
- lexical width/sign overflow.

The safe facade is benchmark-authoritative today. If the mechanism passes, these checks must move into one
production owner; no monkeypatch-style facade may ship.

### 4.3 Synthetic Attractor/Phrase Substrate — `agent/v030-attractor-substrate`

Purpose: manufacture shared phrase atoms that need not already exist as files/chunks, attacking redundancy that
Mosaic's selected direct roots can miss.

CMPNX15 is a complete research archive and is compared against accepted v0.29 plus same-live-tree solid
`tar+Zstd-19`.

Frozen gate:

- >=256 KiB raw win versus v0.29 on one focused workload;
- >=512 KiB portfolio aggregate across focused workloads;
- >=64 KiB better than same-tree solid Zstd on one workload;
- zero portfolio regression, exact verification, <=8 MiB physical decode unit.

Production audit strengthened its safe reader:

- physical records must be canonical contiguous records ending exactly at authenticated tail metadata;
- paths are rejected during verification, before materialization;
- phrase positions must fit declared physical records;
- stored phrase use counts are recomputed from file parses and must match exactly;
- logical parse length must equal declared logical size;
- codec/csize declarations are canonical and bounded;
- file/tree/reference materialization bombs fail before joining payloads.

**Passing the size gate is not enough for production.** Current phrase packing must then be rehabilitated to
measure and satisfy the separate **per-member <=8x** selective-read law. Weighted averages or “worst phrase” are
not substitutes. RSO/locality-aware co-packing is the preferred next experiment; if the gain cannot survive the
member-locality law, substrate remains research-only.

### 4.4 Representation Superoptimizer (RSO) — `agent/v030-rso-extractor`

Purpose: avoid destructive phase ordering when several targets share roots/atoms/dictionaries whose opening cost
is paid once.

Production audit found a critical correctness bug in the original constructor: policy filtering could remove all
plans for one declared target and silently drop that target from the optimization problem. The hardened owner now:

- captures declared targets before policy filtering;
- requires every target to retain a legal facility-free fallback;
- rejects duplicate target/plan identities;
- rejects noncanonical/NaN resource declarations;
- verifies exactly one selected plan per target;
- decomposes the sharing graph into independent connected components;
- exhaustively solves every component with <=18 active facilities;
- emits `optimality_proven=False` for larger components that require bounded beam extraction.

This turns “absolute most” into a testable property: a production archive may require every real sharing component
to receive an **exact optimality certificate**, pruning candidate generators until no component exceeds the exact
ceiling. Synthetic optimizer tests are not compression benchmarks; production admission requires fully priced
real candidate plans.

## 5. Canonical r25 recovery contract

The first r25 evidence footer was rejected during self-audit because tail recovery still depended on the primary
header's compressed-index length.

The hardened successor footer carries `record_base` explicitly and its domain-separated SHA-256 tail certificate
commits to:

- kind / index codec / flags / reserved;
- compressed and decoded index sizes;
- previous-footer pointer;
- `record_base`;
- decoded index bytes.

After certificate verification, the reader independently proves that the authenticated blob table exactly tiles
one contiguous physical region from `record_base` to the tail-index copy. Primary and tail may independently
recover a fresh archive; if both are valid they must agree.

Tests cover:

- corrupted primary compressed-index length recovered from tail;
- corrupted tail recovered from primary;
- record-base tamper invalidating the tail certificate;
- both paths unusable => fail closed;
- <=256 MiB index decode bounds.

Transaction/journal generations are **not yet r25-qualified** and remain a release blocker.

## 6. Frozen focused canonical gate

`benchmarks/canonical_v25_geometry_probe.py`, executed through the hardened safe entrypoint, regenerates exact:

- repaired logs `7356b866...`;
- analytics `6d0854fe...`;
- ML `efc09910...`.

For each same live tree it builds the real canonical r24 archive, compiles raw r25, proves canonical logical
sections and member bytes are unchanged, and compares complete artifact bytes.

Frozen survival gate:

- raw r25 beats r24 by >=256 KiB on **each** workload;
- aggregate >=2 MiB;
- at least one lane/delimiter/hierarchical/lane-permutation chunk is selected;
- no portfolio fallback may manufacture the three raw wins.

Passing this gate authorizes only the manual full qualification, not release.

## 7. Preregistered full 15-workload gate

`benchmarks/canonical_v25_full_qualification.py` was committed **before** focused results were known.

It regenerates the inherited 15-row public frontier, validates every source tree against the accepted historical
or repair-v5 identity, then measures same-live-tree r24 and self-locating r25.

Frozen contract:

- exactly 15 workloads;
- complete portfolio <= r24 on every row (0 B tolerance);
- >=2 MiB aggregate portfolio saving;
- >=3 workloads improved;
- canonical logical graph sections identical on every row;
- self-locating recovery contract present on every r25 row;
- raw r25 losses reported even when portfolio fallback wins.

Workflow: `.github/workflows/v030-canonical-r25-full-qualification.yml` is `workflow_dispatch` only until the
focused gate passes.

## 8. Remaining production gates — no release may skip these

### 8.1 Integrated writer

The current canonical evidence path is deliberately two-pass (`r24 build -> r25 physical compile`). Before
performance promotion, move surviving representation code into `src/cmpct` and make the normal builder price the
same views during physical encoding. The release timing gate measures that one-pass writer, not this prototype.

### 8.2 Native reader / portability

`native/cmpct-core` currently advertises and accepts revision 24 only. A real r25 release requires:

- memory-safe r25 header/tail recovery;
- codec-5 Geometry metadata parser with the same resource ceilings;
- independent golden vectors for G1-G5 / hierarchical + prefix variants that actually survive production;
- malformed/fuzz corpus parity against Python;
- exact SHA/CRC behavior;
- range/locality parity;
- Android/Linux/macOS/Windows portability rules or documented supported matrix.

The Python evidence reader is **not** a substitute for this gate.

### 8.3 Transaction / recovery parity

Canonical r24 supports generation/journal semantics. Fresh-build r25 currently supports dual full indexes only.
No public r25 until append/update/recovery behavior is either ported and conformance-gated or the release contract
explicitly and safely disables unsupported mutation rather than pretending parity.

### 8.4 Performance / memory

Release writer and reader need repeated same-runner medians. Regression blocks when >5% **and** >3 ms versus the
direct base. Record create, full extract/verify, selective reads and peak RSS. Representation search CPU is a
budgeted resource; expensive losers require a cheap screen/fast reject rather than permanent portfolio tax.

### 8.5 Locality

- Geometry preserves the canonical logical storage graph and must not worsen its decode topology;
- any new shared substrate/reference packing must satisfy **every member <=8x** read amplification;
- dependency depth remains bounded (production target depth <=1 for shared references).

### 8.6 External competitors

On the final same-live-tree suite rerun at least:

- ZIP/Deflate-9;
- solid tar+Zstd-19;
- 7z/LZMA2;
- ZPAQ m5 where available;
- structural/backup competitors already used by the public benchmark when available.

Semantic mismatches (solid/random access/recovery) must stay visible; size alone does not erase them.

### 8.7 Product surface

Only after all production gates and explicit user authorization:

- choose final project version / canonical revision;
- update version constants consistently;
- append durable benchmark history (never rewrite old records);
- update website/status tables from committed evidence;
- update compatibility/export docs;
- merge through to `main`.

## 9. Current branch map / pickup order

1. **Parent research reactor:** `agent/lattice-v030-breakthrough`, PR #45. Keep frozen while its G3/G4 and GIR
   independent gates are queued.
2. **Production staging:** `agent/v030-production-candidate`. Current production architecture, G5, canonical r25,
   self-locating recovery and preregistered full qualification live here.
3. **Bitplane:** `agent/v030-latent-type-supercompiler`. Wait for repaired frozen gate, then re-audition against
   full G0-G5 before possible integration.
4. **Sequence:** `agent/v030-sequence-microprograms`. Wait for hardened frozen gate; if green, internalize safety
   and add descriptor-aware incremental gate versus the then-current production compiler.
5. **Attractor:** `agent/v030-attractor-substrate`. If complete size gate wins, rehabilitate member locality before
   any canonical integration.
6. **RSO:** `agent/v030-rso-extractor`. Once semantics gate is green, feed real complete-cost candidates and
   require `optimality_proven=True` for production evidence.

Do not merge child mechanisms merely because their code exists. Each enters staging only after its frozen gate,
then must survive a second incremental gate versus the current staging incumbent.

## 10. Completion definition

The research campaign is **production-ready** only when all are true:

- [ ] parent G3/G4 independent gates executed at frozen thresholds;
- [ ] each child mechanism has an executed pass/fail record; losses preserved;
- [ ] every admitted mechanism survived a second incremental audition against current staging;
- [ ] canonical r25 focused gate green;
- [ ] canonical 15-workload gate green with 0 B regressions;
- [ ] integrated one-pass writer replaces two-pass evidence compiler without losing bytes;
- [ ] creation/extraction/selective-read/peak-memory gates green;
- [ ] every new shared member <=8x read amplification and dependency depth legal;
- [ ] r25 native reader + independent vectors + malformed/fuzz parity green;
- [ ] transaction/recovery parity green;
- [ ] external competitor matrix rerun on exact live trees;
- [ ] durable evidence appended and public claims generated from it;
- [ ] explicit user authorization to merge/release.

Until then, **v0.29.0 / canonical r24 remains the truthful production statement**.
