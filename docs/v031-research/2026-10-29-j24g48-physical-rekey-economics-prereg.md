# J24G48 — preregister source-exact physical Reader journal-rekey cost court
Date: 2026-10-29
Status: PRE-RESULT. This is a separate research-only child of product owner PR #773; no product changes, no release claim.
Base: J24G47 repair head `893aac3f6b7b54e89d71af6970405ff5fc71aef7`.
Control: defective J24G46 head `78b9dd2d148350898c95a0cdbeefe760de2e567e`.

## Primary question
Does preserving the correct `fsmeta` member identity across a signed revision-24 lexical-insertion journal impose a decision-changing cold Reader open/CPU/RSS cost in a *real Builder-produced archive*, beyond the O(N) helper micro-measurement already obtained in #773?

## Baseline, mechanism and alternatives
J24G46 physically authenticated the positional metadata defect; J24G47 fixes it with an O(N + sparse-records) lineage mapping only when rows or identities change. Existing abstract 10,000-row helper measured 18.6–40.7 ms for a lexical insertion, but does not include real signed archive parsing, Reader startup, VM/RSS, source import, or the effect of sparse xattr density. The simplest control is source-exact #770 Reader, demonstrably wrong on the same input, **not an equivalently correct product comparator**. Also compare the J24G47 candidate's own unchanged base vs shifted archive to distinguish journal decoding from rekey cost.

## Experimental design, locked before instrumentation
- Source-exact two checkouts within one Ubuntu 24.04 runner, Python 3.11; installed candidate dependencies, forced `PYTHONPATH` to each pinned Git source, assert source SHA and module path.
- Build each fixture exactly once with the inherited real Builder, `reproducible=False`, bytes generated solely from member name; 256/2,048 small files; 0%, 1/32 and 1/2 genuine Linux `user.*` xattr coverage.
- Append one lexically *earlier* new member once with inherited genuine Writer; all reads of the original and shifted archives reuse identical immutable physical input files for both code versions.
- Measure subprocess-isolated import separately from Reader open/list; interleave source orders ABBA and operation orders; retain individual wall, CPU, process peak RSS and archive bytes plus SHA-256 for each observation. At least 7 repeats per source/case when runner permits; do not infer full extraction throughput.
- Independently name-key expected metadata from filesystem source, require repaired Reader to preserve it and pre-repair Reader to reproduce the negative at nonzero xattr coverage; no genuine improvement may be purchased by weaker semantics.
- Timestamp and record exact source, runner, platform, workload fingerprint, seed, outputs and artifact paths.

## Prediction, decision and disproof
Prediction: source-correct Reader retains all original xattrs; source-defective Reader misbinds at least one on nonzero-density shifted archives. Candidate's incremental cost will grow with index/member count, and dense sparse records will be higher cost. A repeated additional open cost exceeding **20 ms absolute** and **10% relative** at 2,048 members is material research debt to investigate; peak-RSS overhead exceeding **5 MiB** relative to the prior source is material. These are prospective research triage thresholds **not CMPCT release gates**, and the baseline is semantically invalid. An absence of stable source-confirmed measurements, accidental different input bytes, unexpected metadata semantics or a stronger inherited failure invalidates a cost conclusion. No preregistered threshold can waive a released product gate.

## BONK / rivals
Compare (a) accepting current measured O(N) helper as bounded and prioritizing product integration; (b) real physical cost court here; (c) premature speculative data-structure optimization; (d) another unrelated architecture family. Choose (b) because physical scaling is an explicit unpaid claim blocking reliable promotion economics and is cheapest to decide before code optimization. Do not invent a new metadata schema or rewrite the owner PR.

## Scope and handoff
Experiment/CI/evidence only; do not mutate `reader.py`, `transactions.py`, benchmark contracts, frozen tests, `docs/discovery/STATE.json`, format, release, version or other agent branches. Preserve raw noise, negative evidence, support limits and all failures. This is performance/correctness research, not proof of full create/extract economics, multihost portability or ZIP/Zstd dominance.
