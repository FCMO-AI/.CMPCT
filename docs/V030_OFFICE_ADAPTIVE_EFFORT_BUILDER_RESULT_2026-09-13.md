# v0.30 EG08 adaptive-effort Office Builder result — 2026-09-13

Status: **Office Builder pass; research evidence only; transfer required before promotion**

Exact measured head: `c1b228b803e424540368f0282363cf3a717a4e62`
Hosted run: `34762412169`
Receipt artifact: `10319437209`
Artifact digest: `sha256:b9d523a77a7a02ced9a070a746d1bf6f96e0682f495e785db90f0c4f4f1fbf67`
Scientific verdict: **`EG08_OFFICE_BUILDER_PASSES`**

## Same-input result

Office tree: `ba72464747d4e3c129d91077c30f0c17c97fcb9bf5fc997cfe7001e234998934`

| Contender | Stored bytes | Fresh-process create CPU | Fresh-process wall | Peak RSS |
| --- | ---: | ---: | ---: | ---: |
| EG07 direct baseline | `6,437,727 B` | `0.29185 s` | `0.29186 s` | `473,660 KiB` |
| **EG08 adaptive effort** | **`5,954,142 B`** | **`0.67188 s`** | **`0.67196 s`** | **`473,660 KiB`** |
| exact frozen Genesis-v0.29 surface | `5,954,929 B` | `18.56233 s` | `18.56428 s` | comparator receipt does not export RSS |

EG08 is therefore:

- **483,585 B smaller than EG07**;
- **787 B smaller than the exact frozen v0.29 product surface** on this current deterministic Office tree;
- ~`27.63x` faster in creation CPU than frozen v0.29 (`EG08/v0.29 = 0.03620x`);
- byte-for-byte lossless and strongly verified after the real repack, not merely an attribution oracle.

The actual archive realizes **99.766%** of the preregistered `484,719 B` same-geometry oracle saving.

## Reader/locality invariants

EG08 preserves the EG07 physical geometry exactly:

- member count: `20`;
- maximum member read amplification: `4.0011285x`;
- maximum raw decode unit: `524,288 B`;
- strong verify: pass;
- canonical user-tree identity: pass;
- primary-metadata corruption -> authenticated tail recovery: pass.

No locality budget was spent to recover Office density.

## Effort economics

The research implementation first builds valid EG07 and then performs a role-aware repack. That exported work is fully charged:

- adaptive repack CPU: `0.29913 s`;
- adaptive repack wall: `0.29914 s`;
- total EG08 fresh-process creation CPU: `0.67188 s`;
- total EG08 fresh-process wall: `0.67196 s`.

The threshold-free ladder made `65` high-effort attempts, stopped early on `3` packs and changed `8/28` physical packs. Final selected effort roles:

- current level-1/raw choice: `20` packs;
- level 6: `1` pack;
- level 19: `7` packs;
- levels 3/12: `0` final packs.

Hot inverse-view stream roots remained untouched. The mechanism uses no path, extension, workload identity or Office-derived byte threshold.

Peak RSS in the fresh-process receipt is unchanged at `473,660 KiB` for EG07 and EG08. This does **not** prove the post-build repack is memory-free: the common V25/Office build already owns the measured peak, so finer memory attribution remains useful. It does show no new observed peak-RSS regression on Office.

## What this establishes

The frozen-v0.30 Office deficit was not evidence that the bounded reader geometry was inherently too expensive. The current EG07 geometry can beat the mature v0.29 Office size while retaining the v0.30 creation-speed advantage when compression effort is spent selectively on the physical units that continue to earn bytes.

This is the mechanism-level result sought from the Genesis lesson: cheap default work, spend expensive compute only when the same unit proves continued economic return, keep reader semantics unchanged.

## What this does not establish

Office is the discovery workload. Passing it does **not** authorize promotion or any canonical score change. The unchanged EG08 mechanism must now transfer to Analytics and held-out/hostile workloads, with CPU/RSS debt visible. A no-byte-regression construction is not enough if high-effort attempts create broad creation regressions or memory pressure.

No Genesis aggregate, composed R4 aggregate, version number, release state, ONE evidence or locality rule changes from this Office pass.
