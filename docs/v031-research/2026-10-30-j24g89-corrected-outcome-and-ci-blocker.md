# J24G89 — corrected O0 replay-only evidence and hosted route blocker

Date: 2026-10-30 UTC. **Research outcome: `AMBIGUOUS_10_TO_20_PERCENT`; product credit ZERO.** Frozen preregistration `c5c243a1621fb75d25cfaeed28bda5d881938c23`. This document supplements, never rewrites, [the original prereg](2026-10-30-j24g89-owned-replay-headroom-prereg.md) and [source-alignment correction](2026-10-30-j24g89-source-aligned-correction.md).

## Core question, stronger control, hypothesis and result
Does removing only the 63 one-pass DELETE operations from an already-private optimized signed-history Reader offer enough *complete CPU/work* savings to justify adding a K32 new-format checkpoint, after charging authenticated original snapshot decoding and public lookup work? The generous free-DELETE oracle does not avoid existing signed footer/decompression obligations. Stronger control is the original authenticated r24 29-byte one-op delta and existing #823 owned decoder; checkpoint #842 adds 136–144 bytes and new Reader grammar, never free.

Two authentic J24G83 physical archives were recovered from finished hosted evidence #41061290836; 65 signed linked generations per source, 63 original deletes, checksum/footer corruption refusal, and exact generation64 full-index survivor consistency checked independently. Local research instrument uses libzstd+msgpack and no CMPCT import.

An early local script double-decoded the full N-member base index and led to **invalid ~5%** replay fractions. See correction note for explicit source-exact #823 Reader semantics. No post-result threshold was moved. The **corrected** source-aligned pass decodes the signed checkpoint once, processes 63 delta payloads, applies one set of deletes, and builds a consumer dictionary.

## Corrected local physical-data stage results (two separate 151-sample repeats)
| Authenticated archive | Pass | Primary signed snapshot decode+SHA+MessagePack | 63 signed deltas parse+SHA | One-pass DELETE filter | Lookup materialization | Fraction of staged wall in DELETE |
|---|---|---:|---:|---:|---:|---:|
| 8,192 / middle | A | 79.39% | 1.97% | 9.94% | 8.70% | **10.130%** |
| 8,192 / middle | B | 78.70% | 2.09% | 10.50% | 8.71% | **10.492%** |
| 32,768 / tail | A | 78.93% | 0.51% | 9.68% | 10.88% | **9.881%** |
| 32,768 / tail | B | 78.45% | 0.54% | 10.20% | 10.81% | **10.348%** |

Columns with stage percentages are based on the ratio of separately obtained median stage times, while the rightmost replay fraction is the **median of individual per-sample ratios**. Those are subtly different statistics and must not be conflated. Warm per-sample staged totals for A/B are 4.969/4.479 ms at 8192; 20.124/18.602 ms at 32768. Fully gifted zero-DELETE-work-only ceilings are approximately 1.110–1.117×. CPU ratios agree in broad direction, but are not production benchmark CPU measurements.

Secondary independent resampling (3000 IID bootstrap resamples, not accounting for autocorrelation) produced approximate *median wall share* intervals: 8192 A [9.909,10.294]%, B [10.350,10.630]%; 32768 A [9.663,10.049]%, B [10.257,10.453]%. These illustrative intervals reinforce **boundary sensitivity** but are not cross-host confidence intervals or a reason to retune the 10% criterion. The prereg decision is AMBIGUOUS because both inputs are not strictly below 10% across independent repetitions.

## Exact HEAD / CI route evidence
Research workflow on PR #845 originally failed at first source CI because default shallow checkout could not resolve immutable prereg commit: [Actions #41096583729](https://github.com/FCMO-AI/.CMPCT/actions/runs/41096583729), before any physical measurement. This **CI method defect** was corrected with complete fetch ancestry in `61372f5979b64f3080b4a02c252c42a9b3f5c818`.

