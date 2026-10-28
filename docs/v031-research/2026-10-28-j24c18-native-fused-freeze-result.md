# J24C18 result — native per-item ref freezing is not a viable rehabilitation

Date: 2026-10-28 UTC. **DRAFT RESEARCH ONLY. No product change, promotion, release, version or format mutation.** Parent source [#676](https://github.com/FCMO-AI/.CMPCT/pull/676) exact `3b6a73f9205f40f11124cd9ff332407e52cebb93`, original native C blob `6c925d50c610681812b5698776ea7a9edfa0bcfc`; preregistration first child commit `3f77430f70a56df0d0431fe6d0fc11839a6c68d3`. Independent [PR #679](https://github.com/FCMO-AI/.CMPCT/pull/679), no changes to parent #676 or discovery state.

## Decision

**REJECT the bounded C-per-item fused immutable-tuple copy mechanism** as a way to rehabilitate the J24C17 Reader opening/Q1 regression. On the prospectively required 65k and 262k exact-proven reference cases, the new C implementation failed to provide the required >=5% median full scan+freeze improvement on every host; it usually regressed. The same complete signed logical proof, stride-256 search checkpoint construction, frozen reference identities, and invalid-input rejection survive. This is a definitive negative **for this mechanism at component tier**, not an argument against immutability or all parser/ownership changes. The first J24C17 mutation fix remains a separately preserved narrow positive, with +13–24% product session cost on #676's two source-exact A/B courts.

## Controls and measured code

The experimental C file `research/j24c18_fused_copy_component.c` reproduces the source-exact existing stable-ABI `scan_refs_index` unchanged (only its *isolated module name* differs). A new method `scan_refs_index_copy` returns two objects: the identical stride-256 prefix tuple and an immutable tuple of the already validated reference objects, constructed with `Py_INCREF` and `PyTuple_SetItem` per element. **Stronger simpler control** calls unchanged `scan_refs_index` then CPython's optimized `tuple(refs)`. The Python runner never imports the CMPCT production Reader.

Both use identical built-in lists, deterministic 4-owner or 256-owner synthetic physical descriptors (including zero and unequal logical lengths), 65,536 / 262,144 / 1,048,576 references, same checks, exact reconstructed Python reference/checkpoint digests, and five adversarial inputs. Each of three hosts ran 9 independent balanced A/B subprocess pairs for **four cases**: 72 raw process observations per host, 216 total. Timed wall and CPU include complete native proof **plus** tuple freeze, not process startup; worker preparation and independent verification are outside the timed section. The independent stdlib referee rechecked every raw pairing and digest, all medians, and rejected seven forged receipts per host.

## Repeated exact-source evidence

First hosted [run #40700673098](https://github.com/FCMO-AI/.CMPCT/actions/runs/40700673098) at `c1e592a35bb14f9decf512d3cc4154cb29e1bfa0`:
- Ubuntu and macOS: hosted independent referee SUCCESS with `REJECT_C_PER_ITEM_FUSED_FREEZE_ROUTE`.
- Windows: all 72 fresh raw workers finished and emitted logically valid wall results, but **external referee failed** because Windows' sub-tick process CPU yielded zeros and the instrument incorrectly required strictly positive CPU. **Do not count its failed referee as proof of product failure or a fully audited win.** No scanner/product/benchmark input was changed to address this.
- Raw artifact identities: Ubuntu id `12821392724`, SHA-256 `ad38504aafb350cf18664f6e3cd95234c99a7fe567a647d8b40061e3b00f482f`; macOS id `12821217624`, SHA-256 `89fe4877c2633463b67228e10b9b8c4dd3f44f3d6745048c38e21f3e9dcfed3c`; Windows (referee-failed) id `12822585270`, SHA-256 `6949e0b5b3b2228cecb1c6155f572467d328824e438ea1b35f4acccec9b6a4a9`.

The only subsequent change was in the **separate second-root auditor** to accept recorded zero CPU but classify a zero-median CPU ratio as `UNMEASURABLE` and forbid a pass credit. The prospective wall, integrity, resource criteria, input corpus and native C source are unchanged. Final exact-code [run #40701073699](https://github.com/FCMO-AI/.CMPCT/actions/runs/40701073699) at `0203a3481df588078f276d056caa3b2a73ed5dcb` ended **SUCCESS on Ubuntu, macOS and Windows**, all referees `REJECT_C_PER_ITEM_FUSED_FREEZE_ROUTE`, all 7/7 forged receipts rejected on each host. This is a successfully *measured negative*, not a product success.

| Host | 65,536 refs · control/fused ms | Fused/control | 262,144 refs · control/fused ms | Fused/control | 1,048,576 refs ratio | 262k × 256 owners ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ubuntu | 1.621 / 1.845 | **1.1382×** | 6.416 / 7.361 | **1.1473×** | 1.1508× | 1.1815× |
| macOS | 1.032 / 1.170 | **1.1339×** | 4.480 / 4.442 | **0.9915×** | 1.0199× | 1.0954× |
| Windows | 1.338 / 1.437 | **1.0741×** | 5.333 / 5.779 | **1.0836×** | 1.0957× | 1.1267× |

Greater-than-1 ratio means **slower**. The final macOS 262k minor positive does **not** pass the >=5% improvement condition and conflicts with its earlier source-identical +7% regression, so no generic product gain can be claimed. Ubuntu's wall and CPU losses are consistently about 14–18% across these cases. In Windows, CPU observations have insufficient resolution for submillisecond work and must remain not measurable; RSS is `null` there. Available process HWM RSS differences on macOS/Linux are not real transient allocation peaks and cannot be substituted for an allocation profiler.

Final hosted artifacts: Ubuntu id `12820804379`, ZIP SHA-256 `a05e65b335936c6e6a6a781a8e70c7581dd449b4ceb262e38728ee4920175779`; macOS id `12820939173`, ZIP SHA-256 `75966c3268f52685ec10cae729738543bba09915c8309731f1482cf40b1792f9`; Windows id `12822110720`, ZIP SHA-256 `6fd9069e4290084896f1f87b236da91f062de4955e4e51369672163847a523d8`. Raw receipts and per-host referee summaries are attached to run #40701073699. Host checkouts may materialize equivalent canonical source with CRLF on Windows and LF elsewhere; the referee fingerprints each exact built source locally and never conflates host byte hashes with source identities.

## Lower-rung *new-frame* oracle: pre-owned immutable parse

Separately (not prospective J24C18 results, no hosted or CMPCT installed control), CPython 3.13/Linux with msgpack 1.1.2 explored the very different ownership boundary of **constructing tuples during MessagePack decoding**, then converting only outer r24 structures back into mutable lists. Twenty-seven alternated local measurements per case used identical deterministic MessagePack bytes, and validated byte-identical reserialization of reconstructed trees. Tuple-at-decode + outer-list restoration versus normal list decode then post-copy tuple medians:

| Refs / owners | List-decode + postproof tuple (ms) | Tuple-decode + outer thaw (ms) | Relative |
| --- | ---: | ---: | ---: |
| 65,536 / 4 | 0.464 | 0.370 | 0.797× |
| 262,144 / 4 | 2.539 | 1.517 | 0.598× |
| 1,048,576 / 4 | 10.252 | 6.035 | 0.589× |
| 262,144 / 256 | 3.572 | 3.149 | 0.882× |

**Important: generous parser-only oracle, not a Reader performance improvement.** These timings omit the native proof entirely, real archive mmap/header validation, journal deltas, general index validation, other representation types, hostile inputs, original Reader's list-only native predicate and full product economics. Such broad `use_list=False` decoding **cannot be inserted into the current Reader safely**: `src/cmpct/validation.py` explicitly requires lists for S_CHUNKS/CDC/SPARSE and blob rows, `_apply_delta` mutates file/blob arrays and file rows, and the C extension checks `PyList_CheckExact`. A future schema-aware immutable-ref admission must change all relevant invariants and prove equivalence—mere parser speed headroom earns zero product credit.

## Counterfactual discriminator and completion

The cheapest **prospectively recognizable** negative was already observable in the local unpreregistered no-checkpoint pilot: per-item C tuple filling was 15–23% slower than native scan+optimized CPython tuple on 65k–1m refs. Because the pilot omitted stride checkpoint construction and ran only on one Python/host, the bounded independent hosted replication was justified. It confirmed the same directional cost and retired the exact mechanism without writing a new product implementation. This is a **local scientific-selection lesson**, not evidence sufficient to modify Discovery Engine doctrine. Do not recycle nearby per-item loops or threshold variations without different information.

**Next lowest-cost unclaimed question:** Can a schema-aware immutable parse representation retain r24 journal correctness and all native validator acceptance semantics *without* a second O(N) reference copy? Start with a hostile syntax/delta/typed-API compatibility falsifier, then a charged oracle and only afterward actual installed Reader economic tests; do not touch other owners' branches or replay source code into main. The prior #676 sealed mechanism remains a narrow integrity seed with explicit economic debt. No new release, merge, README version, physical format, benchmark threshold or `docs/discovery/STATE.json` mutation.
