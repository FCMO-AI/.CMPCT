# CMPCT1 / ONE Genesis gate readiness V2 preregistration — 2026-09-09

Experimental state: **ONE-G0.2**  
Branch authority: `research/cmpct1`  
Claim boundary: **non-scoring gate-readiness infrastructure only; this does not execute or preview the 2026-09-11 Genesis decision.**

## Mission lock

The first two readiness attempts exposed infrastructure/substrate defects before any candidate or comparator encoding was allowed:

1. the first lane could not regenerate the deterministic media workload because its hosted runner lacked `ffmpeg`;
2. after that dependency was supplied, source `67e88ec2b0e0f9364cda9ac69be91d412882232b` reproduced 14/15 accepted workload identities and both frozen comparator SHAs exactly, but `neutral_hostile_v1/01_developer_repository` retained the same file count and logical byte count while its tree hash drifted.

The second failure has a concrete harness owner. `benchmarks/mosaic_v029_generalization_bench.py`, which is the accepted v0.29 portable-frontier authority consumed by readiness, now obtains its neutral repair identity and producer from **determinism repair-v6** (`benchmarks/neutral_hostile_determinism_repair_v6.py` plus `benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json`). Repair-v6 was accepted specifically because repair-v5 left two developer-workload ELF fixtures dependent on host GCC/linker provenance. The V1 readiness harness nevertheless regenerated neutral rows with repair-v5 while comparing them with `_preserved_rows()` identities already upgraded to repair-v6.

Therefore the observed developer hash mismatch is expected from an internally inconsistent readiness harness; it does **not** authorize changing any expected tree hash.

## Hypothesis

If readiness uses the same already-accepted repair-v6 authority for both expected identities and neutral-workload generation, then all 15 workload identities should reproduce exactly on the hosted runner while the frozen v0.29 and v0.30 checkouts remain exact.

## Disproof / HOLD

V2 remains `HOLD_GATE_READINESS` if any of the following is true:

- the workload set is not exactly 15 rows (10 neutral + 5 resemblance);
- any workload file count, logical byte count or tree SHA differs from the accepted identity returned by the v0.29 generalization authority;
- `01_developer_repository` does not match repair-v6 accepted tree SHA `d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49`;
- any other accepted repair-v6 neutral row drifts;
- frozen v0.29 HEAD differs from `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- frozen v0.30 HEAD differs from `f4b158a55a08b9b18b50e4e4abe4b9251048c772`;
- the lane performs CMPCT1, v0.29 or v0.30 encoding/scoring;
- the lane changes expected hashes, corpus semantics, comparator settings or the September 11 decision contract.

## Allowed repair

V2 may only reconcile the readiness harness with the **pre-existing accepted repair-v6 substrate authority**. It may install deterministic media dependencies already required by the accepted corpus producer. It may not change workload bytes or expected identities.

The old V1 readiness harness and its failures remain evidence. V2 is a corrected authority-binding lane, not a rewrite of history.

## Required V2 output

The machine-readable manifest must preserve:

- exact CMPCT1 source SHA;
- exact v0.29/v0.30 checkout SHAs;
- all 15 names, file counts, logical byte counts and observed/expected tree hashes;
- explicit `scoring_executed=false`, `candidate_encoding_executed=false`, `comparator_encoding_executed=false`;
- the exact repair identity used (`neutral-hostile-repair-v6` where applicable);
- an admissible decision of only `READY_FOR_GENESIS_GATE` or `HOLD_GATE_READINESS`.

A V2 `READY_FOR_GENESIS_GATE` establishes only that the exam substrate and frozen comparator identities are reproducible. It says nothing about which system wins on September 11.