Follow-on [Actions #41096841307](https://github.com/FCMO-AI/.CMPCT/actions/runs/41096841307) **PASSED ancestry and dependency setup**, but failed at the original source GitHub artifact download due to **HTTP 503: Azure workflow artifact egress is over the account limit**. It did not execute the research script. Do **not** interpret this as a scientific negative, or as evidence of hosted performance success. Original physical input remains previously verified and available to local independent reproduction. The scientific decision is based on corrected local repeated source-data measurements only; hosted rerun remains blocked by provider egress rather than code behavior.

Engineering Evidence initially flagged missing required PR `disproof`/`quality-ratchet` markers; those markers were supplied without changing evaluator or historical gate, and exact [run #41096860325](https://github.com/FCMO-AI/.CMPCT/actions/runs/41096860325) finished **SUCCESS**. Exact version discipline #41096841216 and R36 #41096841591 succeeded. General/CI topology were pending at the result cut; their final status should be read from live GitHub rather than guessed.

## Limits / counterfactual / continuity
The source-aligned independent Python loop is **not** source-exact installed #823 `OwnedCMPCT`, and does not measure footer backward discovery, same-runner actual Reader A/B, physical cold I/O, process startup, RSS, native/Windows/macOS, parser safety limits, signed xattrs/hardlinks, Writer concurrent leases or promotion parity. A hypothetical new checkpoint may affect proof-path cost differently than merely eliminating one-pass DELETE work. The original pre-owned 97–98% incremental replay attribution from #809 does not survive unmodified into a one-pass decoder.

**Decision-changing evidence:** the initial incorrect ~5% was overturned by inspecting real Reader control flow and eliminating double charging. The resulting 9.9–10.5% border is not material proof to retire or promote this family. Counterfactual discriminator potentially generalizable: before any O0 budget attribution, audit which physical full-index stages the *real* Reader executes once, then separately charge auth/proof and execution work; this single episode is not enough to modify global discovery policy.

**Next best executable:** when artifact route is restored, run the exact GitHub script and independently recompute its raw receipts; then, if the threshold remains material, conduct a **single** source-exact #823 Reader A/B instrumentation on the actual same physical archive without creating a new-format checkpoint. Current owner #823/#820 must coordinate that product seam. Meanwhile prioritize independent product hardening (#749 verified/published inode, #836 session/cooperative lease, #574 state reconciliation). Do not overwrite `docs/discovery/STATE.json`, alter release rules, or merge this Draft research PR.


---

## Late hosted evidence — provider route recovered without modifying the mechanism (2026-10-30 UTC)

**Do not erase the 503 failure above.** The later independently launched [exact source workflow #41097287582](https://github.com/FCMO-AI/.CMPCT/actions/runs/41097287582) **SUCCEEDED**, including immutable prereg ancestry, download of original J24G83 physical evidence, all signed SHA/footer/63-delete/checkpoint64/tamper checks, and 151 paired hosted samples per case. The earlier Azure 503 was transient infrastructure route failure, not a scientific rejection.

- Original [provider raw ZIP artifact #12996897450](https://github.com/FCMO-AI/.CMPCT/actions/runs/41097287582/artifacts/12996897450), **ZIP SHA-256 `109462171cfde8c1d12c3edce8810f34675668ad5f5051f1c6756e89a15b91c9`**. Downloaded again through the connected artifact service, verified exact ZIP checksum; recomputed both median replay shares from **151 physical-source samples each** with an independent offline Python routine and validated ZIP integrity. Source archive SHA-256: 8,192 `5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a`; 32,768 `8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81`.
- Hosted original CI `j24g89-result.json` records run checkout GitHub's PR **merge-ref** `359055c6a77f6150fd9ebbb413a0a796f5e9f17b` (NOT identical to PR source branch HEAD `bd65ca78697f00d3347d2c2f7618e7eee076744d`). Source script bytes and branch identity remain separately pinned by the artifact script-SHA file, immutable prereg ancestor and branch metadata. Do not conflate merge-ref with branch HEAD.
- Hosted Ubuntu CPython 3.11: 8,192/middle replay fraction **8.9382855366%**, total staged wall **5.291659 ms**, zero-replay-only generous speed ceiling **1.098156×**; 32,768/tail replay fraction **4.9175358766%**, total staged wall **51.324768 ms**, ceiling **1.051719×**. Local corrected CPython 3.13 two repetitions remain **10.130/10.492%** and **9.881/10.348%** respectively. The different source-aligned Linux runtime/host measurements **do not agree on the frozen <10% decision** at both sizes.

**Primary hosted-source decision:** `REPLAY_WORK_LOW_FRACTION_O0` on this one hosted Ubuntu runner (both under prereg 10%). **Broader cross-environment disposition: `LOW_ON_HOSTED__BOUNDARY_SENSITIVE_LOCALLY`**, not a claim that K32 checkpoints cannot help any real Reader. Do not overwrite or reclassify the local ambiguous result, and do not declare a universal family retirement or product acceleration. The differences may involve CPython runtime, environment, stage implementation or cache/instrument semantics; only a source-exact installed #823 Reader phase court can adjudicate transfer.

Current exact source CI specialized run **SUCCESS**; Engineering Evidence #41097521468, Version Discipline #41097287481, topology #41097287306 and R36 #41097287316 **SUCCESS** on branch code before this documentation-only append. Full General CMPCT Tests #41097287448 were **in progress at the late evidence cut**, must be checked separately on latest HEAD. Other independent official performance and release gates were not executed. No product code changed; no merge/release.
