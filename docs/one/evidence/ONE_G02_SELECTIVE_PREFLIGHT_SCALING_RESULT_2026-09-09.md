# ONE-G0.2 — fixed-cone selective preflight scaling result

Date: 2026-09-09  
Decision: **HOLD_PER_REQUEST_FULL_PREFLIGHT / COST OWNER CONFIRMED**

## Exact authority

- branch: `research/cmpct1`
- source: `56d1d6af8791a87a8d1e62cde3ff2ab68f5382be`
- workflow run: `34387583826`
- job/check: `102587658845`
- artifact: `10118296681`
- artifact digest: `sha256:4ff076faf64f355f2869f0688e8023e2c8190d950b2f977a3fc1bbe2513e620b`
- schema: `cmpct-one-g02-selective-preflight-scaling-v1`

The first source at `50309f121eb0f9265d9e744c487b8139687d192f` was a harness failure, not admissible scientific evidence: the 4,096-unrelated-node cell exceeded the default 4,096-node Program limit once the live root nodes were included. The corrected source raises only the synthetic Program's `max_nodes` enough to make that test graph valid while preserving all other inherited limits.

## Frozen experiment

- root: 128 KiB
- requested range: first 4 KiB
- Law families: add8, XOR
- unrelated valid nodes: 0, 64, 256, 1,024, 4,096
- 11 warmed CPU samples per cell
- requested bytes, requested Law, root geometry and dependency cone remain fixed

## Hosted result

| Law | unrelated nodes | compile CPU | vs 0 unrelated |
|---|---:|---:|---:|
| add8 | 0 | 36.495 us | 1.000x |
| add8 | 64 | 145.167 us | 3.978x |
| add8 | 256 | 484.552 us | 13.277x |
| add8 | 1,024 | 1.940 ms | 53.150x |
| add8 | 4,096 | 7.331 ms | **200.885x** |
| XOR | 0 | 32.989 us | 1.000x |
| XOR | 64 | 143.674 us | 4.355x |
| XOR | 256 | 466.395 us | 14.138x |
| XOR | 1,024 | 1.836 ms | 55.649x |
| XOR | 4,096 | 7.253 ms | **219.850x** |

CPU growth was monotonic for both families.

## Causal interpretation

`compile_native_law_range_plan()` performs `Program.validate_shape()` and full `_preflight(program)` before lowering the requested cone. `_preflight` intentionally visits every stored node so malformed archive validity cannot depend on the requested root or cache order.

Therefore the byte/data plane can remain cone-local while the control plane is not: repeated selective opens pay O(total stored graph) validation even when requested reconstruction work is fixed.

This is not evidence for skipping validation. Full-Program validation is a hard safety invariant.

## Rehabilitation target

Move the exact existing full validation proof to an explicit Program/archive-open boundary, bind it to an immutable snapshot of the Program, and reuse that authority for later range requests. The raw Program API must retain full validation. Caller-mutable root mappings must be copied/frozen before authority is granted.

The follow-up experiment is preregistered in `ONE_G02_VALIDATED_PROGRAM_SELECTIVE_PLAN_PREREG_2026-09-09.md`.

## Negative-evidence rule

Do not describe current native selective planning as CPU cone-proportional merely because its source/data traffic is cone-proportional. Until reusable validation evidence passes, repeated range-open CPU remains graph-size-sensitive.
