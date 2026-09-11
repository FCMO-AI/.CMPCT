# ONE-G0.2 — Deferred-rescue cost-owner chain

**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`  
**Scope:** encoder-discovery research evidence only. No stored-byte, reader, product-speed, comparator, v0.29/v0.30-superiority, or release authority.

This evidence supersedes the *next Builder* suggestion in `ONE_G02_STARVATION_RESCUE_FALSIFICATION_2026-09-05.md`. The earlier negative findings remain intact: cold late rescue is retired, and isolated suffix-read reduction is not a primary elapsed owner.

## Surviving semantic path

Cold activation without retained history loses the useful historical minimum in **35/35** independently generated hard-rescue rows. Retaining enough history restores the exact opportunity:

- tuple history: **65,536 B**, 35/35 preserved;
- compact signal history: **32,768 B**, 35/35 preserved;
- one Gear seed + bounded **4,096-byte** input history: modeled incremental history **4,112 B**, 35/35 preserved.

The byte-history form is therefore the retained-history survivor. It does not, by itself, pass the promoted native compute boundary: the original compiled full-rescue candidate reserved 71,680 B versus 41,056 B for the promoted tail-return selector and was slower on ordinary controls.

## D1 — observation/cache versus full rescue

Exact source: `e09ec317dc376d8f91916bb929a566ec3d7a8063`  
Workflow: `33945478414`  
Job: `101250653816`  
Artifact: `9963181094`, ZIP SHA-256 `5ccd83c3c1a595726f10937265849bcfa3aa51cafaa798624382b83ae9741ba9`  
Semantic boundary: **50/50 ONE tests passed**.

The observation-only arm continuously maintains the exact Gear recurrence, starvation signal and 4,096-byte replay cache, but performs no replay or queue construction. It matched the full arm's final Gear state, considered-position count, sparse-anchor count and rescue-active count on every row.

| case | observation / promoted baseline | full rescue / observation | activations | replayed bytes |
|---|---:|---:|---:|---:|
| random 1 MiB | **0.806250x** | **1.309049x** | 19 | 77,824 |
| zlib-random ~1 MiB | **0.813737x** | **1.316843x** | 19 | 77,824 |
| repeated basis 1 MiB | 0.669469x | 1.297951x | 32 | 131,072 |
| shifted pair +1 | 0.807284x | 1.217651x | 12 | 49,152 |
| 4,160-byte boundary | 1.718136x | 0.969297x | 0 | 0 |
| hard starved 8,193 B | 1.065813x | 3.563860x | 1 | 4,096 |

Observation state was **6,144 B** in the instrument versus **41,056 B** for the promoted baseline and **71,680 B** for the full rescue. The small 4,160-byte boundary remains hostile and therefore requires the existing size dispatch; this experiment does not authorize lowering that boundary.

**Frozen decision:** `advance_replay_queue_owner_attack`.

**Causal result:** ordinary-path observation/cache is not the exported compute problem. On both entropy controls it leaves roughly 18.6–19.4% elapsed headroom relative to the promoted selector. Replay plus queue work consumes that headroom and more.

## D2 — replay arithmetic versus queue work

Exact source: `e0d71584b859b799deed92cd04d1836ac21efd22`  
Workflow: `33945620503`  
Job: `101251032254`  
Artifact: `9963224191`, ZIP SHA-256 `6fae4852a7fab66994fd843775c5f09160a8597a1bcd473333063139282ca1ba`  
Semantic boundary: **50/50 ONE tests passed**.

The replay-only arm performs the exact bounded Gear replay on every activation but never constructs or maintains the rightmost-minimum queue. Its semantic/accounting state matched the full arm on every row.

| case | replay-only / observation | full / replay-only | full peak queue |
|---|---:|---:|---:|
| random 1 MiB | **1.059206x** | **1.333441x** | 18 |
| zlib-random ~1 MiB | **1.058602x** | **1.346668x** | 18 |
| repeated basis 1 MiB | 1.088343x | 1.260526x | 15 |
| shifted pair +1 | 1.037314x | 1.263164x | 22 |
| 4,160-byte boundary | 1.016362x | 1.034608x | 0 |
| hard starved 8,193 B | 1.330511x | 2.801466x | 21 |

**Frozen decision:** `advance_queue_construction_maintenance_owner_attack`.

Replay arithmetic is measurable but secondary on the entropy controls: about +5.9%. Queue work adds another +33.3–34.7%. The hard-starvation row pays both heavily, so a successful rehabilitation must not optimize ordinary controls while ignoring the rescue case that exists to justify the mechanism.

## D3 — queue construction versus maintenance

Exact source: `31e1c45c0336aff1debb57243df6cab81a6a28dc`  
Workflow: `33945683208`  
Job: `101251203351`  
Artifact: `9963246131`, ZIP SHA-256 `580f4eb90605b4b58e9aaa0d0bf7c58418bf7f32201720888de609508d528121`  
Semantic boundary: **50/50 ONE tests passed**.

The build-only arm performs exact replay and exact monotonic-queue construction at activation, then deliberately omits post-build maintenance. Accounting matched replay-only and full rescue on every row.

| case | build-only / replay-only | full / build-only | queue entries built |
|---|---:|---:|---:|
| random 1 MiB | **1.211420x** | **1.070541x** | 77,824 |
| zlib-random ~1 MiB | **1.214377x** | **1.073284x** | 77,824 |
| repeated basis 1 MiB | 1.171389x | 1.031208x | 131,072 |
| shifted pair +1 | 1.104881x | 1.098690x | 49,152 |
| 4,160-byte boundary | 0.962760x | 1.027263x | 0 |
| hard starved 8,193 B | 1.670423x | 1.654236x | 4,096 |

**Frozen decision:** `advance_queue_construction_owner_attack`.

On the entropy controls activation-time construction costs about **+21.1–21.4%** over replay-only, while post-build maintenance costs only **+7.1–7.3%**. Construction is therefore the primary ordinary-path queue owner. The hard rescue remains harsher: construction +67.0%, then maintenance +65.4%, so later hostile review must preserve both phases there.

## Referee → Builder transition

The causal chain is now narrow enough to justify a concrete Builder rather than another broad minimizer search:

1. sparse-anchor starvation alone is not a sufficiently selective opportunity signal;
2. cold late rescue loses historical opportunity;
3. a 4,096-byte retained input history preserves it cheaply in memory;
4. continuously maintaining that history is cheap enough on large ordinary controls;
5. bounded replay arithmetic is secondary;
6. **activation-time monotonic-queue construction is the primary ordinary-path exported cost**;
7. post-build maintenance is secondary on ordinary controls but material on the hard rescue.

The immediate preregistered Builder is `one_g02_starvation_linear_build_ab.py`: during activation construction, queue `head == 0` and no expiry can occur, so the queue cannot wrap. It replaces generic ring modulo addressing during that phase with a linear monotonic-stack build, preserving the exact queue state handed to normal active maintenance. Promotion requires exact trace/accounting equality, candidate/full median `<=0.95` on both entropy-dense controls, no tested-case median `>1.05`, and identical reserved state.

If that local specialization fails, do not tune its threshold. Construction remains the owner; the next attack must change construction organization (for example a proof-equivalent bulk/vectorizable construction or a compact sufficient summary), not the starvation gate or reader ontology.
