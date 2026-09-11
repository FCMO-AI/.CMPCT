# ONE-G0.2 — generic translation IR range-cone result

Date: 2026-09-05

## Mission Lock / Referee freeze

The immediately preceding selective-access falsifier showed that the current whole-program wire + whole-root reference VM incurs source-size-scaling amplification for a 4 KiB request. This Builder isolated one causal question: is that amplification inherent to executing the generic ONE Law graph, or is it primarily an artifact of whole-program/whole-root execution?

The Builder was constrained to the existing six generic operations (`surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`). No translation/version-specific opcode, reader path, discovery logic, or legacy mechanism was allowed. It received an already-decoded `Program`; therefore wire indexing and selective integrity were explicitly **not** gifted as solved.

Frozen promotion gate across all 64 rows:

- requested bytes must exactly equal the independently authenticated full-reference oracle slice;
- cone materialization <= 2.1x requested bytes;
- cone reconstruction work <= 2.1x requested bytes;
- the range path must explicitly report `authenticated=false`.

## Builder

`experiments/one/range_vm.py` adds a generic cone-only evaluator. It reuses the reference VM's static graph/range/resource preflight, maps requested intervals backward through the same six generic Law operations, and materializes only intersecting information. Its public name, `reconstruct_range_unverified`, and result flag deliberately state the integrity boundary.

`tests/one/test_range_vm.py` independently checks all generic operations against the full reference evaluator, rejects invalid range/root requests, and verifies the translation shape touches only nodes needed by the requested cone.

## Exact evidence

- source SHA: `365c6f17a91271e9eb6988e6066398c32372ccf7`
- workflow run: `33948998926`
- result-bearing job: `101260118230`
- artifact: `9964201354`
- artifact ZIP SHA-256: `6dec1cfaae27eda6813bf3dfefce239230c9bab13b8ae356e75259855fc0569e`
- semantic + range-oracle boundary: **53/53 tests passed**
- experiment rows: **64/64 exact, 0 gate failures**
- request size: **4,096 bytes**

### 65,536-byte sources

- median materialized amplification: **2.0x**
- maximum materialized amplification: **2.0x**
- median reconstruction-work amplification: **2.0x**
- maximum reconstruction-work amplification: **2.0x**
- median nodes touched: **2**
- maximum nodes touched: **8**

### 262,144-byte sources

- median materialized amplification: **2.0x**
- maximum materialized amplification: **2.0x**
- median reconstruction-work amplification: **2.0x**
- maximum reconstruction-work amplification: **2.0x**
- median nodes touched: **2**
- maximum nodes touched: **5**

The measured 2.0x is source-size invariant over this test family: 4,096 requested bytes caused 8,192 bytes of modeled cone materialization and 8,192 bytes of modeled reconstruction work.

## Decision

**Advance the generic cone executor as causal evidence. Retire reconstruction-cone amplification as the dominant owner of the earlier 32x–448x loss on this family.**

The earlier whole-path loss remains real, but this A/B localizes it: the generic Law graph can reconstruct the requested interval with bounded, source-size-independent work without introducing a temporal/version-specific reader mechanism.

## Remaining non-borrowable debt

This is **not an authenticated selective-read solution**.

1. **Wire indexing:** the A/B begins with an already-decoded `Program`. The current wire reader still parses/materializes the program sequentially. A generic index/framing scheme must make the needed node and Surprise bytes addressable, and all index bytes must be charged.
2. **Hard selective authentication:** current roots carry a single whole-root SHA-256. The cone evaluator intentionally returns `authenticated=false`; claiming otherwise would require a whole-root scan. A generic authenticated framing/Merkle or equivalent structure must make range integrity possible while charging its stored bytes, proof traffic, hashing work and failure blast radius.

The next experiment should therefore study the density/access/integrity Pareto of generic authenticated Crystallization rather than hiding these costs behind the cone result.

## Hostile-review boundary

The 2.0x result is a reconstruction-cone fact for the tested generic IR family, not a product-access claim. Static preflight still sees the complete decoded program; physical random-access IO, wire parse bytes and authentication bytes are absent from this metric. Those omissions are named experimental debt, not gifted costs.

No v0.29/v0.30 comparator, canonical format, product-speed, release or public supremacy authority is created here.
