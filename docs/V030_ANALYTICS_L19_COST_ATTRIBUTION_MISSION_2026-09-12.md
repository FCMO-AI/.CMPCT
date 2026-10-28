# v0.30 Analytics L19 per-pack cost attribution mission

Status: **research-only causal referee**. No archive, format, selector, release, comparator, locality, integrity, recovery or ONE/Genesis authority changes.

## Question

The frozen selective Analytics writer proves that density requires essentially the whole positive L15->L19 opportunity: 45 admitted packs recover 434,113 B and leave only 232 B of optimistic margin versus the accepted v0.29 floor. Its level-19 stage costs about 4.78 s CPU. Admission therefore cannot solve the remaining speed problem by simply skipping more work.

The next optimization target depends on whether that 4.78 s is concentrated or diffuse. If a small number of raw packs dominate CPU, a targeted structural/native acceleration can attack those packs while preserving all required savings. If cost is broadly proportional across the 45 required packs, the problem is the high-effort engine itself and targeted exceptions are unlikely to matter.

## Falsifiable hypothesis

On the exact 45 packs admitted by the frozen `raw >= 256 KiB && L15 ratio <= 0.70` rule, the most expensive quartile (top 12 by level-19 CPU) accounts for at least **70% of total L19 compression CPU** while preserving a measurable share of the required L15->L19 byte reward.

This is an attribution hypothesis only; either result is useful. No production decision is made from pack identity.

## Referee contract

1. Rebuild the same normalized Analytics source and the exact L15 physical pack fixture.
2. Select the same 45 raw packs using the already-frozen path-blind rule; fail closed on population drift.
3. In a fresh child process, compress every admitted raw pack at fixed L15 and fixed L19, repeated three times with rotated pack order.
4. For each pack report raw bytes, deterministic L15/L19 sizes, saving bytes, median L15 CPU/wall, median L19 CPU/wall, incremental L19 CPU, and L19 CPU per KiB saved. SHA is used only as a stable join key, never as a policy feature.
5. Report concentration curves: top 1, 4, 8, 12 and 24 packs by L19 CPU, with fraction of total CPU, raw bytes and byte reward.
6. Report size-bucket aggregates derived from raw byte counts only; no path/extension/workload labels.
7. This lane earns no archive-size or release credit and does not claim scheduler performance.
8. Green CI means the receipt is valid, not that concentration exists.

## Decision

- **CONCENTRATED:** top 12 >=70% of L19 CPU. The next Builder must target the causal hot-pack mechanism (structural or native) while retaining all required byte reward.
- **DIFFUSE:** top 12 <70%. Retire pack-targeted acceleration as the primary idea and focus on reducing the high-effort algorithm cost globally or earning enough structural density to step down search.

The ONE Genesis result and `research/cmpct1` remain untouched.
