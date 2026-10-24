# O14b preregistration — portable source-mode projection loses filesystem semantics

Date: 2026-10-24  
Status: **PREDICTION ONLY**, committed before O14b instrumentation.

## Baseline
O14 [hosted result 40119076117](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117) confirms the entire installed r24 sample archive becomes byte-identical on Linux/macOS/Windows when only source mode rows are forced to directory 0755/file 0644. That is an exact research observation, not proof that fixed modes can replace the product's fidelity-preserving or documented reproducible modes.

## Primary question / scientific disproof
Does the mode-only projection that eliminates O14's cross-host archive difference also destroy intended POSIX executable, read-only and group-writable file mode semantics even while every content byte remains exact?

Prediction: original authentic `Builder(reproducible=True)` preserves `run.sh=0755`, `locked.dat=0444`, and `shared.log=0666`; O14's fixed-file `0644` projection reconstructs the same contents while losing all three mode distinctions (including `run.sh` execute bits). An alternate simple `mode & ~022` mask would preserve executable/read-only semantics for these files but would still drop group/other-write bits from `shared.log`. All changes are accounted as metadata semantic loss, never as output corruption or compression wins.

## Controls / alternatives
Use the real installed revision-24 Builder and Reader on Ubuntu 24.04, no production changes. Create identical bytes and explicitly `chmod` source files, stat-check each before building; construct control with unchanged Builder, candidate using O14 fixed-mode subclass and an independent mask-only subclass. Strong verify/individual reads/full extract with `metadata=True`; compare *both* payload and resulting `stat.S_IMODE`. Control that original archive mode matches source before claiming loss. Preserve exact complete archive SHA for every arm and output as separate GitHub CI artifact. No use of metadata=False because that would hide physical preservation/loss.

## Decision / kill
Positive: baseline extraction preserves all source permission bits, fixed-mode extraction loses differences as predicted, mask-only preserves executable/read-only but loses intended group write; all content exact. Negative or ambiguous: any historical baseline mode loss, no suitable chmod support, or failed strong verify; preserve failure, narrow scope. The result is Ubuntu ext4/hosted filesystem scientific evidence, not universal POSIX, security, ACL or Windows permission law.

## Architectural consequence
Cross-platform byte-identical output and full native permission fidelity **cannot be inferred simultaneously from the O14 result**. A portable option, if desired, must define an explicit metadata equality class/loss budget and opt-in contract. Neither forcing 0644/0755 nor masking mode bits can silently replace the current fidelity-preserving builder.

## Scope / concurrency
Sibling experiment of O14, same independent PR #372; no changes to Reader/Writer/Builder, release policy, format, owner #352, CI benchmark thresholds or shared discovery cache. No release. If this result confirms predicted semantic export, retire generic *silent* fixed-mode productization and return to more diverse opportunities rather than tuning mode masks against fixtures.
