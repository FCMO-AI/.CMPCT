# ONE-G0.2 — cold late-rescue transfer negative

**Date:** 2026-09-04 America/Mexico_City  
**Experimental version:** `ONE-G0.2`  
**Result-bearing source:** `66f512216452edbddd46da8f3b45f55748b6b45b`  
**Workflow:** `33944085404`  
**Job:** `101246889451`  
**Artifact:** `9962759274`  
**Artifact digest:** `sha256:b8b003c3cc3d685cdbb4b3113a0ee861a476700722e72451419a38c572fc7ce0`

## Referee question

The fixed 4,096-position starvation gate preserved the original 8 KiB hostile shifted relation and cut hosted negative-path elapsed by more than half. The strongest surviving objection was structural transfer: did that success depend on the original adversarial seed being long enough to tolerate a cold minimizer warm-up?

The transfer corpus therefore selects inputs by a causal property that predates the candidate outcome: the first 12 deterministic pseudorandom 4,096-byte bases whose sparse Gear stream contains zero qualifying anchors. The frozen seed search interval is 0..4095. Selected seeds were:

`10, 71, 87, 106, 150, 186, 194, 215, 218, 250, 319, 359`.

Each basis is duplicated with insertions of 1, 8 and 31 bytes. Input selection never inspects full-minimizer or late-rescue success.

**Hypothesis:** the same 4,096-position cold starvation gate preserves full-minimizer marginal opportunity across these generator-distinct shifted/starved pairs.

**Disproof:** any hard-rescue row loses full-minimizer opportunity. Zero hard-rescue rows would be inconclusive rather than a win.

## Exact result

Decision: `reject_late_rescue_transfer`.

- transfer rows: **36**;
- rows where full minimizer supplied opportunity beyond both fixed and sparse cheap observers: **35**;
- hard-rescue losses: **35 / 35**;
- one remaining row did not require hard rescue;
- typical hard row: full minimizer **4,096 B**, late cold rescue **0 B**.

For example, seed 10 with a one-byte insertion produced an 8,193-byte input:

- fixed opportunity: 0 B;
- sparse Gear opportunity: 0 B;
- full minimizer opportunity: **4,096 B**;
- cold late rescue opportunity: **0 B**;
- rescue-active fraction: **49.2372%**;
- emitted rescue minimizers: **0**.

The same complete loss occurred for seed 10 at 8- and 31-byte insertions and broadly across the selected seeds.

## Causal interpretation

This rejects the **cold-start integration shape**, not sparse-anchor gating itself.

The gate waits until a sparse-anchor drought reaches the already-frozen 4,096-position minimizer span. The cold implementation then starts collecting a fresh 4,096-position minimizer window. Its effective first useful nomination therefore arrives only after roughly two spans of evidence. The original 8 KiB-basis hostile case was long enough to survive that delay; the 4 KiB transfer cases are not.

This is precisely the kind of false confidence the transfer gate was intended to expose. Moving the starvation threshold after seeing the result would be result-driven tuning and is forbidden.

## Scoped negative constraint

Do **not** promote or re-test the simple `detect starvation -> cold-start empty minimizer -> wait a full span` family by changing only the threshold, seed set or insertion length.

Reopening requires a causal change that removes the second warm-up interval. Examples include retaining sufficient pre-trigger Gear history/state to materialize the minimizer at the moment starvation is established, or an equivalent exact construction that does not add a source rescan or reader-visible mechanism.

## Rehabilitation direction

The strongest next Builder is **deferred materialization**:

1. sparse Gear remains the cheap always-on signal;
2. retain only the bounded pre-trigger observation state needed to cover the previous minimizer span;
3. when the 4,096-position starvation condition is met, construct the minimizer state from that already-observed history immediately rather than beginning a second warm-up;
4. charge the retained state, writes/materialization work and elapsed cost;
5. require the same generator-distinct transfer corpus to recover the hard rows before any timing promotion.

This preserves the successful idea—content-derived opportunity gating—while attacking the exported cold-start debt rather than tuning away the gate.

## Claim boundary

This is encoder-discovery negative evidence only. It changes no ONE reader semantics, product format, stored-byte claim, native-speed authority, comparator status or release state.
