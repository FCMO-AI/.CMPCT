# J24G04b — Prospective correction of Builder footer baseline; not a hypothesis rescue

**Recorded after infrastructure-only initial failure; BEFORE any N>0 orphan-tail experiment executed.**

First hosted source-exact run [40638195302](https://github.com/FCMO-AI/.CMPCT/actions/runs/40638195302) installed genuine CMPCT successfully, proved Git source blob identity, and failed before the first orphan tail at the initial baseline assertion:
`assert archive.latest_footer_pos == 0`.
This assertion was a mistaken instrument assumption, not scientific evidence of a quadratic decoder or its absence.

## Causal error

The authentic released Builder writes *both* authenticated primary and **tail checkpoint footer**. Therefore valid `Builder.build` archive has a nonzero `latest_footer_pos` and requires at least one call to the genuine footer decoder at Reader open. The original prereg assumed incorrectly that a valid Builder baseline had no footer; importantly it had not run any N=32/128/256 cases. Deleting or stripping that Builder footer would weaken the required first-party control.

## Frozen correction before observing scientific result

Keep the original Builder archive and footer *unchanged*; keep original N=32/128/256, linked orphan deltas, three repetitions, authentic SHA framing, zero-magic same-size and real rename controls. Count calls on genuine `CMPCT._decode_generation_payload` with the unchanged decoder result. Under the original triangular mechanism, the **incremental** orphan-footer work must equal `N(N+1)/2` relative to the original Builder tail footer's constant baseline `B` (expected B=1), rather than requiring absolute N(N+1)/2. All orphan-tail opens must select the **same valid authenticated Builder footer**, not primary fallback. Record selected footer address, full archive hash, exact original bytes. The equal-length nonmagic tail must also retain baseline B calls, and a first-party appended rename must select a newer footer and retain exact content.

**Outcome / disproof rule:** reject original absolute count prediction as **instrument specification error** (visible forever). Confirm the causal incremental hypothesis only if `calls(N)-calls(0) = N(N+1)/2` for every specified N and raw repetitions, while valid Builder footer recovered and contents verified. Any non-triangular incremental result falsifies this refined structural prediction; do not adjust N, source or acceptance after observing it. No product fix/release/benchmark credit. The initial CI failure remains a permanent negative instrument receipt.

## Why not change the scientific source

This change fixes only an impossible assertion about preexisting legitimate footer state; it does not edit product code, alter the orphan tail, lighten the controls, or change the count mechanism. A zero-history reviewer can see the original prereg, the first failure, this correction, and the later instrument commit in chronological Git order.
