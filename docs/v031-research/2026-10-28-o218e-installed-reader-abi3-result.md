# O218e — Whole-installed-Reader stable-ABI economics, observed scientific result

**Disposition: `ABI3_FULL_READER_STRONG_HOST_PASS` in six separate platform/interpreter cells, with independent off-workflow replay; RESEARCH ONLY. No product patch, merge, release, new revision, or v0.31 promotion authority.**

## Exact provenance and scientific boundary

- Published baseline `main@80c358f8824ec1b20d349c92ed94c898090969b0`: CMPCT v0.30.0, physical revision 24; unchanged. Parent O218d PR #631 `3dd2e24b99eacf8f61b363278ff35e6ffb45b77b`.
- Preregistered hypotheses and disproof **before instrumentation** at `066c99caed747a0de62974f7be9f05e4c9a0ad5d` ([prospective dossier](2026-10-28-o218e-installed-reader-abi3-prereg.md)).
- Actual experiment source Git HEAD: `57f07c0064a9555f863d351b8a8d9379a244509f`; [GitHub Actions #40618979945](https://github.com/FCMO-AI/.CMPCT/actions/runs/40618979945) **SUCCESS**: Ubuntu 24.04, macOS 14 (arm64 hosted runner), Windows Server 2022, and independent cross-host job.
- Real *installed, non-editable CMPCT Reader* source Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`, identical to current owner PR #569 Reader source `c5e13bb3...`; validator `51c2849061f99a4afeddb7666956b24566ce7de0`; direct native C `a54f15181d9dbe667b9e8c9d52e927b09c80152f`. The ABI3 module is an **optional research wheel injected into the original validation entrypoint**; the branch does *not* modify the product Reader or constructor code.
- Source-pinned unchanged Builder-independent O215 signed-r24 archives: 65,536 and 262,144 references with one 4-byte physical owner, plus 65,536 references with 256 physical owners. Original fixed-chunk strict admission, 24 named malformed cases and 2,500 deterministic adversarial references were exercised against **both** native predicates; error diagnostics fell back to the original Python validator for anomalous inputs. The same physical archive bytes and SHA-256 identities were preserved across all arms/interpreters and all three OS runs.

## Direct measurements — full Reader constructor median, correct same-input arms

Five arms: original Python, safe O216 Python, original direct-macro C, same ABI3 wheel, and explicit unsafe `unguarded` timing floor (NOT a product choice). Each platform ran CPython 3.11 and 3.13 with exactly one `cp311-abi3` wheel compiled on 3.11 and imported unchanged on 3.13. The direct C control was compiled separately for each minor. Every cell has 3 archive profiles × 5 arms × 2 shuffled cycles × 2 fresh workers × 5 repeated constructor openings = **300 timed whole-Reader constructor observations per cell**, plus separately charged process startup; **360 fresh worker processes / 1,800 constructor observations total**.

| Host / Python | Safe O216 / ABI3 (65k/1 owner) | Safe O216 / ABI3 (262k/1 owner) | Safe O216 / ABI3 (65k/256 owners) | ABI3 / original direct C (262k/1 owner) |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 / 3.11 | 2.951× | 3.010× | 3.109× | 1.313× |
| Ubuntu 24.04 / 3.13 | 3.834× | 3.852× | 3.793× | 1.259× |
| macOS 14 / 3.11 | 3.344× | 3.299× | 3.372× | 1.277× |
| macOS 14 / 3.13 | 4.820× | 4.642× | 4.171× | 1.022× |
| Windows 2022 / 3.11 | 3.439× | 2.766× | 3.405× | 1.138× |
| Windows 2022 / 3.13 | 3.675× | 2.765× | 3.191× | 1.172× |

**All six cells satisfy the prospective strong whole-Reader threshold of safe-Python / ABI3 >=2.0× and ABI3/direct-C <=2.0× for both focus geometries.** Overall preregistered focus gain: **2.765×–4.820×**. Held-out 256-owner results remain positive. This is *not* the O218d 10–20× detached microbenchmark; there is no multiplication or conflation of speedups.

Actual 262k one-owner median constructor wall (milliseconds), by host/minor, **safe Python → ABI3 → direct C**:

| Host | Python 3.11 | Python 3.13 |
|---|---|---|
| Ubuntu | 24.466 → 8.127 → 6.192 | 32.675 → 8.483 → 6.736 |
| macOS | 19.052 → 5.775 → 4.522 | 31.287 → 6.740 → 6.592 |
| Windows | 30.565 → 11.051 → 9.710 | 33.342 → 12.057 → 10.288 |

One-time ABI3 wheel distribution size: **7,580 B Linux; 4,813 B macOS; 6,758 B Windows**. One-time wheel compile wall: **1.381 s / 2.028 s / 17.622 s**, respectively; kept outside the constructor measurements but charged. Direct non-ABI3 C binary and per-interpreter compile costs retained in raw receipts, not hidden. Original unsafe no-validation floor remains faster and is not a correct candidate. Linux process VmHWM was measured, with no material demonstrated reduction attributable to ABI3; macOS/Windows whole-process RSS was **not** measured. Windows CPU timer generated **306 real 0ns observations** across both interpreters, preserved as quantization rather than fabricated positive CPU timings. Cross-host absolute times must not be compared as identical hardware.

### Worker-to-worker robustness, before aggregate medians

A separate replay computed the intentionally **pessimistic unpaired** ratio `minimum of four safe-Python worker medians / maximum of four ABI3 worker medians` for each of the 12 prereg focus OS/minor/cardinality cells. The smallest was **2.650×** (Windows 2022, Python 3.11, 262,144 references), with all other ratios at least 2.714×. This does not confer a statistical confidence interval or represent a paired crossover probability: the worst-extreme calculation is only an independently rooted check that the published >=2.0× result is not solely an artifact of the median-of-medians choice. Keep the original prereg decision, which used medians across workers, unchanged.

## Separate fresh-process economics — startup and repeated opens matter

The raw `fresh_process_wall_ns` measure is **one newly started Python worker performing five repeated constructor calls**, including import/startup and worker setup; it is *not* a single cold-open measurement. Recomputed same-host safe-Python/ABI3 worker-process median ratio (65k one-owner / 262k one-owner):

| Runner | Python 3.11 | Python 3.13 |
|---|---|---|
| Ubuntu 24.04 | 1.27× / 1.76× | 1.41× / 2.03× |
| macOS 14 | 1.29× / 1.84× | 1.49× / 2.23× |
| Windows 2022 | 1.24× / 1.66× | 1.25× / 1.67× |

**Important negative:** these worker-process gains are materially lower than the pre-registered repeated-constructor-only gains for small profiles. The harness deliberately timed 5 opens per worker, so the process ratios cannot be advertised as the one-open cold-process benefit; any shipping native ABI3 module still owes a specifically pre-registered process-start/one-open crossover, optional-import penalty and multi-member mixed-index test. This counterfactual separator is inexpensive and prospective: for a one-open user workflow, import/startup may erase a meaningful share of the 2.8–4.8× constructor improvement, even though the five-open repeated-worker gains remain positive. No post-hoc relaxation of the constructor criterion occurred.

## Independent custody, reproducibility, negative controls

The workflow’s independent raw-worker referee recomputed median-of-worker-medians, exact wheel/binary and physical archive SHA-256, source/prereg ancestry, both native validators' semantics, and all six results; rejected **5/5 deliberately forged scientific receipts per host/minor**, or **30/30** across six cells. Separate cross-host job checked source/wheel identity within each OS, six expected results and the common semantic fingerprint. All four GitHub jobs succeeded.

Original workflow artifacts:
- [Ubuntu, id 12786372936](https://github.com/FCMO-AI/.CMPCT/actions/runs/40618979945/artifacts/12786372936)
- [macOS, id 12786700736](https://github.com/FCMO-AI/.CMPCT/actions/runs/40618979945/artifacts/12786700736)
- [Windows, id 12786611773](https://github.com/FCMO-AI/.CMPCT/actions/runs/40618979945/artifacts/12786611773)
- [Cross-host independent verdict, id 12786183437](https://github.com/FCMO-AI/.CMPCT/actions/runs/40618979945/artifacts/12786183437)

A **separate local off-workflow standard-library-only replay**, reading the four original downloaded artifacts without importing CMPCT, independently recalculated all six result medians and physical archive/wheel/binary SHA-256 identities, with decision `INDEPENDENT_AUDIT_PASS`. Its full JSON report SHA-256 is `64ca885304014d674bb36c5930415f7ef76f053d767a9ebabf6231301edb82ec`. This is complementary evidence, not another source implementation of Reader or a new product test; underlying hosted artifacts are the durable public source of truth.

## Strongest negative / limits / counterfactual

- The optional ABI3 scanner is **usually 2–33% slower** than direct macro C in the full Reader contexts (one observed ~1.5% faster), in line with but milder than O218d's micro-level ~1.8× limited-API tax. The ABI3 economy is a measured portability/packaging tradeoff, not absolute fastest native admission.
- The ABI3 route remains ~1.5–2.6× slower than the **unsafe** no-validation constructor floor; cannot equate that floor with a competing valid Reader.
- The Reader's validation of S_CHUNKS is an existing real bottleneck but #569's broader previously measured **27–28× high-reference open regression is NOT retired**, especially at mixed representation, index/recovery or policy boundaries. The result is a strong independent **candidate** for that owner's safe admission architecture, not a merged fix.
- No fully hostile signed-journal mutation/recovery, mixed S_CDC/S_SPARSE/PACK/VZIP, hardlink owner consistency, extraction inode safety, write/update cost, PyPy/ARM, packaging lifecycle, complete RSS accounting, official 15-row benchmark or release-parity was tested. Scope is full Reader constructor on three reference-rich S_CHUNKS geometries, in research mode.
- Counterfactual discriminator: the correct next step after O218d micro proof was not another micro scan; **the same-source whole Reader across two CPython minors** established a realistic advantage and quantified the stable-ABI tax before investing in optional shipping. A prospective future policy change is **not** earned; repository Discovery STATE remains owned by #574 and untouched.
- Generic General Tests and release/evidence gates are independent; **the scoped science workflow SUCCESS is not blanket CI green or release eligibility**. Engineering Evidence initially failed because the PR description did not have a literal `## Evidence` header; fix PR dossier rather than weakening the evaluator.

## Next highest-value executable action

Submit the actual optional abi3 `scan_refs` to Reader #569's bounded fail-closed admission and its inherited prospective controls **only after source owner review**, while assessing whether the existing Rust native core could reuse validation work without adding a second dependency. Build the smallest same-source composed candidate with optional import/fallback, enforce original invalid-input type/message behavior, authenticated journal/recovery, and a full product/cold-open CPU/wall/RSS ABBA + release parity. If packaging/dependency or mixed-reference cost erases this gain, preserve the scientific seed and favor simpler direct C/Rust/proof redesign. **No merge or numeric release from O218e alone.**

**O218e state transition:** preregistered question answered positively at research/product-candidate economic level; code and branch remain Draft PR #635; published CMPCT and on-disk r24 unchanged. Product promotion credit = 0.
