# O5 — prospective higher-N follow-up to saturated RSS high-water

Date: 2026-10-24 UTC. This is an **independent bounded extension**, preregistered *before* new hosted measurements. It neither changes product nor rewrites O4 outcomes.

## Previous evidence and exact boundary
[O4 run 40092228664](https://github.com/FCMO-AI/.CMPCT/actions/runs/40092228664) passed on `e46207d9902c3748977ec35588995a51f10f06d9`. At 4,096 valid signed operations the combined replay cut preflight wall 486.198 ms to 21.240 ms, and process high-water RSS was identical 33,776 KiB. **But** high-water was already saturated before the timed function, so zero `ru_maxrss` increase was uninformative; the median during-call *live* VmRSS increase was 3,804 KiB candidate versus 2,528 KiB historical (~1,276 KiB extra), roughly 1,140 KiB after subtracting the equivalent checkpoint signal. This is nonzero but below the preregistered materiality discriminator. See `docs/v031-research/2026-10-24-preflight-fresh-process-rss-o4-result.md`.

## New primary scientific question
Is that increasing memory difference economically **material** at a still legitimate, larger r24 archive with **16,384 logical files and 16,384 signed rename operations**, while the established CPU win and unchanged checkpoint semantics survive? Observing a ~1 MiB 4k additional live footprint is not enough to extrapolate to all bounded valid file counts.

## Locked mechanism, controls and prediction
Use **unchanged** source-exact combined validator blob `1e085db992add64118a9488790096c574fff154d`, historical comparator Git blob `51c2849061f99a4afeddb7666956b24566ce7de0`, genuine r24 Builder-derived physical file and authenticated generation via the unmodified O4 source module. Invoke its `run_parent` with **exactly N=16,384, 5 independent subprocesses per arm**, for both delta and equivalent checkpoint; no parser ceilings or success checks change. Same-process time excludes startup; process peak high-water + before/after VmRSS; raw SHA-identical archive comparisons and child output retained as a distinct `fresh-rss-o5` artifact. Preserve original O4 artifact.

Prospective **research triage**, NOT release threshold: if candidate's median extra live-RSS increase at N=16,384 is >=8 MiB absolute or >=10% of historical post-call VmRSS and persists after subtracting checkpoint-control effect, conclude that a bounded representation-memory redesign deserves its own separately registered experiment. If it remains below both, do **not** iterate similar threshold variants; conclude that the tested N<=16,384 memory debt does not yet justify product complexity and return to integration/product parity. CPU/RSS tradeoffs must be reported regardless.

## Falsifiers and ambiguities
Any altered archive digest/semantic result, missing receipt, changed source fingerprint or timeout invalidates the O5 conclusion. `ru_maxrss` may remain saturated before preflight: do not mistake unchanged high-water for a zero memory cost. Before/after live VmRSS misses transient peaks, so positive material difference is meaningful but negative is bounded. Historical replay O(N²) is time-bounded via 90s child timeout, five samples, one large N; no unbounded scaling ladder or automatic retries.

## Concurrency, policy and future action
Research/evidence-only branch stacked on [#348](https://github.com/FCMO-AI/.CMPCT/pull/348). No edits to Reader, Builder, validation.py, other owners' branches, format r24, security, comparison thresholds, release, version or `docs/discovery/STATE.json`. A decisive O5 result can retire this narrow family until new evidence, not invent a reward-score criterion. Both positive and negative raw measurements remain public.
