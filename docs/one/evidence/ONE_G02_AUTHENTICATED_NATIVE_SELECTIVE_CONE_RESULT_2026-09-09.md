# ONE-G0.2 authenticated native selective cone — result

Date: 2026-09-09  
Decision: **ADVANCE_AUTHENTICATED_NATIVE_SELECTIVE_CONE**

## Exact evidence authority

- Evidence source: `cb75fd68784d072e25f94e15c57f1b6d147cb471`
- Workflow: `CMPCT1 ONE-G0.2 authenticated native selective cone`
- Run: `34393209563`
- Job: `102606408231`
- Artifact: `10120476749`
- Artifact digest: `sha256:71bb42656d3e3fb456dd07b7bef52e6faa6429f778d7517ee25c22791f9dc29e`
- Artifact name: `authenticated-native-selective-cone-cb75fd68784d072e25f94e15c57f1b6d147cb471`

The hosted lane checked out the exact evidence source, installed the repository test dependency surface, passed the inherited selective-auth/native-range/AuthTree semantic and hostile tests (`59 passed`), ran the frozen falsifier, and retained the exact-source JSON artifact.

The earlier run `34383200129` is **not scientific evidence**: it failed during pytest collection because the narrow workflow omitted repository dependencies (`msgpack`) and never reached the falsifier. The scientific matrix and gates were not changed to rehabilitate the lane; only the dependency surface was corrected and the exact lane re-armed.

## Frozen-gate result

The candidate boundary remained:

`requested range -> Merkle-leaf-aligned dependency cone -> native generic ONE Law schedule -> reconstructed authenticated leaves -> sibling-proof preparation -> root verification -> requested bytes`

No whole-root reconstruction/hash shortcut was permitted. Unsupported topology still fails closed.

All frozen gates passed:

| Gate | Result |
| --- | ---: |
| exact semantic parity | PASS |
| hostile authentication/resource rejection | PASS |
| no hidden fallback | PASS |
| no whole-root positive work | PASS |
| fixed-cone non-scaling | PASS |
| temporary state cone bounded | PASS |
| median Law-positive CPU below incumbent | PASS |
| worst Law-positive CPU <= 1.10x incumbent | PASS |
| median Law-positive modeled movement <= 0.75x incumbent | PASS |

Key aggregates from the retained JSON:

- median Law-positive candidate/incumbent CPU: **0.0781982661x**
- worst Law-positive candidate/incumbent CPU: **0.1755686447x**
- median Law-positive candidate/incumbent modeled data movement: **0.7352817195x**

For fixed 4 KiB requested cones while roots grow 32 KiB -> 128 KiB -> 512 KiB, add8/XOR and sparse-crack Law rows preserve:

- `cone_bytes = 4096`
- `authenticated_leaf_payload_bytes = 4096`
- `source_read_bytes = 4096`
- `source_plan_write_bytes = 4096`

Only authentication sibling count grows logarithmically with root size (`3 -> 5 -> 7` for the fixed-cone rows), as expected for the generic tree proof.

At the 512 KiB root scale, examples include:

- add8, first 64-byte request: `0.07025x` incumbent CPU and `0.80216x` incumbent modeled movement; only a 4 KiB authenticated cone is reconstructed while 520,192 root bytes are avoided.
- XOR, first 64-byte request: `0.14984x` incumbent CPU and `0.80216x` movement.
- add8+Surprise crack, first 64-byte request: `0.07488x` CPU and `0.66968x` movement.
- XOR+Surprise crack, first 64-byte request: `0.17557x` CPU and `0.66968x` movement.

The movement result is strongest on sparse Surprise-bearing relations because the incumbent redoes more logical work while the candidate reconstructs/authenticates only the requested leaves.

## Interpretation

This closes an important G0.2 reader question: ordinary ONE Law/Surprise Programs can support **authenticated, cone-proportional selective reconstruction** without reader discovery, Law-family proof formats, whole-root reconstruction, or integrity weakening.

The candidate's main remaining per-request cost owners are now preparation and authentication work, not Law arithmetic. Typical 4 KiB positive rows spend tens of microseconds in plan preparation and roughly tens of microseconds in proof preparation/root verification, while native execution itself is generally around 9-13 microseconds.

This ADVANCE does **not** erase the already-confirmed control-plane locality problem: raw Programs still require whole-Program preflight. Repeated selective access should therefore use a fully validated immutable Program authority rather than repeating global validation on each request.

## Strongest caveat

The frozen promotion gates apply to **Law-positive selective rows**. Literal/Fill/Concat controls can be slower than the incumbent because the generic authenticated native route has fixed planning/proof overhead and sometimes extra source-plan traffic. This is not a reason to weaken the result, but it means the production reader should remain opportunity-gated: use the generic native cone path where its topology/economics justify it, and preserve the simpler incumbent path for cheap controls.

The experiment therefore promotes the authenticated selective-cone mechanism and its causal architecture, not an unconditional rule that every selective request must use the native plan.

## Next decisive work

1. Consume the compact reusable validation-certificate falsifier without moving its frozen memory/CPU gates.
2. Integrate reusable validated-Program authority with authenticated selective cones and measure the complete **open-once + retained authority + repeated selective reads** lifecycle.
3. Make candidate admission generic and economic so trivial Literal/Fill/Concat requests avoid native planning/proof overhead when it cannot repay itself.
4. Keep the September 11 full 15-workload ONE vs frozen-v0.29 vs strongest-deferred-v0.30 gate separate and same-semantics.
