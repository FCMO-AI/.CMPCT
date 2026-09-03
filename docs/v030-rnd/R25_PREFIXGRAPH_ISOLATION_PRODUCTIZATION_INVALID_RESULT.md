# PrefixGraph isolation Builder hostile review — invalid robust-RSS receipt

Status: **PRESERVED INVALID S6 RECEIPT / CUSTODY FAILURE / ZERO RELEASE CREDIT**

This record preserves the first result-bearing execution of `R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_PREREG.md` after exited-child-aware whole-process-tree RSS accounting was admitted. The frozen preregistration and v1 instrument remain immutable.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `9d73b16c2ad55078e500d88487681a631168b488`
- workflow: `CMPCT v0.30 PrefixGraph isolation Builder hostile review`
- run: `33722652263`
- substantive job: `100544872146` (`hostile-review`)
- artifact id: `9880867780`
- artifact digest: `sha256:314f5ced2cbfb6e4910a9c1d37406e2ff75a994dad58e49b06490ea3415ee83f`
- schema: `cmpct-v030-prefixgraph-isolation-productization-v1`
- experiment valid: **false**
- release credit: **false**

The substantive Builder-versus-threaded-control measurement completed and uploaded its exact evidence. The terminal ratchet correctly did not run because the v1 oracle declared the receipt invalid.

## Exact measured summaries

| arm | final r25 bytes | r24 product bytes | median whole-tree peak RSS | median wall |
|---|---:|---:|---:|---:|
| threaded control | **1,700,599 B** | **29,883,728 B** | **365,168 KiB** | **34.671370133 s** |
| process-isolated level-15 Builder | **1,700,660 B** | **29,883,728 B** | **259,774 KiB** | **38.770957360 s** |

Both arms were deterministic. The candidate size penalty was **61 B / 0.003587%**. Descriptively only, without granting terminal authority, the measured candidate reduced whole-tree peak RSS by **28.8618%** and had a **1.118241x** wall ratio.

Those descriptive deltas are not a valid S6 decision because the v1 custody gate failed first.

## Exact invalidity

The v1 oracle hard-coded:

`R24_BYTES = 29_883_732`

Every result-bearing control and candidate build on the exact source instead emitted the same current genuine-r24 product size:

`29_883_728 B`

The frozen preregistration's product invariant is that r24 product bytes remain unchanged **between arms**. That invariant held in the measured receipt. The additional hard-coded four-byte historical fingerprint in the v1 instrument was stricter than the preregistration language and had become stale relative to the exact current source.

Because result-bearing execution had already begun, the old oracle may not be edited or reinterpreted after the fact. Its outcome remains exactly **`INVALID_PRODUCTIZATION_RECEIPT`**.

## Scoped interpretation

This invalid receipt does **not** prove `PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED`, `PREFIXGRAPH_ISOLATION_EXPORTED_DEBT_REMAINS`, or `PREFIXGRAPH_ISOLATION_PRODUCTIZATION_DID_NOT_TRANSFER`.

It does establish two useful custody facts for the superseding experiment:

1. exited-child-aware accounting still measured a large candidate/control RSS separation under this source; and
2. the obsolete fixed r24 byte constant, rather than arm-to-arm r24 drift, prevented the frozen decision from being evaluated.

The observed wall ratio was above the unchanged 1.10 promotion boundary, so a valid superseding receipt must preserve that runtime debt if it reproduces; it may not widen the wall threshold.

## Reopening / supersession rule

Do not rerun v1 unchanged. A superseding freeze may change only the stale custody predicate from the obsolete historical r24 byte literal to an exact-current, same-source arm-equality requirement while preserving:

- target corpus and source-tree checks;
- control/candidate mechanisms;
- two alternating rounds;
- exited-child-aware whole-process-tree RSS accounting;
- `>=20%` RSS reduction gate;
- `<=1.10x` wall gate;
- `<=8,192 B` and `<=0.50%` size-debt gates;
- PrefixGraph selection, deterministic bytes/tree, helper lifecycle and hostile fail-closed requirements;
- zero release credit.

Any broader change requires a different scientific freeze.
