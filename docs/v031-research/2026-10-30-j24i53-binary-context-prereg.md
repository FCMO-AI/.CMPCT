# J24I53 — Binary Builder create context-lifetime falsifier (prospective)

Date: 2026-10-30 UTC. Research-only, no product/format/ABI/release changes. Exact parent: PR #816 at `1c073d024111be00a1246e67b1138a3d4232b3b9`, incorporating PR #807 candidate `0b80ecb9b1742a6c20756f4c9e8e097103881cb4` and the negative native primitive experiment J24I52. Published main stays v0.30.0/r24.

## Primary question and measured baseline

Does the *unchanged* real binary/library/Builder operation become consistently slower within one persistent Python process after executing the canonical `tiny -> source -> media` library-create prefix, compared with the same operation in a fresh Python process without that prefix? The original #807 same-source official r24/ZIP ABBA had two candidate-labeled binary/library create failures: base/candidate 171.668/199.447ms (+16.18%) and 141.103/161.638ms (+14.55%). Same complete `src/` tree; #816's corrected native FFI micro A/B was neutral (-0.10%). CLI library/create controls from the same two official runs were ~+0.21% and ~+1.05%, respectively. These original gates remain promotion vetoes.

## Hypotheses, simpler control, and disproof

H1 (context/lifetime effect): with identical pinned #807 code and same immutable binary corpus, prefix-conditioned child processes have reproducibly greater **wall and CPU** median binary Builder creation cost than fresh-context child processes. Strong simpler control: source-identical A/A sham process labels both execute FRESH with the same ordering and number of timed operations. Alternative H2: runner/corpus chronology and dynamic noise shift measurements without a prefix-specific CPU effect; prefix output may be cache warming and make FASTER, not slower. Another alternative is original full eight-corpus ABBA label/order confounding, which this small court cannot reproduce.

Preregistered decisions: `CONTEXT_COST_SUPPORTED` only if two balanced four-arm groups show same positive sign, median prefix/fresh cost exceeds **both +5% and +3 ms** in wall and CPU, and same-source FRESH/FRESH sham has neither a gate-scale cost nor nondeterministic archive bytes. `CONTEXT_COST_NOT_REPRODUCED` if prefix effect fails those criteria with valid corpus/output provenance and stable sham; `AMBIGUOUS` if sham reaches the threshold, CPU and wall disagree, or signs differ. The 5%+3ms criterion is a *scientific materiality discriminator*, never a release gate substitute. Invalid source, nondeterministic archive bytes, two different corpus trees or missing physical evidence => `INVALID`.

## Execution and evidence contract

1. Use a single installed candidate source checkout and physical native library from the exact inherited #807 commit, verified by Git ancestry and `cmpct` import provenance; do not rewrite Builder, codec, or official benchmark scripts.
2. Generate the standard public deterministic `benchmarks/universal_bench.py::make_corpora()` tree *once*. Freeze its binary/source/media/tiny bytes and metadata for the entire court. At minimum retain binary file SHA-256s and entire generated-tree fingerprint; no per-arm regeneration.
3. Run balanced `FRESH PREFIX PREFIX FRESH` and `PREFIX FRESH FRESH PREFIX` groups in independent child processes with 3 timed repetitions (after exactly one immediate untimed binary warmup). In PREFIX before warmup, use the same real Builder on tiny/source/media in that order, writing to temporary output; FRESH does no prefix. Separately run analogous FRESH-A/FRESH-B sham with identical code. Child startup/import and warmup are measured separately from the three binary timed closures; source and bytes must match.
4. Capture every wall/CPU sample, child RSS, source commit, environment, file counts and physical archive hashes/sizes. Calculate per-group and global distributions, retain raw JSON and at least one physical binary output archive for detached verification; report prefix elapsed CPU/wall and archive sizes, never silently export those costs.
5. Run on GitHub Actions Ubuntu 24.04 Python 3.11. Expect artifact `cmpct-j24i53-<exact HEAD>`. No user-facing speed claim until independent downloaded receipt audit, and no release/merge without inherited gates.

## Prior work and concurrency

PRs #238/#711/#715 already own **different source-bound** A/A/ABBA studies, and #711 has a prefix experiment at #699/#704. Do not duplicate their files/PR branches, and do not claim new general discovery if our result only replicates their mechanism. #816 owns direct native-codec A/B. #807 owns the C ABI. #574 owns discovery STATE reconciliation. This is a narrow independent #807 source-bound context transfer question. `docs/discovery/STATE.json` is staleable and is not written.

## Boundaries and future leverage

No compression gain, encoded-byte change, selective-read/verify improvement, format revision or algorithmic improvement is claimed. Prefix can legitimately alter filesystem cache and CPU thermals; matched results are causal *within this experiment's source/context*, not proof of why historical #807 base/candidate labels diverged. If prefix has no convincing cost, return to full-gate chronology/source-identical A/A physical receipt discrimination rather than rewriting unrelated Builder code. If prefix has a large cost, instrument the expensive prefix's persistent global resource owners before touching threshold or release policy. Do not weaken any frozen evaluator.

Counterfactual: if history-specific same-source A/A had been used as the first local witness after the #807 red, it could have eliminated or supported process context before probing native codec. This remains a **prediction** until hosted evidence; no discovery-policy change earned.
