# ONE-G0.2 numeric morphology gate preregistration — 2026-09-07

## Mission lock

Repository authority identifies deployed ASCII-numeric roots as a measured red for generic fused observation: the generic fused observer can add writer cost where the older path already avoids the redundant stride scan. This experiment attacks that red without adding any reader-visible mechanism.

Activation T0 was recorded as 2026-09-07T17:09:12-06:00.

## Current hypothesis

A bounded morphology classifier can select a **bulk chunk-digest implementation** for sufficiently large, strongly numeric ASCII roots, reducing observation wall/CPU time while preserving the same run and reuse opportunity classes and exact proof semantics as generic observation on the hostile matrix.

The classifier selects writer implementation only. It no longer authorizes deletion of reuse discovery. ONE bytes, Law + Surprise semantics, reader execution, locality, integrity and recovery contracts are unchanged.

## Falsified predecessor preserved

The first design skipped reuse fingerprinting outright on numeric-looking roots. It was tightened once to require sampled chunk diversity and again to distribute the same 4096-byte sample budget across eight deterministic windows.

Hostile review then constructed a stronger counterexample **before any completed hosted scientific result**: a diverse numeric root with a repetitive numeric island placed between deterministic sample windows. The classifier still gated it while the generic observer found roughly 10%+ source-scale reuse evidence in local reconstruction. That disproves the premise that bounded sampling can certify global absence of useful reuse.

The skip-reuse design is therefore retired. Adding more windows would only make the counterexample more annoying, not remove it.

## Reformed builder

`experiments/one/morphology_gate.py` now uses the same bounded morphology evidence only to choose implementation:

- at most 4096 sampled bytes across eight deterministic windows;
- minimum input 16 KiB;
- >=98.5% numeric/delimiter alphabet membership;
- >=35% digit density;
- >=90% sampled 64-byte chunk uniqueness;
- when gated, run observation and 64-byte reuse fingerprinting are both preserved;
- gated fingerprint nomination uses deterministic BLAKE2b-64 computed on aligned chunks in optimized native code rather than per-byte Python FNV64 arithmetic;
- exact byte equality remains mandatory before reuse opportunity emission;
- collision buckets remain bounded by the existing `max_index_entries` contract;
- ungated inputs delegate exactly to generic `observe`.

The selected path consumes the root in aligned chunks; run detection iterates the chunk bytes while the digest operates on the same temporary chunk. The 4096-byte morphology evidence is charged as extra source traffic. Algorithmic retained index payload uses the same 8-byte digest + 8-byte retained-offset lower-bound model as generic observation; actual Python RSS still requires hosted/process measurement.

BLAKE2b and FNV64 have different collision partitions, so opportunity identity is not assumed axiomatically. It is an explicit hostile-test and benchmark invariant on the current matrix. Exact reconstruction safety is stronger than fingerprint identity because every emitted reuse still requires byte equality.

## Frozen falsifier after reform, before result authority

`benchmarks/one/one_g02_numeric_morphology_gate.py` uses 256 KiB and 1 MiB roots, 15 paired alternating repetitions, and five families:

1. diverse numeric ASCII — morphology selects bulk digest;
2. numeric root with a repetitive island deliberately located between sample windows — morphology selects bulk digest and **must preserve generic reuse exactly**;
3. repetitive numeric ASCII — must fall through;
4. diverse-prefix / repetitive-tail numeric phase shift — must fall through;
5. binary control — must fall through.

Promotion gates are frozen before hosted result authority:

- every row must preserve generic run opportunities exactly;
- every row must preserve generic reuse opportunities exactly on the matrix;
- gated numeric wall ratio <= 0.90 versus generic observe;
- gated numeric process-CPU ratio <= 0.90;
- fall-through families must remain <=1.08 wall and CPU;
- every ungated observation must equal generic observe exactly.

No threshold may move after observing CI output to manufacture a pass.

## Disproof / retirement conditions

Reform or retire the bulk-digest selector if any of the following occurs:

- gated numeric roots fail to achieve the preregistered 10% wall and CPU reduction;
- run or reuse opportunities diverge on the hostile matrix;
- collision behavior creates materially worse discovery on broader corpus evidence;
- fall-through overhead exceeds 8%;
- the classifier/digest path becomes a material memory-traffic or RSS owner in whole-writer profiling;
- end-to-end stored bytes regress materially after planner integration despite observation-level parity.

A component pass is not a Genesis scoreboard win. If positive, this path still has to earn value in the complete writer envelope and at the 2026-09-11 same-input comparator gate.
