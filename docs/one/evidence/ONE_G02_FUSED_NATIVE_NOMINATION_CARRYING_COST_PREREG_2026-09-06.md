# ONE-G0.2 fused native nomination carrying cost — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The fused native nominator is semantically exact and removes one complete sequential observation pass, but it still uses a deliberately over-reserved fixed writer-side index. Before spending effort compacting that state, test whether the one-pass concept is economically viable in elapsed time against the exact same two-stage native semantics.

## Baselines

All timed paths execute behind one Python->C transition per sample through native wrapper functions so interpreter-call count cannot manufacture a win.

1. **selector-only**: promoted native minimizer selector with no nomination work. This quantifies the carrying premium of nomination but is not a same-semantics competitor.
2. **two-stage exact baseline**: promoted selector emits its anchor trace, then the terminal native event consumer re-scans the same bytes and consumes that trace. This is the same nomination semantics as the fused candidate.
3. **fused candidate**: one-pass fused selector+nominator, with trace output disabled.

The terminal semantic gates already establish exact agreement. This experiment must recheck output counts before timing.

## Falsifiable hypothesis

Eliminating the second full observation scan and intermediate anchor trace will make the fused candidate materially faster than the exact two-stage native baseline on mature inputs, despite moving event/index work into the selector hot loop.

### Disproof

The one-pass concept is not yet economically justified if the cross-large fused/two-stage median is >= 1.00x or if any mature negative-control regime exceeds 1.05x without a clear noise explanation.

## Frozen timing envelope

Use deterministic rows at 64 KiB and 256 KiB relation sizes, seeds 7, 29 and 53, across:

- `shift_plus1`;
- `damage_quarter`;
- `fragmented_every96`;
- `hostile_fixed_bands`;
- `fragmented_every32`;
- `independent_random`.

Run 31 paired samples per row with alternating A/B-B/A order after warmup. Persist raw samples and medians for selector-only, two-stage and fused paths.

## Promotion/decision law

This experiment cannot promote the fixed-index implementation because it carries 198,144 B of research event-index reservation. It can only decide whether the fusion principle deserves rehabilitation.

- `advance_fused_nomination_state_rehabilitation`: semantic equality; cross-large median fused/two-stage <= **0.90x**; no row > **1.05x**; negative controls have median <= **1.00x**.
- `hold_fused_nomination_state_rehabilitation`: semantic equality; fused/two-stage < **1.00x** cross-large but the stronger gate is missed.
- `retire_fused_nomination_hot_path`: cross-large median >= **1.00x** or systematic negative-control regression > **1.05x**.

Also report fused/selector-only. A large selector premium is explicit remaining carrying-cost debt even if fused beats two-stage.

## Hostile Reviewer

A win over two-stage only says fusion is better than deliberately duplicated work; it does **not** prove the nomination policy is cheap enough for the final writer. The always-hot 136-byte certificate already demonstrated that useful evidence can be economically disastrous. Therefore selector-only carrying premium and fixed-index state remain first-class debt and must be rehabilitated before integration into a product writer.
