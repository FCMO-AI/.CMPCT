# ONE-G0.2 Native Law Terminal Reader — result

Date: 2026-09-09
Experimental version: ONE-G0.2
Decision: **HOLD_NATIVE_LAW_TERMINAL_READER_V1**

## Exact authority

- scientific source: `bca3c86750245d7627e9ddc68b20344bdeb57739`
- workflow: `cmpct1-one-g02-native-law-terminal-reader`
- run: `34376831675`
- job: `102551647429`
- artifact: `10114300645`
- artifact zip digest: `sha256:859a296a87851d981075e26b44609d54f7bbcd9015b314091b2f527f3a180d6a`

The immediately preceding source `cfb21c8f3afa4a87586e39973327fd82fc4cdd53` is not scientific evidence: run `34376563627` stopped before tests/benchmark because its workflow referenced a nonexistent inherited test file. The benchmark and frozen gates were not changed when that lane was repaired.

## Mission / result

The experiment tested whether ordinary ONE terminal Law cones could execute as bounded native bulk commands (`COPY`, `FILL`, `ADD8_CONST`, `XOR_CONST`) after normal Program validation/preflight, without adding a stored opcode or reader discovery.

All inherited + hostile tests passed (`26 passed`). All 21 timing rows reconstructed byte-exact outputs with authenticated SHA-256 parity. Unsupported partial-root and nonconstant-Law topology continued to fail closed to the incumbent evaluator.

The mechanism is extremely strong on the intended Law rows but does not clear the full frozen integration gate.

### Productive Law CPU

- median native/reference CPU: **0.01206384x** (~82.89x faster)
- worst native/reference CPU: **0.02145059x** (~46.62x faster)
- semantic gate: PASS
- median Law CPU <=0.75x: PASS
- every Law row <=1.00x: PASS

Representative 512 KiB/version rows:

| family | reference CPU | native CPU | native/reference | native throughput |
|---|---:|---:|---:|---:|
| add8 | 219.477 ms | 1.853 ms | 0.008442x | 539.1 MiB/s |
| xor | 84.262 ms | 1.669 ms | 0.019806x | 598.5 MiB/s |
| add8 + crack | 218.465 ms | 1.312 ms | 0.006004x | 761.4 MiB/s |
| xor + crack | 83.621 ms | 1.782 ms | 0.021307x | 560.7 MiB/s |

Stored ONE Programs/wire were unchanged; this is execution strategy over the existing grammar.

### Control CPU — FAIL

- median control native/reference CPU: **1.119039x** (frozen max 1.10x)
- worst control native/reference CPU: **1.765531x** (frozen max 1.25x)

The worst row is the 512 KiB/version terminal Surprise/Fill Concat control. V1 routes no-Law controls through the new plan even though they have no expensive Law loop to eliminate. That carrying cost is unnecessary for canonical integration; a Law-presence gate can fail closed to the incumbent reader.

### Resource accounting — FAIL

- median Law native/reference-work ratio: **0.916721x** (frozen max 0.75x)
- exact add8/xor rows: **1.000x**
- crack rows: about **0.83334x**
- peak native temporary bytes: <= one requested root length on every row (PASS)

The cost owner is explicit in the implementation: the native path writes into a root-sized mutable `bytearray` and then freezes it with `bytes(sink)`. The native model charges that freeze as another complete root read+write (2x root bytes). This is avoidable data movement, not representation work. A causally different direct-final immutable root sink can remove that copy while keeping SHA verification and all Program semantics.

The plan also packs source slices during preparation. At 512 KiB/version exact relations, `packed_source_plan_bytes` is 1,048,576 B. Preparation is measured separately and remains visible; this state should not be silently treated as free.

## Referee decision

**HOLD**, without threshold changes.

The Law execution principle is strongly supported, but V1 is not the canonical reader shape because:

1. it pays native-plan overhead on inputs with no Law opportunity;
2. it performs an avoidable root-sized freeze copy after native execution;
3. selective authenticated ranges remain deliberately unsupported by this experiment and continue through the incumbent range evaluator.

## Causal rehabilitation

A V2 may reopen only by changing the cost mechanism, not the gate:

- use a cheap static Law-presence eligibility check and fall back to the incumbent reader for no-Law controls;
- write the native schedule directly into a newly allocated final immutable Python bytes object (or an equivalent one-allocation final root buffer), removing the modeled freeze read+write;
- keep root SHA-256 verification, Program validation/preflight, fail-closed topology, and all V1 CPU thresholds unchanged;
- keep preparation/source-plan bytes visible and preserve the selective-range limitation until independently solved.

If direct-final root construction does not push the frozen Law traffic gate below 0.75x while retaining the CPU win, stop this rehabilitation and move to the generic range/native integration boundary rather than tuning thresholds.
