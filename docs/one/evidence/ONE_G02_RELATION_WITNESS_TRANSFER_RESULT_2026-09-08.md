# ONE-G0.2 relation witness transfer — result

**Decision:** `ADVANCE_RELATION_WITNESS_TRANSFER`

**Authoritative source:** `c099ee8f162b3f9c77fc168277bf486384ad325c`

**Workflow run:** `34314893593`

**Job:** `102348942070`

**Artifact:** `10089831608`

**Artifact digest:** `sha256:5ce59f940543b1e5285514e40129715537f7d6d42eb1bed7604535e267894b90`

## Mission lock

Test whether one bounded 64-byte-cadence observation structure can hand exact verification an actionable `(op, value, parent_offset, child_offset)` witness for non-periodic adjacent-version add8/XOR structure, without a second discovery scan and without confusing exact reuse or probe-only coincidences with Law.

The candidate remains writer-only discovery state. A witness never authorizes storage. Exact relation proof, ordinary ONE `add8` / `xor` / `surprise` / `concat`, full Program evaluation and root hash remain authoritative.

## Frozen matrix and verdict

The exact 21-cell matrix was `64 KiB / 256 KiB / 1 MiB` × `add8_versioned`, `xor_versioned`, `add8_sparse_cracks`, `xor_sparse_cracks`, `exact_repeat`, `random`, `probe_false_positive`, with seven timed repetitions.

All semantic checks passed. All twelve positive relation rows selected the required non-zero relation and reconstructed exactly. All nine negative rows admitted zero relation bytes. The probe-only hostile control spent only 64–66 exact proof bytes, far below the frozen 8192-byte ceiling. Every row charged exactly one source scan. Probe traffic was fixed at `0.046875x` input. Modeled state remained below the frozen `0.60x` input cap on every row.

### Representative 1 MiB results

| Family | Wire / literal | Accepted relation bytes | Exact proof bytes | Modeled state / input | Writer CPU | Bits saved / CPU s |
|---|---:|---:|---:|---:|---:|---:|
| add8_versioned | 0.500066x | 524,288 | 524,288 | 0.260994x | 93.62 ms | 44.80 Mbit/s |
| xor_versioned | 0.500066x | 524,288 | 524,288 | 0.261036x | 88.43 ms | 47.43 Mbit/s |
| add8_sparse_cracks | 0.500273x | 524,280 | 524,288 | 0.260471x | 96.94 ms | 43.25 Mbit/s |
| xor_sparse_cracks | 0.500273x | 524,280 | 524,288 | 0.260532x | 88.14 ms | 47.56 Mbit/s |
| exact_repeat | 1.000000x | 0 | 0 | 0.308311x | 38.17 ms | 0 |
| random | 1.000000x | 0 | 0 | 0.209892x | 35.02 ms | 0 |
| probe_false_positive | 1.000000x | 0 | 65 | 0.260166x | 36.97 ms | 0 |

The positive versioned families contained zero cross-version exact-reuse 64-byte blocks, so the density win is not an exact-reuse accident. The exact-repeat controls contained the expected large reuse signal but were not misclassified as non-zero add8/XOR Law.

At 64 KiB the positive wire ratio was `0.501059x`; at 256 KiB it was `0.500265–0.500406x`; at 1 MiB it was `0.500066–0.500273x`. Sparse cracks therefore preserve almost the entire half-file relation while becoming ordinary Surprise at the actual cracks.

## Hostile-review interpretation

This advances a **writer discovery handoff**, not a product writer or general resemblance detector.

The result proves that compact block evidence can carry enough geometry to launch exact maximal relation growth without a second discovery scan. It does not prove that the Python dictionaries/objects used by the research prototype are acceptable production state. `modeled_state_bytes` is a compact target accounting, not CPython RSS. Python wall/CPU is retained as research telemetry only.

The benchmark also knows that each synthetic input consists of two contiguous versions when converting witness geometry into a candidate parent/child pairing. The observer itself receives no family or boundary label, but general archive segmentation remains open.

The fixed 8192-signature capacity covers this preregistered envelope; it is not authority for arbitrary larger archives. Late relations beyond the cache horizon, arbitrary phase shifts, many-way version history and replacement policy remain hostile transfer debt.

## Strongest negative / self-critique

The state fraction is still large: roughly 21–37% of source bytes on the tested rows. That is below the deliberately permissive structural gate, but it is nowhere near a production writer target. The successful discovery substrate is therefore not yet evidence that its carrying cost earns its density gain in a complete ingest path.

A second weakness is that the writer performs exact proof over essentially the entire accepted relation span. That is correct and bounded, but the next systems gate must charge it against the work it avoids/savings it creates rather than treating exact verification as free.

## Promotion scope

Promoted principle:

`one forward 64-byte-cadence observation -> bounded actionable relation witness -> exact maximal span verification -> ordinary ONE Law/Surprise Program`

Not promoted:

- Python object layout or memory behavior;
- production writer throughput;
- arbitrary archive/version segmentation;
- unbounded signature-cache behavior;
- general resemblance discovery;
- any reader-visible opcode or format change.

## Next decisive falsifier

Move upward to a **charged end-to-end writer envelope**. Reuse the promoted observer/witness principle and maximal relation growth, but compare against the inherited fused observation/direct-emitter writer path while charging:

1. root hashing / identity already required by ingest;
2. block observation and retained-state traffic;
3. witness nomination;
4. exact relation proof bytes;
5. Program construction + validation;
6. direct canonical emission;
7. peak/modelled discovery state;
8. final wire bytes and bits eliminated per extra CPU second.

Attack random/incompressible, compressed/media-like, exact reuse, false invariant collisions, sparse cracks, late relations beyond the current cache horizon, arbitrary phase shifts, and version-history depth. Promotion requires a mechanism-level marginal-information-yield win without weakening semantics or turning relation search into a separate reader-visible mechanism.

Do not loosen this experiment's frozen thresholds after the result. Any production rehabilitation must reduce carrying state/cost while retaining this exact semantic and density evidence.