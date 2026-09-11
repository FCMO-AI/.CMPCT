# ONE-G0.2 — Exclusive non-zero-shift gate causal result — 2026-09-05

## Authority and claim boundary

This is writer-discovery research evidence only. It changes neither the ONE reader ontology nor stored representation bytes and grants no v0.29/v0.30 comparator or release authority.

Result-bearing source: `a0c5c05ae87ac414384211a09cc160a0389244d0`  
Workflow: `33960086736` (`CMPCT1 ONE-G0.2 exclusive shift opportunity gate`)  
Job: `101290347180`  
Artifact: `9967653819`  
Artifact digest: `sha256:9201698d8fba1a3dc0f64a493647f65b962bfed05624dea0ea0dc1891afdee55`

All ONE semantic tests in the workflow passed before the falsifier.

## Referee hypothesis

The immediately preceding sparse FNV shift gate retained the two known positive-marginal shifted cases but was retired because:

1. shift-invariant zero data falsely satisfied the non-zero shift signal; and
2. the 16 KiB shifted-rescue probe cost `0.0835503x` the avoided promoted-selector increment, above the frozen `0.05x` budget.

The superseding experiment kept the inherited `4/8` evidence threshold unchanged. It changed the evidence definition instead: a sample can contribute non-zero displacement evidence only if zero-shift equality fails. If zero shift already explains the sample, non-zero comparisons are skipped. FNV hashing was replaced with exact 64-byte equality in 8-byte words with early exit. Actual modeled reads were charged on both sides.

Frozen pass law: preserve every positive-marginal case, reject every zero-marginal case, remain <=`0.05x` selector increment on every input >=8 KiB, and read <=25% of each such input.

## Exact result

Decision: **`advance_exclusive_shift_gate`**.

The gate enabled exactly the two positive-marginal cases and no others:

- `shifted_version_pair_1byte_insert`: +524,288 B marginal reuse opportunity, 8/8 exclusive +1 matches;
- `starved_shifted_basis_8k_insert1`: +8,192 B marginal reuse opportunity, 8/8 exclusive +1 matches.

The previous zero-data false positive disappeared: `zeros_1mib` had 8/8 zero-shift matches, 0 exclusive non-zero matches, and was not enabled.

### Cost at the former failure boundary

`starved_shifted_basis_8k_insert1` (16,385 B):

- old sparse FNV probe median: 3,154 ns;
- exclusive exact-equality probe median: 772 ns;
- new/old probe ratio: `0.24477x`;
- new probe / avoided selector increment: `0.01993x`;
- modeled bytes compared: 1,536 B (`0.09374` of input).

The neighboring zero-marginal 16,384 B repeated case used 721 ns, `0.01855x` selector increment, and 1,024 modeled compared bytes (`0.0625` of input).

### Large ordinary controls

Representative 1 MiB probe medians were 731–781 ns. Random and zlib-random-like data read only 640 modeled bytes because exact word comparison exited on the first unequal word of almost every candidate. Probe/selector-increment ratios were about `0.00024x–0.00026x`.

The causal win is therefore not a looser admission threshold. It comes from asking a narrower question and avoiding work whenever zero-shift equality already explains a sample.

## Hostile reviewer

This pass does **not** establish a general discovery gate. Eight deterministic point samples can be phase-attacked: a globally useful shifted relation may be damaged only at those points while remaining profitable elsewhere. A follow-up hostile transfer was therefore frozen without changing threshold, positions, or shifts. Its preregistered disproof explicitly retires deterministic point sampling as a sole admission signal if any positive-marginal hostile case is missed.

Transfer harness: `benchmarks/one/one_g02_exclusive_shift_gate_transfer.py`  
Transfer workflow: `.github/workflows/cmpct1-one-g02-exclusive-shift-transfer.yml`

## Current decision

**Advance to hostile transfer; do not product-promote.**

If hostile transfer passes, the remaining debt is to fuse this signal into already-paid observation traffic and then measure complete encoder work. If hostile transfer fails, preserve the failure as evidence that deterministic point sampling cannot be the sole gate; do not respond by hand-picking more sample points or relaxing the frozen threshold.
