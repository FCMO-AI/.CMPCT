# O196 / O196b — actual native CDC execution boundary: hosted results

Date: 2026-10-26 UTC  
State: SCIENTIFIC DECISION COMPLETE, product/release promotion NOT earned.  
Owner: O185 existing Draft [PR #516](https://github.com/FCMO-AI/.CMPCT/pull/516), not a new competing implementation.

## Prediction before measurement

O196's prospective admission claim was committed at `dbb99f6d3bb51bbad12171cf548e336de7b31062`, **before** new probe source or workflow. O196b's second-stage claim was committed at `cc38684c6b19844595c4002c6b1b5dcdcbc97687`, **before** its two-arm instrument or workflow. Both predicted that the optional standalone native C chunker was **not loaded** in normal packaging, though its original source still passes independent compilation/ThreadSanitizer.

The precise source seam is `src/cmpct/codec.py` loading only sibling `libcmpct_cdc.so`, with fixed-256KiB fallback when missing; `pyproject.toml` packages the Rust `cmpct_core` cdylib, not the separate optional C helper. User-facing `README.md` documents explicitly compiling the latter into `src/cmpct/libcmpct_cdc.so`.

## 1. Original clean-wheel experiment — confirmed

Preregistered **O196 [GitHub Actions #40346318252](https://github.com/FCMO-AI/.CMPCT/actions/runs/40346318252)** on exact HEAD `75cd1a7c7daaab6982a42043166481a24b3fe7df`: the result-bearing job fully executed and succeeded. Original [raw artifact #12661217736](https://github.com/FCMO-AI/.CMPCT/actions/runs/40346318252/artifacts/12661217736), digest `sha256:d523166568b1c06e92fac64fef4e6e2e2639497f434538ffea6b52b17f3114cb`. Wheel SHA256 `b9e7ef17211ee38bfbf209e54c258381d674eab9918216d80fe20e1ab875bb66`.

The normal isolated Linux/Python 3.11 wheel installed into a new venv outside checkout contains `cmpct_core.cpython-311-x86_64-linux-gnu.so` but **no** `libcmpct_cdc.so`. Fresh import produced `codec._cdc is None`. For exact deterministic 2,240,000 bytes (SHA256 `ccaf863d7df1a1a4fd09996cd807afa6a1d7d1c32ebb1915d677d02bc9062330`), default `cdc_chunks` produced eight 262,144-byte units plus a 142,848-byte tail (nine units total). Explicit positive control compiled the exact checked-in native C Git blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364`, injected it into a **separate experiment process only**, and observed native chunks of `[659638, 604762, 975600]` bytes; the direct C ABI returned the exact same boundaries, and reassembly was byte-exact.

**Observed decision:** `O196_DECISION=DEFAULT_WHEEL_CDC_HELPER_ABSENT`, `O196_NATIVE_INJECTION_POSITIVE_CONTROL=PASS`. This is source-authenticated packaging/admission research, **not** a speed win or claim that the released wheel includes the native fix.

## 2. Actual official ABBA source-path setup — independently confirmed

Preregistered O196b [GitHub Actions #40347199519](https://github.com/FCMO-AI/.CMPCT/actions/runs/40347199519), exact HEAD `4a86982c9a522699b3010b3401a703554d1d7659`, **all result-bearing job steps SUCCESS**, [raw artifact #12661598342](https://github.com/FCMO-AI/.CMPCT/actions/runs/40347199519/artifacts/12661598342), digest `sha256:96c4c2ff7a3fe311bc253f9456aeafc23a65e3164bd7cddf175638b175670d12`.

The experiment replicated the official ABBA direct-base native Rust materialization and candidate ordinary `pip install -e .`, including actual distinct source-path imports `PYTHONPATH=/tmp/o196b-direct-base/src` and `PYTHONPATH=<candidate-checkout>/src`. Base source was genuine `62792a7fc61b033b306b4445c337ed123946514d`; candidate source `4a86982c9a522699b3010b3401a703554d1d7659`. Their `src/cmpct/codec.py` SHA256 matched `6f4836ef42332e220ea44a40be523dee0f7e7f569327c3b96c292d3f281ddc07`. Both loaded their own correct source modules, had **no sibling native C helper and `_cdc is None`** and, on the same exact 2.24MiB input, independently emitted identical fixed `[262144 × 8, 142848]` segmentation with exact reconstruction.

**Observed decision:** `O196B_DECISION=ABBA_PATHS_BOTH_CDC_ABSENT` and `O196B_EXACT_SOURCE_PATH_AND_REASSEMBLY=PASS`. The original C-source patch therefore does not participate in **either** ordinary measured source-path arm under the source-exact reproduced official harness setup. Any claim of speedup/slowdown *caused by executing the modified CDC C function* in those ABBA runs is unsupported. This does not prove the host-level cause of measured timing variation.

## 3. Preserve original performance negatives, do not promote

The earlier O185 performance receipts remain unchanged:
- first original implementation attempt [#40331357435](https://github.com/FCMO-AI/.CMPCT/actions/runs/40331357435) on `5f4ff924c936244054800945fd1eb67f93acfc5d`, AMD: **FAIL**, binary/library/create 111.070→117.500ms (+5.79%, +6.429ms);
- separately preregistered same-source second attempt on Intel: **PASS**, 154.904→154.482ms (−0.27%); different CPU, so cannot pool one-machine results;
- newly completed true four-round [ABBA #40340587167](https://github.com/FCMO-AI/.CMPCT/actions/runs/40340587167) on `7b115f39aed095fe0273f906c5bd42db66e156f5`: **FAIL**, nested/CLI/create 64.118→67.353ms (+5.05%, +3.235ms), 1 confirmed timing red, **0 deterministic archive-size reds**, artifact #12660305775.

The latest complete original-head scientific/general/native/fuzz/test CI for `7b115f39...` passed, including the strengthened Builder native-positive regression, but **does not supersede the official RED**. Both O196 experiments are research-only; on their later commits administrative green performance gates may skip benchmarking. None earn release, packaging, promotion or speed claims. Keep O175 genuine-Reader warm-scan tradeoff (~−14.99% peak RSS, +25.61% second-scan wall) as inherited regression debt.

## Scientific disposition and cheapest next action

**Hypothesis confirmed for tested Linux wheel and official ABBA source-path setup:** optional C native CDC is not admitted by default. Positive injected native C remains a distinct, externally built opt-in path and its original concurrency fix is meaningful **for that opt-in usage**, not an established default distribution improvement.

**Counterfactual, prospectively detectable:** before spending expensive ABBA compute attributing a performance change to an optional source artifact, inspect the actually executed module and helper identity in **both arms**; a cheap authenticated import/ABI oracle would have narrowed the causal question immediately. This is a local methodological lesson; it does NOT modify global discovery policy without repeated durable evidence.

**Next highest-value option** is a decision about whether optional C CDC deserves productization at all: measure real workloads with helper admitted versus fixed fallback (full stored bytes, CPU/wall, RSS, temp I/O, update/dedup value, cross-platform wheel/loader semantics) **only if** credible product leverage exceeds new packaging/dependency cost. Otherwise retain the original native race patch as opt-in safety and stop treating inactive C source as the owner of ordinary ABBA noise. Separately diagnose the persistent official performance RED without changing thresholds, workload, comparator or semantic boundary. No product code, on-disk format, reader, release version or frozen experiment was changed in O196/O196b.

**quality-ratchet:** preserve code-owner source and all published adverse timings while reducing runtime causal attribution uncertainty.  
**disproof:** evidence from a comparable **ordinary** wheel/official installed execution where `_cdc` loads C must reopen and narrow the model, not be ignored.
