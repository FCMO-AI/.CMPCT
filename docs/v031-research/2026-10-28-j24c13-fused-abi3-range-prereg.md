# J24C13 — fused native admission and compact range checkpoints (preregistration)

Date: 2026-10-28 UTC
Status: **PREREGISTERED BEFORE PRODUCT OR EXPERIMENT IMPLEMENTATION**
Exact parent: PR #641 `a639570c1e9f9b36decae3893265be74a6d185b0`; released control `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0 / r24).
Scientific lineage: J24C12 PR #659 (released-vs-ABI3 negative), O221 PR #583 (separate eager/lazy Python checkpoint oracles), J24C10 #652 (uniform-only shortcut and early negative).

## Primary question
Can *fusing* the already-required ABI3 S_CHUNKS validation scan with construction of a **bounded in-memory checkpoint index** remove the per-range O(N) Python location walk, without making short sessions worse, requiring a second scan, weakening original strict admission or exporting material memory/dependency cost?

This is not a second O221 Python checkpoint implementation, nor uniform geometry special-casing. It changes **ownership**: the native pass already paid for at Reader open emits occasional exact prefix sums as a by-product. No separate index-build scan. The inherited validation and on-disk r24 grammar must remain unchanged.

## Baseline, alternate explanations and controls
- J24C12's three independent historical-on-source sessions at 262,144 refs measured ABI3 **+8.22% to +15.00% worse** than the published Reader; excess opening admission was ~4.3–5.0 ms, but six selective reads were ~49–51 ms. Compare all three Readers on the **same inputs and operations**.
- Stronger control: O221's stride 256 separate Python index had strong Q64 wins but Q1 5–9% losses and Q4 lazy failed its >=1.10× gate. C index fusion must beat or honestly lose to this lower-complexity path when measured.
- Alternative explanation: the Python loop is not dominant for heterogeneous actual data or C→Python index creation consumes more than it saves; multi-codec decode, archive startup, member mix, short reads and RSS may reverse synthetic RAW outcomes.
- Avoid false positive: run authentic installed CMPCT wheels and exact signed r24 inputs. Fixed and heterogeneous reference lengths, Q1/Q6/Q64, early/mid/late/random ranges, invalid structs, Python 3.10/no-native fallback. Do not call a pure in-process microbenchmark product evidence.

## Planned minimal mechanism
Add *optional* ABI3 exact-list positive-only proof returning compact checkpoints every 256 references while validating the **complete** member list, signed total and each physical blob descriptor. The Reader only installs those checkpoints on successful proof and uses bisect + original bounded per-chunk byte extraction. For short vectors (<512 references) keep the previous native proof with no index and no map entry. Extension unavailable, false/exception or unknown input -> unmodified strict Python validator and original selective walk. Never cache unsigned facts into archive, rely on pathname reopening, skip required header/canonical-path checks, or change source descriptor ownership.

## Prospective evidence / rejection
1. First rung: local ABI3 **instrument-only micro A/B** compares original native proof vs fused proof+index creation on deterministic 65,536/262,144 ref fixed and mixed lengths, exact full-sum check, and carries per-instance index bytes, CPU, wall and Python object carrying cost. This is **research evidence only**.
2. Second rung: installed same-archive exact-Reader A/B of released / ABI3 / fused (Q1/Q6/Q64; fresh process; CPU/wall/RSS; same signed inputs, Python interpreter/OS, startup separated), including per-phase open and ranges.
3. Candidate must: equal all returned bytes; reject/fallback safely on invalid/adversarial index, preserve all inherited hardening tests; at 262,144 refs for Q6 beat **released** Reader by >=5% and >=3 ms in both CPU and wall while improving over ABI3; at Q1 not regress vs ABI3 by both >=5% and >=3 ms; candidate extra RSS <=8MiB; no archive byte/format change. Any observed hard semantic violation is a kill. Failure to achieve the joint economics means a protected negative research seed, **not** promotion. One platform cannot grant cross-platform product credit.
4. If runtime/build/host not available, preserve measured lower-rung evidence separately and report exact unavailable product proof, without calling it a pass.

## Concurrency/ownership
Independent J24C13 branch off exact #641 (do not update #641, #583, #652, #659 or shared STATE). Distinct question: **fused admission ownership** versus O221's separate index and J24C10 uniform arithmetic. Do not copy competing product modifications or weaken frozen comparators. PR remains draft until three-host installed source-exact evidence and full inherited product gates complete.

## Decision rule
If fused native checkpoint production does not materially improve Q6 **against released**, stop nearby Python threshold gardening and return to representation/access ownership. Retain the baseline as legitimate winner and preserve negatives.
