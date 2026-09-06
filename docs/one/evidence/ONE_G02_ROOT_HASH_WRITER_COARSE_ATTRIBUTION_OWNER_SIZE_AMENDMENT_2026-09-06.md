# ONE-G0.2 root-hash writer coarse attribution — exact owner-size amendment

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`
Parent preregistration: `ONE_G02_ROOT_HASH_WRITER_COARSE_ATTRIBUTION_PREREG_2026-09-06.md`
First result-bearing source: `94f0b81665cb09496b19863b02cf2cf5b3e715a4`
First run: `34041997414`

## Referee finding

The preregistration froze the secondary cross-size owner criterion as >=20% median phase share in at least **2 of the 3 named mature sizes: 16/64/256 KiB**. The first Builder implementation instead populated that secondary map with every size >=16 KiB (16/32/64/128/256 KiB).

This is an implementation mismatch and must not be silently reinterpreted after results are visible.

The primary owner criterion was implemented as frozen: >=25% median phase share across all mature productive rows >=16 KiB. No phase met that criterion in the first result (the largest was segmentation at ~23.21%), so the first `diffuse_root_hash_writer_cost` decision is already robust to the secondary-size mismatch. Nevertheless, terminal authority will come only from an exact rerun.

## Frozen correction

The v2 executable changes **only** the population of the secondary size-consistency map:

- aggregate mature productive phase medians remain over all rows >=16 KiB exactly as preregistered;
- secondary owner-size medians are computed only at 16 KiB, 64 KiB and 256 KiB;
- the >=25%, >=20%, 2-of-3 thresholds remain unchanged;
- workload matrix, 31 paired rounds, timer boundaries, semantic/oracle gates, instrumentation-overhead gates and claim boundary remain unchanged;
- no phase is merged, split or renamed;
- no result-driven optimization is added.

The first run remains preserved as descriptive evidence and as evidence that the instrumentation itself is low-perturbation. The exact rerun supersedes it for the terminal owner/no-owner decision.
