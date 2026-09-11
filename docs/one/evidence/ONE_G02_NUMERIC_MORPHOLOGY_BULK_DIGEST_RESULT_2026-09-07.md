# ONE-G0.2 numeric morphology bulk-digest result — 2026-09-07

## Exact evidence authority

Result-bearing source: `c2e26d8b6b02cce665bf5f1017489415c45accc5`  
Workflow run: `34169919560`  
Job: `101888131598` (`morphology-gate`)  
Runner: Ubuntu 24.04, CPython 3.12.14  
Outcome: **PASS**

The job bound checkout exactly to the evidence SHA, provisioned `.[test]`, ran the hostile morphology suite, then executed the 15-repetition paired resource falsifier.

## Correctness / hostile result

`tests/one/test_morphology_gate.py`: **9 passed in 0.45 s**.

The benchmark additionally required exact equality of generic and candidate run opportunities and reuse opportunities on every row. The result completed green, including the numeric-island counterexample that had falsified the predecessor skip-reuse design.

## Hosted timing result

Frozen gated thresholds were <=0.90x median wall and <=0.90x median process CPU versus generic `observe`. Fall-through controls were capped at <=1.08x.

| family | size | wall ratio | CPU ratio | generic reuse bytes | candidate reuse bytes |
|---|---:|---:|---:|---:|---:|
| diverse_numeric | 256 KiB | 0.3528x | 0.3528x | 0 | 0 |
| numeric_island | 256 KiB | 0.3720x | 0.3720x | 27,200 | 27,200 |
| repetitive_numeric (fall-through) | 256 KiB | 1.0060x | 1.0059x | 260,160 | 260,160 |
| phase_shift_numeric (fall-through) | 256 KiB | 1.0068x | 1.0068x | 243,776 | 243,776 |
| binary_control (fall-through) | 256 KiB | 1.0093x | 1.0091x | 261,888 | 261,888 |
| diverse_numeric | 1 MiB | 0.3514x | 0.3514x | 0 | 0 |
| numeric_island | 1 MiB | 0.3600x | 0.3599x | 139,584 | 139,584 |
| repetitive_numeric (fall-through) | 1 MiB | 1.0186x | 1.0185x | 1,046,592 | 1,046,592 |
| phase_shift_numeric (fall-through) | 1 MiB | 1.0022x | 1.0022x | 1,030,208 | 1,030,208 |
| binary_control (fall-through) | 1 MiB | 1.0063x | 1.0062x | 1,048,320 | 1,048,320 |

On the two intended numeric paths the candidate consumed only about **35–37%** of generic observation wall/CPU, a roughly **2.7–2.85x component speedup**, while preserving emitted opportunities exactly on the matrix. Fall-through overhead stayed about 0.2–1.9%, comfortably inside the frozen 8% ceiling.

The selected path pays an explicit 4096-byte distributed morphology sample. For example, the 256 KiB diverse-numeric row reports 266,240 candidate source-read bytes versus 262,144 generic bytes; the speed win is therefore not produced by pretending the classifier is free.

## What caused the win

The important mechanism-level change is not the morphology heuristic itself. Generic G0.2 observation computes FNV64 with Python integer arithmetic per source byte. The gated path preserves the same opportunity classes but computes a BLAKE2b-64 nominee digest per aligned chunk in optimized native code while run detection remains in the chunk traversal. The result is consistent with removing a large Python arithmetic owner rather than weakening discovery.

## Falsified predecessor

A prior variant used numeric morphology plus sampled diversity to **skip reuse discovery**. Hostile review placed a repetitive numeric island between deterministic sample windows. The classifier still called the root safe while local reconstruction found roughly 10%+ source-scale generic reuse evidence. This disproved the assumption that bounded samples can certify global absence of useful reuse.

That design remains retired. The successful result does not rehabilitate it: the winning successor preserves reuse and uses morphology only to select a faster implementation.

## Strongest remaining critique

The current success may make the morphology gate itself unnecessary. If chunk-bulk native digest nomination is faster while preserving opportunities on structured, random, compressed-like and repetitive roots too, the simpler ONE design is one generic observer rather than a permanent numeric-special writer branch.

`benchmarks/one/one_g02_bulk_digest_generalization.py` and its exact-head workflow were added to test that causal hypothesis. No generic replacement is authorized from the numeric result alone.

Actual peak RSS is also not yet isolated. The algorithmic index payload model is unchanged, but Python object/container overhead still needs process-level evidence before full promotion.

## Promotion boundary

This result promotes the bulk-digest mechanism to broader observer/generalization testing. It does **not** change canonical ONE bytes, reader semantics, selective-read behavior, reconstruction work, integrity, recovery, or the Genesis comparator scoreboard.

If broader generic evidence remains positive, remove unnecessary morphology policy and test one generic bulk observer in the complete ONE writer envelope. If broader evidence is mixed, retain the morphology selector only if its classifier overhead and complexity remain justified. Either path still requires whole-writer creation wall/CPU/RSS evidence and the September 11 same-input comparator gate.
