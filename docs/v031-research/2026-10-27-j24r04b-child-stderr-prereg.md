# J24R04b — diagnostic-only transparent child failure (prospective correction)

**Observed at 2026-10-27 12:35 UTC, before change.** Exact-head J24R04 original hosted run [40504186935](https://github.com/FCMO-AI/.CMPCT/actions/runs/40504186935) completed three-host semantics 3/3 SUCCESS; the Ubuntu ABBA job stopped on its very **first original-baseline child subprocess** (E=1, round 0), leaving only `subprocess.CalledProcessError`. The unchanged original J24R01 instrument captures the child's stderr/stdout but does not print it when `check=True` fails. Therefore the cause is unobserved; classify as **evidence infrastructure failure, not Reader regression or performance result**.

## Hypothesis and smallest next action
Preserve the original J24R01 script, all frozen inputs, ABBA order, process boundaries, cost metrics and release thresholds. Add a **parent-only** wrapper that intercepts `subprocess.run` and, only upon `CalledProcessError`, prints already-captured child stdout/stderr then re-raises. No modification to worker Python child, its imports, benchmark/hypothesis code or stopwatch. Same J24R04 test/controls must re-run from fresh exact HEAD; no credit from the failed first job. Preserve J24R04b and original failure records.

**Kill:** if no new diagnostic is observable, stop repeated blind reruns; investigate a materially different read route or script failure. If the diagnostic shows a real product fault, preserve it and debug without adapting the evaluator. Any new test code output is infrastructure evidence until raw ABBA and independent referee fully pass.
