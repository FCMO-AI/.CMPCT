# J24G34 — source-bound compaction composition: initial result and contradictory A/B

Date observed: 2026-10-29 UTC. **Status: EVIDENCE CONFLICT; PROMOTION BLOCKED.** This is a product-candidate experiment, not released product evidence. The preregistration at `39f7ebd960a7d66c6bc45ea61af95d578b41cd8a` predates implementation and all hosted results.

## Exact source and independent owners

- Initial measured candidate PR [#738](https://github.com/FCMO-AI/.CMPCT/pull/738) HEAD `f7e3a9c5e8fa07241cd8b813fb78e14a874ec7f6`; parent #735 `82e90eca58ed0580df191378947004e4061d53c3`.
- Candidate Reader Git blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`: exact, unchanged [#620](https://github.com/FCMO-AI/.CMPCT/pull/620) donor. Historical control Reader `b2b7774c13a5c8235ff89786d171b7ea3ff20710`: exact #735/#613. Builder `387192edd783e02bf7a44a38945214bf9d6c183e` and transactions `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264` unchanged.
- Hosted [Actions #40835307369](https://github.com/FCMO-AI/.CMPCT/actions/runs/40835307369): Ubuntu, macOS, Windows **unmodified donor hostile tests PASS**; Ubuntu actual installed-product source/owner compaction court passes. Full workflow **FAILURE** due secondary A/B assertion, not a product correctness failure. Raw original [artifact #12879653864](https://github.com/FCMO-AI/.CMPCT/actions/runs/40835307369/artifacts/12879653864), GitHub-reported ZIP SHA-256 `0e942bfd5c256110448bdeee1468c8a4424ef291a2df5b87360b9beea46555cb`.

## Test 1: candidate absolute bounded-memory acceptance (positive, narrow)

The new 2MiB/128MiB regular sparse owner ± true hardlink candidate court passed its prospective thresholds. For 128MiB the conservative alias-minus-owner RSS increase was **0 KiB** with all candidate alias runs below 64MiB; source/output indexed rows, member SHA, metadata and physical hardlink topology matched, genuine appended journal compacted away, original source bytes unchanged, repeated output physical hashes identical. This supports **candidate bounded-memory feasibility under the examined topology** only.

## Test 2: stronger same-source A/B falsifies attribution

The new independent-venv A/B/B/A test reused the **same physical 128MiB owner+hardlink archive**, source SHA-256 `10afabd4780342bf7fe14a6b3ec4952bb7c6c362ac20f81048e99efbe7e1d979`, 1,510-byte compressed source, 1,342-byte identical output for all four runs; exact physical output SHA `85a1f2babe540f4b98b579c7e4f25841cb47108f4fb3f92c73642f6579bea2db`.

| Trial | Interpreter intended | Peak RSS KiB | CPU ms | Wall ms |
|---|---|---:|---:|---:|
| A0 | historical #735 `b2b7774c...` | 25,220 | 430.805 | 432.846 |
| B1 | candidate #620 `f2bf7e5c...` | 25,052 | 429.631 | 430.064 |
| B2 | candidate #620 `f2bf7e5c...` | 25,276 | 429.672 | 430.135 |
| A3 | historical #735 `b2b7774c...` | 25,208 | 429.762 | 430.548 |

Conservative *observed* saving = min(historical peak) - max(candidate peak) = **-68 KiB**, hence the preregistered >=64MiB saving condition is **NOT MET**. The test correctly failed and preserved the receipts; do not call it green. This contradicts the original [#737](https://github.com/FCMO-AI/.CMPCT/pull/737) topology perturbation, which under the same historical Reader Git blob reported 285,844/285,828 KiB for alias and 25,580/25,580 KiB owner-only, +254.148MiB. **The two scientific experiments did not use byte-identical source archives** (historical #737 128MiB alias SHA `b7980f928eac5dac299c651c83736fab105e92f545499a7ca6be1290cac077cf` versus this run `10afabd...`). No causal mechanism or gain may be attributed to this composition until the discrepancy is explained with exact interpreter provenance and strict same-wire controls.

## Root-cause fork and instrument change

The first ABBA script labelled A/B by venv path and expected Reader blob but **did not actually inspect the installed Reader imported inside each child**. It is possible that Python path/source import selection erased the true A/B contrast. That is an instrument ownership gap, not an excuse to relabel baseline. Another possibility is a reproducible physical-source/metadata-sensitive difference, different environment, or a genuine no-gain result.

Following the initial negative, without changing thresholds or original historical #737 or frozen tests, the **new distinct** J24G34 positive court and ABBA now compute actual imported Reader Git object hash in each child and reject source mismatch before timing. The updated CI will differentiate source-custody failure, verified same-wire false gain, and genuine restored contrast. The historical run remains FAILED in GitHub and in this result file.

If verified provenance holds and both A/B engines are equally low-RSS on the same original physical archive, **narrow/retire J24G34 as a memory-improvement claim**, investigate whether source topology/metadata or runtime behavior controls the historical #737 difference, and preserve the existing #620 semantic strength without attributing a new compaction savings number. If custody fails, repair only the instrument and rerun unchanged product/hard-limit controls. This is not admission-threshold gardening.

## Independent blockers and scope

- The original #735 historical source-locked workflow necessarily fails when the Reader blob changes; do not rewrite it or claim historical green. New court is a different new-code positive route.
- #723/#726 stage-sibling rename/rebind safety is independently RED and blocks promotion, irrespective of RSS.
- Full product size/create/extract/read/CPU/memory/temp I/O, Linux + Windows + macOS compaction, broader graphs and complete same-runner release parity remain open; administrative performance SUCCESS with substantive SKIPPED has no product credit.
- No change to original #737 negative results, #620 donor, Builder/transactions, native format r24, main v0.30.0, release gates or shared Discovery STATE.json (#574 ownership).

**Discovery decision:** Initial composition result is mixed and **A/B contradictory**, not a product improvement. Independent same-source A/B was prospectively the stronger control; it prevented promoting a coincidental or incorrectly sourced RSS improvement. Rooted falsification now requires actual interpreter provenance rather than confidence from labels. No repeated, causal evidence yet earns a change to the Discovery Engine policy.

## Append-only correction: venv symlink root cause isolated (2026-10-29 UTC)

New result-bearing [Actions #40836084142](https://github.com/FCMO-AI/.CMPCT/actions/runs/40836084142) source `b2a23ef8271966613ab4b8213462a2cf4f27da1c` made **the actual imported Reader Git blob inside every fresh child** a mandatory assertion. Original donor hostile tests passed three-host; candidate genuine installed Linux physical compaction passed. The same-wire ABBA correctly **failed earlier**, now at exact A0 source provenance:

`AssertionError: ('samewire historical/candidate Reader provenance mismatch', '/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/cmpct/reader.py', 'f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f', 'b2b7774c13a5c8235ff89786d171b7ea3ff20710')`.

The cause is **the ABBA runner code itself**: `Path(os.environ["J24G34_BASE_PYTHON"]).resolve()` dereferences the virtualenv's Python *symlink* to the global Python executable. Both supposedly separate A/B subprocesses actually ran the **globally installed candidate**; their matching ~25MiB RSS and ~430ms timings were never valid historical vs candidate performance evidence. This reconciles the artificial no-gain observation with the larger original #737 historical negative without claiming an original-byte-identical replication. The tool was faulty; there is no evidence of a new Reader behavior regression from that false differential.

An instrument-only correction `ec55cef6d19de01cb34d423f98b87de24e163351` replaces `.resolve()` with `.absolute()` (preserves venv entry point), asserts the exact venv `pyvenv.cfg`, and keeps the independent in-child actual Reader Git blob assertion. **No threshold, test corpus, prior receipt, source Reader, or original historical evaluator was changed.** The previous two failed same-wire workflows and source-custody contradiction remain recorded; no A/B improvement is claimed until corrected exact-head run finishes. The prospective winning threshold is still min(historical RSS)-max(candidate RSS) >=64MiB and candidate <64MiB; if a truly historical Reader fails this comparison the hypothesis must be narrowed or rejected.

This is a *specific, prospectively recognizable implementation lesson* about venv symlink identity and per-child source custody, not broad evidence for rewriting the Discovery Engine. It also explains why merely checking Git checkout SHA at workflow setup was insufficient to authenticate the actual Reader used by subprocess benchmark arms. Preserve this class in future source-exact A/B courts via a local per-child import-blob assertion.

## Final source-attested same-wire positive result (2026-10-29 UTC)

**Decision changed to `COMPOSITION_SAME_WIRE_MEMORY_GAIN_REPLICATED` for this narrow experiment.** The previously recorded first incorrect A/B failure and source-provenance failure remain scientifically meaningful instrument negatives above. The fixed source-attested exact-head [GitHub Actions #40836438107](https://github.com/FCMO-AI/.CMPCT/actions/runs/40836438107), actual tested HEAD `8d58bf080f00facdf09e80af154ec117c8d79699`, completed **4/4 SUCCESS**: Ubuntu actual installed + exact owner/hardlink compaction and unchanged donor hostile tests in Ubuntu/macOS/Windows. GitHub original hosted artifact [#12881311009](https://github.com/FCMO-AI/.CMPCT/actions/runs/40836438107/artifacts/12881311009), provider ZIP SHA-256 `899d32393c8a33cf4ef56985c0f12aa5add906588173607203034229a57cc3a0`.

The original 128MiB **same physical source input** was used in all four A/B/B/A fresh subprocesses: source 1,510 bytes, SHA-256 `e0361493d58b2c3a01bc23bc8564f1e31aa22496a9ef680fc57fe2d306dda997`; each physical compacted output 1,342 bytes, identical SHA-256 `7d0d577d65ab506a32d997f6da4a89ad5ef68683b41dbd9541cc0fcf1ccbefee`; source unchanged, indexed metadata, hardlink topology, per-member exact logical hashes, CRC/SHA and journal removal verified. **Each child explicitly authenticated the Reader actually imported in its interpreter**: A = historical Git blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`, B = existing #620 donor `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`. The prior venv symlink substitution is fixed, not rationalized.

| Same physical 128MiB source trial | Reader | RSS peak KiB | CPU ms | Wall ms |
|---|---|---:|---:|---:|
| A0 | #735 historical | 285,952 | 822.977 | 823.700 |
| B1 | #738 #620-donor | 25,516 | 378.625 | 379.009 |
| B2 | #738 #620-donor | 25,524 | 378.436 | 379.024 |
| A3 | #735 historical | 286,336 | 822.450 | 822.972 |

**Conservative peak RSS gain** = min(A) − max(B) = `285,952 − 25,524 = 260,428 KiB = 254.32421875 MiB`. Both B executions satisfy the preregistered **<64MiB peak** ceiling, and the candidate-only alias-minus-owner delta remained **0KiB** on the separate topology experiment (below 32MiB preregistered ceiling). CPU/wall reductions in these four same-host fresh-process trials are narrow and condition-specific, **not** an official general benchmark or release credit. Every verified physical output byte was equal between historical and candidate; no size overhead on this archived case.

**Scientific promotion boundary:** For genuine r24 128MiB sparse owner+one real hardlink alias under private journal compaction, replacing only the existing #613 Reader with exactly #620's proven bounded hardlink Reader **does** prevent the observed materialization cost in the verified source-attested runner. This independently supports the earlier topology negative #737 and falsifies the apparent no-gain result from the badly launched A/B. It does *not* prove arbitrary hardlink graph or multi-platform compaction resource bounds. It cannot promote while the #726 stage-name/custody vulnerability, inherited source-locked historical court failure, full general CI/fingerprint gates, broad parity, recovery, input/staging I/O and cross-platform compaction remain unresolved.

**Counterfactual/prospective lesson:** The missing `pyvenv.cfg` plus direct in-child imported Reader blob attestation was the cheapest prospective discriminator; simply calling `Path.resolve()` on a venv Python executable symlink systematically destroyed A/B source identity. Keep child-import provenance mandatory in future causal cross-version trials, without weakening evaluator thresholds or editing original evidence. This is a local instrumentation rule, not a proven global Discovery Engine policy change. Shared `STATE.json` still belongs to #574.
