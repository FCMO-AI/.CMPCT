# ONE-G0.2 root-hash writer plan-direct wire v2 terminal result — 2026-09-06

## Decision

`advance_plan_direct_wire_writer_v2`

This is a bounded writer-compiler advance only. It does not change ONE reader semantics, relation algebra, canonical bytes, stored size, root hashes, locality, recovery, or the frozen v0.29/v0.30 comparator contract.

## Exact-source authority

- Source/head: `71c0ecc45a4d3b96e689549ad7912046465d404d`
- Workflow run: `34043271914`
- Job: `101513729078`
- Artifact: `9992330328`
- Artifact digest: `sha256:974fe811863b85ce33e22cd109dc1014eb9dcc3607d7db0c9f127dceeea34ecc`
- Full ONE suite: `93 passed`
- Schema: `cmpct-one-g02-root-hash-writer-plan-direct-wire-v2`

## Causal repair from invalidated v1

V1 (`9083603dff3cb311340b3c56429e0165cc2ec34e`) remains invalidated as submitted. The independent semantic diagnostic localized its failure to hierarchy bookkeeping: references to intermediate concat nodes serialized a known reconstructed span as `Ref.length`, while canonical ONE uses `Ref(node)` with `length=None` there.

V2 changes one thing only: creator-side known span and serialized `Ref.length` are independent fields. Intermediate concat references retain the known span for parent declared-length arithmetic but serialize `length=None` exactly like the canonical Program writer.

## Semantic / canonical gates

All frozen rows passed exact equivalence:

- canonical wire bytes: identical;
- `WireStats`: identical;
- admission/enabled decision: identical;
- best shift and exact-proof counts: identical;
- native plan/oracle: identical;
- relation-specific traffic: identical;
- segmentation count: identical;
- hierarchy depth: identical;
- node count: identical;
- decode/evaluate reconstruction: exact;
- malformed-plan probes: passed;
- maximum control-byte delta: `0 B`;
- maximum total-byte delta: `0 B`;
- maximum Surprise-byte delta: `0 B`.

Maximum observed hierarchy depth was `2`; maximum node count `1368`; maximum segment count `2731`; maximum plan bytes `5796`.

## Performance

Frozen mature range: 64/128/256 KiB over the productive temporal cases.

- mature productive median candidate/baseline: **`0.7807797801x`** (~21.92% less elapsed time);
- mature control median: **`0.8915275040x`** (~10.85% less elapsed time);
- productive mature rows `<= 0.90x`: **12 / 12**;
- no mature productive row exceeded the frozen `1.03x` regression bound;
- no mature control row exceeded the frozen `1.08x` regression bound.

Mature productive ratios:

| Size | shift+1 | damage quarter | fragmented /96 | fragmented /32 |
|---:|---:|---:|---:|---:|
| 64 KiB | 0.802157 | 0.790654 | 0.796515 | 0.759059 |
| 128 KiB | 0.804106 | 0.800205 | 0.771818 | 0.743611 |
| 256 KiB | 0.787259 | 0.782001 | 0.759558 | 0.749459 |

Mature control ratios:

| Size | independent random | false pattern |
|---:|---:|---:|
| 64 KiB | 0.881459 | 0.872954 |
| 128 KiB | 0.901596 | 0.907835 |
| 256 KiB | 0.915394 | 0.891528 |

## Interpretation

The improvement does **not** come from weaker discovery, less proof work, fewer relation bytes, or a changed reader. `reduced_relation_specific_traffic_rows = 0` and canonical output is byte-identical. The measured gain comes from removing Python `Program` / `Node` / `Ref` materialization and compiling the already-chosen bounded native plan directly into the existing ONE0 wire representation.

This is strong causal evidence for the ONE doctrine `Analyze rich. Compile poor.`: rich creator-side discovery can collapse directly into the fixed minimal representation without carrying its planning object graph into the writer hot path.

## Resource / access truth

Stored bytes, decode semantics, selective-read behavior, reconstruction work and reader complexity are unchanged because the emitted canonical bytes are identical. This run did **not** establish a new peak-memory measurement. Lower Python object materialization strongly motivates a separate creator-memory/resource measurement, but no memory reduction is claimed here without that evidence.

## Hostile reviewer / bounded claim

- V1's semantic failure is preserved rather than rewritten away.
- V2 received an independent preregistration and did not inherit a fabricated result from v1.
- The fix is causal and singular; no speed threshold changed after seeing results.
- The benchmark establishes a writer-compiler improvement on the frozen root-hash temporal matrix. It does not by itself prove whole-system CMPCT1 superiority over v0.29 or deferred v0.30.

## Next decisive work

Promote V2 only as the experimental canonical writer compiler for further measurement, then re-profile the current writer/system boundary with V2 in place. Do not spend the next lane polishing the direct serializer merely because it won; identify the next dominant elapsed/resource owner under the improved baseline.
