# O228c result — explicit native CDC mode defeats fallback confound, not virtual-run product debt

**UTC 2026-10-27 · Research-only · prospective gate preserved.** The [O228c preregistration](2026-10-27-o228c-native-cdc-mode-prereg.md) was separately committed first (`fdac495666368c9e323203391a0bb772d4dd3c9a`), before the instrument (`02e86df2fb740dc67828b9ce5f2e891eafa997fe`), audit and hosted execution. The experiment did not modify Builder, Reader, decoder, CDC thresholds or any released format. An optional binary was compiled from unchanged canonical `native/cmpct_cdc.c` on the research runner, **not** installed as a shipping wheel feature.

## Original hosted evidence and custody

- [GitHub Actions O228c run #40534143700](https://github.com/FCMO-AI/.CMPCT/actions/runs/40534143700) — **SUCCESS** on Ubuntu 24.04/Python 3.12; artifact [#12747254478](https://github.com/FCMO-AI/.CMPCT/actions/runs/40534143700/artifacts/12747254478); actual tested PR merge HEAD `d3723116fcbb54fd8742acb153b7358ef110bfad` contains source branch commit `41348359cfd10ab2aaa25c83c114c56b4da2c224`.
- Git artifact ZIP SHA-256 `a67fe4cf4c46667f0efbf4cf3a352f1fe9aff4ee13cc7efcd82177723aed6a07`, confirmed against the original downloaded 7,322-byte ZIP, artifact service digest and member CRCs. Exact raw `o228c_raw.json` SHA-256 `aea464c9aa95eb20dee841f7bc81faa8988bc905a9f07efe521a986db76975ec`, independently compared with embedded checksums.
- Original C file Git blob `bf51984f6ca7dec5e5041aa9f8dcccbed75221da` / source SHA-256 `84e376be665ea648307ca2ff5430b7acc1eb79aa8d4480fd2cc6ff95d5de6d20`; compiled .so SHA-256 `2d2ee378fdd0f21d6eab340af722669cfcb5765aca5c446e30faa902ce57225c`. Runtime logs explicitly report loaded helper at `src/cmpct/libcmpct_cdc.so`.
- The runner's independent `o228c_native_cdc_mode_audit.py` returned **PASS**: six paired same-input profiles, 72 isolated unpack observations, two mode-identical Builder/Reader source checks and exact complete archive read/verify/range SHA controls. The test source and auditor are retained under `research/`. No attempt was made to modify the scientific decision after the run.

## Prospective O228c decision — negative

Native mode actually changed the chunk-length boundaries in **five** nonzero cases, satisfying the mode discrimination condition. The decision was `NO_NATIVE_BUILDER_TRANSFER_AT_16MIB`, not an invalid instrument and not a product win: **zero** nontrivial families reached the joint >=8-run / >=2x unpack-heap / nonpositive-index-byte-debt condition.

| Same 16-MiB source | Fixed-fallback refs / runs | Native refs / runs | Native hypothetical run-index delta (total archive) | Native unpack heap literal/runs |
|---|---:|---:|---:|---:|
| All-zero | 64 / 1 | 8 / 1 | -14 B | 1.176x |
| One-period high entropy | 64 / 64 | 17 / 3 | -10 B | 1.289x |
| Two-period high entropy | 64 / 64 | 24 / 24 | -2 B | 0.956x |
| Shifted high entropy | 64 / 64 | 17 / 3 | -10 B | 1.289x |
| Structured records | 64 / 64 | 8 / 8 | +6 B | 0.981x |
| Independent random | 64 / 64 | 29 / 29 | +6 B | 0.976x |

The original O228 262,144-reference synthetic memory benefit remains real **only as a synthetic research bound**. Genuine CDC_MIN=128 KiB and these authentic 16-MiB inputs produce much smaller reference arrays. O228/O228b/O228c do not earn a virtual-index grammar or new format revision.

## Important separate result — choosing a chunker is a different product frontier

Because both actual Builder variants share identical input bytes and the same Builder/Reader code, O228c additionally gives a **direct same-source full-archive comparison of the optional native chunker against fallback**. These are paired one-run measurements, not repeated performance benchmarks, and **not** evidence about the proposed virtual-run grammar:

| Corpus | Genuine fallback archive | Genuine native-CDC archive | Native size effect | Builder wall fallback → native |
|---|---:|---:|---:|---:|
| All-zero | 1,015 B | 1,072 B | +5.6% | 0.034 → 0.052 s |
| One-period | 1,049,818 B | 2,098,336 B | **+99.9%** | 0.038 → 0.055 s |
| Two-period | 2,098,714 B | 3,203,952 B | **+52.7%** | 0.042 → 0.057 s |
| Shifted | 16,782,978 B | 2,084,044 B | **-87.6%** | 0.104 → 0.058 s |
| Structured | 3,506 B | 3,640 B | +3.8% | 0.042 → 0.067 s |
| Independent | 16,782,972 B | 16,780,726 B | -0.013% | 0.103 → 0.098 s |

This conflict is strategically more important than index-run compression at this scale: native CDC restores roughly **14.0 MiB** on a shifted/repeated family where fallback loses alignment, yet it exports ~1.0–1.1 MiB on two aligned periodic families. The source-mode comparison is a **potential general chunking-selection/representation frontier**, not a universal win: do not simply enable native by default based on the shifted case, nor freeze fixed-only based on periodic cases. The existing native helper is optional and has an unrelated identified extreme-`size_t` correctness issue [#606](https://github.com/FCMO-AI/.CMPCT/issues/606); portability, hostile numeric bounds and ordinary wheels remain release debt.

### Cheapest next falsifier, not an implementation promise

Before full dual-encoding, study a generic bounded per-file sample/structural predictor (if any) for choosing fixed/native CDC **without** an expensive double-archive construction. The simpler strong control is the smaller of two *fully charged* authentic archives, explicitly labeled a gifted oracle. Evaluate on held-out insertion/deletion, periodic, incompressible, structured and adversarial data, including classifier false positives; account for all physical bytes, full Builder CPU/wall, cache/index, extract/read, peak RSS, and optional-binary/OS costs. Kill if prospective generic selection cannot approach the gifted bound without exporting more cost than it saves. The bound from [O228c zero-index analysis](2026-10-27-o228c-index-zero-upper-bound.md) still governs **index-only** mechanisms; it cannot rule out changing the physical chunker, whose effects dominate these observations.

## Quality / exact claim boundary

- Product code changes: **none**. On-disk revision-24 format unchanged. No new storage tags accepted.
- Verdict primary O228c: **negative**; native mode really differed, no two nontrivial run patterns met preregistration.
- Distinct result: opposite-signed, large *physical* archive effects of native chunker vs fallback in six generated same-input profiles; exploratory performance observations have only one process per Builder alternative.
- Original private/system data: none, sources generated deterministically. Native Linux experiment only; no Windows/macOS claim.
- Discovery Engine: original state reconciliation belongs to [PR #574](https://github.com/FCMO-AI/.CMPCT/pull/574), untouched. No evidence-backed general policy mutation. Separate PRs own Reader safety, extraction integrity and release gating.
- Best counterfactual: verify optional `_cdc` presence **before** interpreting `S_CDC` mode; run the zero-index bound before building new grammars; do not interpret a source-level semantic tag as proof of which chunker ran.
- **No merge / no release / no product performance credit.** Review original CI/source/results before any future intervention.