# ONE-G0.2 Prepared Terminal Plan — Preregistration

**Status:** frozen before hosted result  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`

## Mission lock

The prior native Fill batch falsifier showed that removing per-Fill FFI calls is insufficient because the reader still walks the generic graph and constructs a ctypes schedule on every reconstruction. Test whether compiling the unchanged bounded terminal `Surprise`/`Fill`/`Concat` graph once into deterministic replay state materially improves repeated reconstruction without hiding compilation cost.

## Hypothesis

For nontrivial run-heavy terminal Laws, prepared replay will remove enough graph-walk/schedule-construction overhead to (a) remain within 1.05x literal-control wall and CPU on every frozen row, (b) beat schedule-on-read native bulk execution by at least 10% on every `long_runs` row, and (c) repay its measured compilation cost within four replays on both wall and CPU.

## Frozen matrix

64 KiB, 256 KiB, 1 MiB × the existing five observer families, 21 repetitions. Same Program, same root commitments, same modeled memory traffic, same stored wire. The candidate plan is compiled from the decoded Program; no cryptographic work, output bytes or Fill effects are precomputed.

## Disproof

`HOLD_PREPARED_TERMINAL_PLAN` if any resource/density gate regresses, any hot row exceeds 1.05x literal control, any `long_runs` hot replay exceeds 0.90x the current schedule-on-read bulk path, or any `long_runs` break-even exceeds four replays. Semantic/matrix failure is `INVALIDATE_PREPARED_TERMINAL_PLAN`.

## Claim boundary

A green result would support reusable validated execution plans for repeated/full-root reads of the tested terminal graph. It would not establish one-shot cold-read superiority, selective-range authority, a new reader opcode, or permission to precompile arbitrary unsupported Law cones.
