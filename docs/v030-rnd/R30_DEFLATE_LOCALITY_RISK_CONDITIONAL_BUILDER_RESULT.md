# R30 — Deflate Locality-Risk Conditional Retention Builder Result

Status: **TERMINAL — BYTE_WIN_RUNTIME_OR_RSS_DEBT; PRESERVE BYTE MECHANISM, DO NOT PROMOTE**

Frozen preregistration: `docs/v030-rnd/R30_DEFLATE_LOCALITY_RISK_CONDITIONAL_BUILDER_PREREG.md`.

Execution authority:

- workflow run: `33833358148`
- result-bearing checkout head: `ddac8b8b3d0fb4e68511bacaa9185991b2a0cfec`
- authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`
- release fingerprint at execution: `fa061c2d0f8d0e09f541aa6ac8f98066b8d86e4f86ed36596f6baa7a2f81eb57`
- immutable artifact: `9922557163`
- uploaded artifact ZIP SHA-256: `c3e4b5723340e3409ae50f7297648eb3536e3453e0b129a1840ee22e48067457`
- frozen Builder: **PASS**
- frozen completeness / decision-law guard: **PASS**

## Frozen terminal decision

`BYTE_WIN_RUNTIME_OR_RSS_DEBT`

The content-derived locality-risk rule recovered the complete mature-64KiB byte opportunity on both frozen targets while preserving strong reconstruction, 1.0x measured virtual-member locality and the release arm's peak RSS. It failed the frozen create-time no-material-regression law on both targets.

| Target / arm | Complete bytes | vs release-all-exact | median create | vs release-all-exact | peak RSS | max locality |
|---|---:|---:|---:|---:|---:|---:|
| full-backups / release-all-exact | 8,088,199 | — | 0.469236 s | — | 473,044 KiB | 1.0x |
| full-backups / mature-64k | 8,055,779 | -32,420 B | 0.561652 s | +19.69% | 473,044 KiB | 1.0x |
| full-backups / locality-risk-v1 | 8,055,779 | **-32,420 B** | 0.563493 s | **+20.09% / +94.256 ms** | 473,044 KiB | 1.0x |
| nested-only / release-all-exact | 2,231,158 | — | 0.305421 s | — | 473,044 KiB | 1.0x |
| nested-only / mature-64k | 2,197,416 | -33,742 B | 0.420631 s | +37.72% | 473,044 KiB | 1.0x |
| nested-only / locality-risk-v1 | 2,197,416 | **-33,742 B** | 0.421710 s | **+38.07% / +116.289 ms** | 473,044 KiB | 1.0x |

Every row strongly verified. The repaired generator identity matched exactly. The locality ceiling remained <=8x with 1.0x observed on both targets. RSS was flat in the frozen median accounting.

## Causal evidence

The strongest result is not merely that the conditional arm was slower. The frozen simple control and the conditional arm converged to the same representation decision:

- release-all-exact retained 192 canonical exact streams totaling 2,201,849 B and regenerated none;
- mature-64k retained 12 canonical exact streams totaling 1,918,264 B and regenerated 180 streams totaling 283,585 B;
- locality-risk-v1 retained the same 12 streams and regenerated the same 180 / 283,585 B on both frozen targets.

The mature-64k and locality-risk-v1 archives were therefore the same complete size on each target and their median build times differed by only ~1–2 ms. The exported ~0.1 s debt belongs to the deterministic regeneration regime exercised by those 180 streams, not materially to evaluating the locality-risk predicate itself.

This updates the Forge diagnosis:

- the zero-byte exact-Deflate retention policy is a real D2 carrying-cost owner for archive bytes on this Incremental Backups regime;
- the content-derived locality-risk predicate is sufficient to preserve the measured locality invariant on the frozen target;
- direct promotion is blocked by a distinct create-time debt in the regeneration path;
- the next lowest-sufficient work is rehabilitation/attribution of that exported runtime, not threshold search and not a global rollback.

## Breakthrough rehabilitation ledger

**Preserved gain:** -32,420 B on full-backups and -33,742 B on nested-only versus release-all-exact, with strong verification, 1.0x locality and flat measured RSS.

**Exported debt:** +94.256 ms / +20.09% on full-backups and +116.289 ms / +38.07% on nested-only versus release-all-exact.

**Scope:** repaired deterministic Incremental Backups target plus the exact nested `snapshot_2.zip` projection under canonical r24 product semantics.

**Hard invariants:** exact reconstruction, strong integrity, <=8x operation-derived locality, no size regression on protected workloads, no >10% RSS regression, no workload/path/corpus dispatch.

**Gain-retention test:** any rehabilitation candidate must reproduce the R30 byte outcome before receiving runtime credit.

**Exit condition:** restore the frozen release-all-exact create-time floor within the existing materiality law while preserving R30 bytes/locality/RSS, then run the superseding protected-workload/global carrying-cost Builder required by R30. R30 itself does not authorize productization.

## Custody note

The JSON artifact's `source_head` field contains `73f8d8eacf0d837a30d93b38ad3dc920ca6ae2a2`, the GitHub pull-request synthetic merge SHA exposed through `GITHUB_SHA`. That field is **not** the result-bearing checkout authority. The workflow explicitly checked out `ddac8b8b3d0fb4e68511bacaa9185991b2a0cfec` through `EVIDENCE_HEAD`, asserted exact HEAD equality before substrate checks, and the immutable artifact metadata independently records `head_sha=ddac8b8b3d0fb4e68511bacaa9185991b2a0cfec` on branch `agent/v030-authoritative-integration`.

Future result schemas should record an explicit exact evidence-head variable rather than infer source authority from `GITHUB_SHA`. This custody defect does not change R30's measurements or frozen terminal decision, but the synthetic SHA must never be cited as the experiment's checkout head.

## Forge decision

**`REHABILITATE_DEBT`**.

Do not promote `locality-risk-v1` globally yet. Preserve the byte/locality mechanism and attack the regeneration-time owner. A decisive next experiment should first attribute the ~0.1 s incremental cost to regeneration work (rather than selection/predicate/packaging noise) and test the cheapest generic way to avoid or amortize that work while preserving exact output. If rehabilitation cannot recover the inherited runtime floor without surrendering the byte gain, preserve this result as a scoped negative constraint and do not repeatedly sweep the 64KiB threshold family.

## Strongest surviving self-critique

R30 proves the runtime debt on one repaired Incremental Backups family and an isolated projection, not on the full protected workload set. The identical mature-64k/conditional representation decisions make the regeneration owner highly plausible, but R30 did not phase-profile the 180 deterministic regenerations or prove which implementation boundary accounts for the extra ~0.1 s. The next experiment must measure that owner directly before editing the product path.
