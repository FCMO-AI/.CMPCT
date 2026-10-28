# J24C11 — prospective causal falsifier for J24C10 no-op negative controls

Date: 2026-10-28 UTC. Status: **PREREGISTERED before any J24C11 instrument/workflow implementation.** Research/evidence only, no product modification, no promotion authority.

## Current evidence and exact control

Parent [J24C10 PR #652](https://github.com/FCMO-AI/.CMPCT/pull/652) at `c93014c4801a145879206e40ff760a86becb8727` preserves exact-head [run #40641105382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382) and an independently recalculated failure: the same installed ABI3 Reader has >=3.61x late uniform range speedup, but macOS +15.85% early Q=1 (65,536 one-owner) and +5.94% ragged Q=1 (262,144 refs) exceed frozen 5% loss veto; Windows CPU single-range clock was unresolved. **J24C10 is NOT PROMOTABLE and cannot be retrospectively rescued by this study.**

Static path analysis suggests neither negative arm invokes the new C proof: early start=12 fails `start*2>=size`; irregular 262,144-ref [4,1,2] repeating fails the cheap `a==mid==prelast` prefilter. If true, their negative times are not causally explained by the proof itself. The alternative is that changing the optional module setting or an unobserved path changes timing or semantics even when the proof itself is not called.

## Primary question and preregistered hypotheses

**Can instrumented same-installed-wheel negative-control reads demonstrate identical byte/error behavior and zero native-stride proof dispatch in BOTH J24C10 arms, while making true per-read CPU/wall observable by aggregating many actual calls without process startup timing?**

- H1/path equivalence: zero calls to `reader.native_uniform_stride` on 65,536 one-owner **early** and 262,144 ragged **late** in both controls, same SHA of every returned answer and same normalized errors. A single observed proof call, changed digest/exception, or source mismatch **FALSIFIES H1**.
- H2/measurement: aggregate per-arm CPU and wall times over **8192 early calls** and **16 ragged calls**; repeat **8 A/B/B/A cycles** in one process with the same installed wheel and signed archive. Windows `time.process_time_ns` must become strictly positive for each arm's **aggregate**, or H2 is **INCOMPLETE**. Never interpret single-call CPU=0 as no CPU work. This is a different workload/evidence rung; **no numeric no-regression benchmark claim** and no replacement for the frozen 5% Q=1 gate.
- H3/observability: collect raw per-arm cycle wall/CPU, path-spy calls, output SHA, Reader source SHA, actual installed package path, input wire SHA and source commit; preserve all outcomes even if the sign of the median remains unfavorable. No select-after-observation or threshold changes.

## Controls and causal alternatives

Two arms use the **identical installed candidate Reader** and identical signed r24 wire, in one process and one Reader instance per fixture. `strict` temporarily sets only `cmpct._chunk_admission._uniform_stride=None`; `witness` restores the original native reference. Original `native_chunk_ok` admission remains untouched. Instrument `cmpct.reader.native_uniform_stride` with the same Python counting proxy for both arms, without changing `read_range`; verify zero calls. No replacement archive bytes or different Python wheels. Warm both arms symmetrically before timing; alternate ABBA group ordering across eight cycles. All results checked against the independently constructed logical slice, not against the Reader itself.

The minimum physically meaningful duration for Windows CPU is unknown in advance; preregistered Q is fixed above and not tuned after result. Any zero/unsupported reading remains `INCOMPLETE`, not PASS. Separate cold-open from these repeated-read results. Do not call repeated-read latency a whole product improvement.

## Exact evidence rung and exclusions

Run installed wheel on Ubuntu24.04, macOS14, Windows2022, Python3.11, independent SHA/source checks, pytest inherited signed controls if cheap, and a standalone referee that recomputes all group medians and checks answer/source/wire identities, negative-path zero-spy and raw data completeness. This is a **causal instrumentation / evidence-quality** study; no Builder/Reader/C/format/version/release source edit. No CI green is scientific success if the contract is violated.

A positive H1 **rules out the native proof itself** as the cause of Q=1 negative controls under the exercised code paths; it does NOT turn original Q=1 negative results green, prove jitter rather than an unrelated cache/OS effect, or allow promotion. If H1 is false, file a material correctness/dispatch defect, preserve raw counterexample, and do not merge. If measured aggregate CPU is missing on Windows, narrow conclusion instead of weakening the question.

## Opportunity and disposition

Prefer this cheap, independently rooted runtime spy and aggregate-clock discriminator over another native C threshold variant, generic eager indexing, or a full product benchmark while causal interpretation remains unresolved. Once this fork is decided, **stop investigating equivalent Q=1 microcontrols**; direct attention to product-wide nonuniform selective I/O, safe admission/ownership alternatives, native packaging or representation-level authenticated proof. O221b Q4 negative remains independent and unchanged; #641/#583/#574 owner branches and their authority remain untouched. `docs/discovery/STATE.json` not changed.

## Safety and immutable boundaries

Read-only tests, source-constant and signed bytes. No user data, secrets, internal corpora, changed evaluator, format semantics, release promotion, or weakened existing hostile tests. A working native witness remains optional and all error/fallback paths are inherited without editing the product. Any unmeasured platform/condition is explicitly `UNMEASURED`.
