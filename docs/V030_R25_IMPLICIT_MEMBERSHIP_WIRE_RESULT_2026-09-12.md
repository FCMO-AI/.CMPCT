# v0.30 r25 implicit contiguous membership wire result — 2026-09-12

Status: **wire mechanism earned; research-only, no format/release/aggregate credit**.

Source head: `f41ec10af21c1a9ff1994922ad4d10a5267cb781`  
Hosted run: `34732343735`  
Hosted job: `103657335878`  
Artifact id: `10310420537`  
Artifact digest: `sha256:1f554ab9a2aae746f8c61a325573054d288b3e045528fc0d24bfb58249408bb4`  
Schema: `cmpct-v030-r25-implicit-membership-wire-v1`

## Verdict

**`R25_IMPLICIT_MEMBERSHIP_WIRE_EARNED`**.

The preregistered candidate records one authenticated pack id plus ordered `[path,length]` members, derives offsets cumulatively, validates the cumulative size against the owning pack uncompressed size, and constructs direct `path -> (pack,offset,length)` lookup while decoding authenticated control.

The referee charged both metadata copies plus a new 16-byte framing reserve per copy (32 B total). It did not change physical payload packs.

## Exact hosted result

### Developer repository

| Quantity | Bytes |
|---|---:|
| source inherited-v0.25 archive | 744,337 |
| explicit-membership counterfactual | 760,499 |
| charged `membership-v1` candidate | **744,395** |
| stored saving vs explicit | **16,104** |
| prior compact-control attribution | 16,162 |
| retained fraction | **99.6411%** |
| preregistered 75% floor | 12,121 |
| candidate metadata raw | 58,303 |
| candidate metadata compressed | 22,226 |
| explicit metadata compressed | 30,294 |

Groups/members: **14 / 1,260**.

### Many Tiny Files

| Quantity | Bytes |
|---|---:|
| source inherited-v0.25 archive | 420,318 |
| explicit-membership counterfactual | 453,596 |
| charged `membership-v1` candidate | **420,392** |
| stored saving vs explicit | **33,204** |
| prior compact-control attribution | 33,278 |
| retained fraction | **99.7776%** |
| preregistered 75% floor | 24,958 |
| candidate metadata raw | 121,275 |
| candidate metadata compressed | 23,212 |
| explicit metadata compressed | 39,830 |

Groups/members: **3 / 5,000**.

## Semantic / hostile gates

All frozen gates passed on both workloads:

- reconstructed per-path `(pack,offset,length)` membership was exact;
- physical payload packs were byte-identical;
- strong user-tree identity remained exact;
- duplicate path failed closed;
- duplicate pack failed closed;
- unknown pack failed closed;
- cumulative-size mismatch failed closed;
- unsafe path failed closed;
- bad version and malformed top-level shape failed closed;
- direct lookup was built once during authenticated-control decode rather than scanning unrelated groups per read.

## What this establishes

The historical CMPNX5 saving did **not** depend on an exotic or unbounded metadata trick. A small bounded grammar reproduces essentially all of the measured control-byte advantage even after reserving fresh product framing. The core mechanism is simply to stop restating an offset when it is the prefix sum of prior member lengths in the same authenticated physical pack.

This remains orthogonal to r25 `implicit-v4` filesystem control. `implicit-v4` removes redundant filesystem-semantic fields relative to graph-owned regular identities. `membership-v1` removes redundant *physical content-pack membership* fields. Keeping those ownership layers separate avoids making filesystem semantics depend on one particular pack layout.

## Strongest self-critique / remaining debt

This is still a wire referee sourced from exact inherited-v0.25 pack relationships. It has **not** yet proved that the current r25 builder naturally produces eligible groups, that complete r25 artifacts get the same saving, or that the final integration preserves all product economics.

In particular, the result does not yet pay or measure:

- any additional r25 candidate-selection descriptor needed to decide when a group exists;
- actual r25 head/tail recovery integration beyond the two-copy byte charge;
- reader-open CPU/RSS for constructing a 1,260/5,000-entry lookup map;
- selective-read physical work from the owning r25 pack geometry;
- update/delete/rename behavior when group membership changes;
- native/shared-reader implementation and parity;
- cross-platform path/metadata portability;
- adversarial resource tests beyond the bounded malformed-control cases in this referee.

Therefore this result earns only the next **complete-artifact integration referee**. `docs/FORMAT.md`, `pyproject.toml`, canonical reader/writer behavior, aggregate scores, accepted v0.29 and ONE Genesis remain unchanged.

## Next decisive gate

Build the same compact membership ownership into the strongest current r25 product artifact without importing CMPNX5 layout policy. Admission must be content/economics driven and exact-fallback on loss. The next referee must charge the complete authenticated artifact and measure at minimum stored bytes, create CPU/wall/RSS, open/decode CPU/RSS, direct selective-read work, strong verify, corruption/recovery behavior and update semantics. Only that gate can earn provisional r25 format integration.
