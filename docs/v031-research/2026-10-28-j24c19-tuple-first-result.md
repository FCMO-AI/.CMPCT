# J24C19 — Tuple-first immutable reference admission: source-exact result

Date: 2026-10-28 · **Decision: RETIRE AS IMMEDIATE SHIPPING OPTIMIZATION** · Research/oracle evidence only, NOT product, release, native ABI, parser safety or benchmark credit.

## Provenance and immutable prospective question

This is an independent P3 scientific follow-up to #676 and #679. Parent **exact** `3b6a73f9205f40f11124cd9ff332407e52cebb93`; the first child commit `822a80a349e15fa48e464c6e3ffb6df79c4bdf09` preregistered question, simpler control, 5% CPU/wall kill and incomplete semantic boundaries **before** any experiment code. The measured branch source was `95f34c532bae1384fb39ad8bcc398443c1e4edc2`, with `reader.py` and `_fastscan_abi3.c` verified bit-identical to parent. No product code was modified.

**Hosted original:** [J24C19 GitHub Actions #40709133246](https://github.com/FCMO-AI/.CMPCT/actions/runs/40709133246), SUCCESS. Artifact `12825116870`; original ZIP SHA-256 `dbc57bf4be708f37fa785336c831302d95a1d5b633ba400cde93965e869b36b7` (3,768 bytes). Original `observations.json` SHA-256 `7da46c6c433f4e68ff9ffa30f681138a7dc1eb98914d64bec365bea4d1cd6050`. Independently downloaded original ZIP, verified CRC, regenerated all six physical MessagePack byte streams without calling the study producer, checked SHA256, recomputed all twelve CPU/wall median ratios directly from 72 original samples, and cross-checked with the hosted referee. All calculations matched. The independent audit file is an activation artifact; GitHub CI preserves original source and receipt ZIP.

## Exact head-to-head measurements

Canonical benchmark here is **component-only index decode plus immutable chunk reference construction**, excluding full Reader and process startup. Both options run on exactly the same binary payload in isolated CPython 3.11 child processes; the freeze-after control is `msgpack.unpackb(use_list=True)` plus CPython `tuple(refs)`, and the candidate is `msgpack.unpackb(use_list=False)` plus schema-structural thaw without copying N chunk references. The source-exact worker design was balanced A/B/B/A, 24 subprocesses, 3 timed observations each, 72 total. The stored index bytes are unchanged, each candidate repacks exactly, and the current tuple-incompatible validator path is reported as a **negative**, not suppressed.

Candidate/control medians (values below 1 are faster):

| Number of references | Shape | Wall | CPU | Pass prereg 0.95 both? |
| ---: | --- | ---: | ---: | --- |
| 4,096 | fixed | 0.8854 | 0.8768 | Small control only |
| 4,096 | mixed | 0.8588 | 0.8588 | Small control only |
| 65,536 | fixed | 0.9266 | 0.9263 | YES, narrowly |
| 65,536 | mixed | **1.0124** | **1.0125** | **NO** |
| 262,144 | fixed | **0.9586** | **0.9584** | **NO** |
| 262,144 | mixed | **1.0115** | **1.0100** | **NO** |

The preregistered criterion required BOTH CPU and wall <=0.95 for BOTH 65k/262k in both physical shape variants. **Three of four decisive large profiles fail.** The scientifically honest decision is rejection of the proposed tuple-first microoptimization as a near-term Reader performance route. The hosted independent referee reports `RETIRE_TUPLE_FIRST_AS_IMMEDIATE_SHIPPING_OPTIMIZATION`, with 7/7 purposely forged evidence receipts rejected.

## The stronger semantic negative

An economic oracle cannot override the actual source contract:

1. `src/cmpct/validation.py::_validate_storage` requires a **list** for `S_CHUNKS` refs even if the tuple has identical integers and wire bytes.
2. `src/cmpct/_fastscan_abi3.c` uses `PyList_CheckExact(refs)`, so tuple-first cannot reach the original native proof without a new API and matching semantics.
3. The Reader transaction replay mutates `files`/`blobs` with `append`, `sort`, `put/del/ren`, and in-place row rename; raw tuple-first decode is not drop-in, and the experimental structural thaw does not yet establish full archive/journal compatibility.
4. Any publicly mutable alias or blob record remains an independent ownership/proof problem even if chunk refs are sealed.

These were prospective, independently inspectable kill conditions, not post-result caveats. An implementation that thaws the N refs back into a list to satisfy the unchanged ABI would lose the proposed ownership invariant and copy avoidance.

## Self-critique, contrary signals, and alternative explanations

A local Python3.13.5/msgpack1.1.2 exploratory in-process microproxy (not the installed CMPCT Reader) had apparently larger 0.73–0.81 ratios for 65k/262k, with Python traced peak allocations about 2x lower in its simplified model. It is **not source-exact, not Python3.11, not a portable product signal**. Differences can arise from CPython version, the independent local oracle, memory trace perturbation, OS or run ordering. Preserve this contradiction rather than average it against the stronger controlled hosted negative.

The hosted court used bounded synthetic lists of low-cardinality refs with tiny physical payload descriptions; it did **not** time full actual archive parsing, authenticated native scanner work, cold Reader sessions, read-range, recovery, extraction, update, peak whole-process RSS on all platforms or released-v0.30 floors. Peak-HWM fields are observations, not guaranteed incremental object memory savings. A scientific PASS is not an optimization win.

## Counterfactual and convergence

**Earlier sufficient discriminator:** the PyList-only native ABI, list-only storage validator and mutable transaction replay already ruled out a no-change drop-in; the cheapest fair microcourt then tested whether a sufficiently large ownership-economics margin might justify an explicit new architecture. Its four large cases did not pass. A transferable prospective lesson is to bind candidate ownership/collection types to the actual parser, native ABI and recovery mutation requirements *before* attributing decode-only wins to product. This one experiment does not justify editing Discovery policy. No `docs/discovery/STATE.json` mutation.

**Next highest-leverage unclaimed action:** leave #676's integrity containment as a protected **research** seed and hand the no-drop-in/no-economic-win result to its owner. Seek a materially different runtime/representation or product gap instead of another C loop, tuple conversion tweak, threshold, or benchmark-gardening step. If a future truly immutable decoder/ABI design is proposed, demand a source-exact full Reader security/recovery/product test with parent v0.30.0 and #662 controls before promotion.

## Explicit unchanged boundaries

Released v0.30.0/r24 untouched; no Builder/Reader/native/format/release/benchmarks/Discovery state changes, no merge. Owner PRs #662, #676, #679, #681 and Foundry #680 were not edited. CI success on the *measured source* `95f34c5` is established; later documentation-only HEAD requires its own exact-head checks before a full green claim.

## Architecture frame review: economical proof and separate product obligations

This episode closes the **tuple-first-plus-minimal-thaw** mechanism, not every possible immutable index architecture. A product-worthy alternative would need independent evidence for each boundary, and should not be attempted by silently changing the strict validator's accepted representation:

| Boundary | Existing exact contract | Cost/risk that must be measured |
| --- | --- | --- |
| Binary admission | `msgpack.unpackb(raw=False)`; strict malformed-map policy at preflight | Object count, nesting, untrusted memory, equivalent accept/reject semantics |
| Chunk proof | ABI3 accepts exact Python lists and returns exact logical prefix checkpoints | New tuple-aware native ABI must check the same every-ref indices and blob lengths; no proof bypass |
| Journal recovery | `files` and `blobs` are mutated by put/del/ren/replay | Thaw must preserve every historical committed generation, not only one single-file index |
| Public Reader metadata | `Reader.index/files/by/blobs` expose Python containers | Snapshot mutation must fail-closed or be authenticated; changing public types is a compatibility decision |
| Product economics | Published v0.30.0 and #662/#676 are real historical controls | Same authenticated archive, Q1/Q6/Q64, create/extract/verify, complete memory and cross-platform wheels |

The *cheap* scientific fork has already been answered negatively at CPython3.11 by the source-exact hosted test. No new C branch or parser policy is justified by the current data; either find a truly different owner boundary with measurable general leverage or advance another independent CMPCT frontier. The most useful counterfactual from this activation is to verify source/ABI structural compatibility **before** investing in microbench gains.

## Memory negative from original raw receipt

The hosted independent worker recorded `rss_increment_kib=0` in **all 24 fresh subprocesses** for both methods (baseline and after run). This does **not** demonstrate zero allocations or equal peak memory; the process imported native CMPCT code and its high-water had already reached a larger value than these short index constructions. The memory metric is effectively **censored/uninformative** for this experiment. A separate local Python3.13 `tracemalloc` proxy observed a transient difference, but that instrumentation is not CPython3.11, installed, portable, or independently product-audited. No favorable memory claim is earned; the economic decision rests on noncensored wall/CPU medians and the strict semantic incompatibilities. A different implementation would need genuine fresh-process peak/RSS accounting before promotion.
