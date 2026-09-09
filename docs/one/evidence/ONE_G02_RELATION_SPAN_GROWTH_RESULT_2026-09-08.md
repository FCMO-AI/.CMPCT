# ONE-G0.2 relation-span growth result

**Decision:** `ADVANCE_RELATION_SPAN_GROWTH`  
**Exact source:** `86ce1618ef2433f26c568ebc951d11d5b954e4ac`  
**Workflow run:** `34302722428`  
**Job:** `102312897503`  
**Artifact:** `10085508099`  
**Artifact digest:** `sha256:bee4b4e58ca7ac6844866a6cee99f84784720ae43b86bc0936b5ebbddae4bce7`

## Mission lock

Test whether a cheap, already-nominated 64-byte `add8` or `xor` seed can be converted into maximal exact relation spans without rereading accepted bytes, while compiling the result through the existing ONE grammar and staying competitive with fixed 4 KiB relation windows.

The experiment is writer-side only. It creates no reader-visible operation and does not establish general relation discovery.

## Frozen promotion law

The 18-cell matrix covered 64 KiB / 256 KiB / 1 MiB × `add8` / `xor` × `long_exact` / `sparse_cracks` / `false_seed`.

For decisive 1 MiB positive rows, grown spans had to satisfy all of:

- node count <= 0.25x fixed-window node count;
- wire bytes <= 1.01x fixed-window wire bytes;
- exact verification bytes <= 1.10x fixed-window verification bytes.

False nominations remained bounded to the real seed plus the first disproving extension. Semantics had to reconstruct exactly.

Source `04d0b2b5d727ab44cd9ccba15231763176e85dc7` is permanently inadmissible because the original `false_seed` boundary was probabilistic. The result above comes from the repaired exact source that deterministically forces the first post-seed byte to violate the claimed relation.

## Result

All 18 rows reconstructed exactly and the frozen decision returned `ADVANCE_RELATION_SPAN_GROWTH`.

At 1 MiB:

| op / family | grown nodes | fixed nodes | node ratio | grown wire | fixed wire | wire ratio | verify ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| add8 / long_exact | 4 | 131 | **0.03053x** | 524,391 | 526,927 | **0.99519x** | 1.000x |
| add8 / sparse_cracks | 19 | 131 | **0.14504x** | 524,608 | 559,599 | **0.93747x** | 1.000x |
| xor / long_exact | 4 | 131 | **0.03053x** | 524,391 | 526,927 | **0.99519x** | 1.000x |
| xor / sparse_cracks | 19 | 131 | **0.14504x** | 524,608 | 559,599 | **0.93747x** | 1.000x |

The false-seed 1 MiB controls admitted only the real 64-byte seed, stopped after the first forced mismatch, and used 65 exact comparisons. Fixed-window verification used 193-194 comparisons in those rows, so the grower was cheaper even on the hostile nomination.

## Interpretation

The structural result is stronger than a threshold win: maximal exact growth removes most control-node fragmentation without buying that reduction through extra exact scanning. On long exact relations it collapses 131 fixed-window nodes to four total Program nodes. Sparse cracks preserve bounded Surprise gaps and still cut the fixed-window graph to 19 nodes while also reducing complete wire bytes by about 6.25%.

The writer should therefore treat a small relation nomination as a seed for bounded exact span growth rather than immediately tiling the object into fixed relation windows.

## What this does not prove

- It does not prove that the observer can cheaply find the right relation, offset or value on arbitrary data.
- It does not establish real-corpus density or Genesis comparator superiority.
- It does not establish product create throughput; the Python grower is mechanism evidence.
- It does not alter reader semantics, selective access, authentication, recovery or portability authority.

## Next falsifiable question

Integrate the promoted fused opportunity gate with exact relation proof/growth and measure the complete discovery economics: nomination cost, false-positive proof work, exact bytes compared, candidate work avoided, final generic ONE wire bytes, and bits/bytes eliminated per extra CPU second. A positive result must survive incompressible/compressed controls and sparse/late/cracked relation cases without turning the writer into independent mechanism-specific scanners.