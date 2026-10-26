# J24F06/J24F06b — exact-source physical RAW extraction economics, independent held-out interpretation

**Date:** 2026-10-26 UTC. **Status:** RESULT-BEARING SCIENCE, NOT PRODUCT PROMOTION. Released CMPCT remains v0.30.0/r24. Parent is J24F05 PR #540 at `1885cb0658cacd34a50d05e45b541ecb76fc8497`. J24F04 whole-chunk baseline #537 is exact `d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3`. No product bytes, Reader implementation, frozen validator, comparator, format, release, or Discovery state were changed in this lane.

## Preregistrations and exact implementation provenance

- Original J24F06 question/preregistered economics: `d4c0c4a48e5584d49c59439d3664c01f0683b074` **before instrument and observed results**.
- J24F06b additional *separately preregistered* Linux current RSS discriminator: `845a2e835c858fd7986cb455bf801a48e30f7610` **after first result**, before additional observations. It does not retroactively change the original prediction.
- Whole-chunk Reader Git blob `8b5910725260e7b4db155ee0b393eb48a42f7efa`; owned-window Reader Git blob `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`. Same installed supporting native/Python package.
- True revision-24 Builder-independent physical archives, independent signed SHA256, **S_CHUNKS** and **S_CDC**, 16 MiB and 64 MiB RAW payload + 1 KiB second RAW payload. Eight timed executions per case (four each, `whole,window,window,whole` twice), distinct fresh processes. Separate, non-timed stage-write count probes per arm. Total per Actions run = **64 independent timed extracts + 16 separately instrumented controls**, across two OSes. Each output independently reconstructed SHA256-exact; archive SHA/source blob/representation/correct output length verified.

## Hosted evidence and independent verification

| Hosted run / exact HEAD | Linux | macOS | Raw original artifacts |
|---|---|---|---|
| [J24F06 #40401295594](https://github.com/FCMO-AI/.CMPCT/actions/runs/40401295594), `32cc6bc25863c1948185460882d797e506187ecb` | SUCCESS | SUCCESS | Linux [#12688422845](https://github.com/FCMO-AI/.CMPCT/actions/runs/40401295594/artifacts/12688422845), macOS [#12689162000](https://github.com/FCMO-AI/.CMPCT/actions/runs/40401295594/artifacts/12689162000) |
| [J24F06b #40402066013](https://github.com/FCMO-AI/.CMPCT/actions/runs/40402066013), `e2d8ebae37135b4d92770d7d6b93d6eec1a71cc8` | SUCCESS | SUCCESS | Linux [#12688763225](https://github.com/FCMO-AI/.CMPCT/actions/runs/40402066013/artifacts/12688763225), macOS [#12687954869](https://github.com/FCMO-AI/.CMPCT/actions/runs/40402066013/artifacts/12687954869) |

Two separate independent standard-library auditors downloaded and inspected the actual original ZIP JSON, recomputed all medians/deltas, compared source/output/archive identities, ABBA order, fresh PIDs, stage-write counts/bytes, candidate 65,536-byte maximum and complete observations: **702 checks PASS** on initial run; **722 checks PASS** on additional run with Linux current-RSS provenance. These checks corroborate receipt consistency, not a novel independent extractor implementation. No output identity discrepancy. Real stage-written logical bytes match (16MiB+1KiB or 64MiB+1KiB).

### Process peak RSS: consistent macOS benefit, Linux high-water ambiguity

Median candidate (window) vs original (whole), identical source/data:

| Host | RAW size | Representation | Baseline peak RSS | Window peak RSS | Delta | Both hosted attempts |
|---|---:|---|---:|---:|---:|---|
| macOS | 16 MiB | S_CHUNKS | approx. 59 MB | approx. 42 MB | **−28–29%** | yes |
| macOS | 16 MiB | S_CDC | approx. 59 MB | approx. 42 MB | **−28–29%** | yes |
| macOS | 64 MiB | S_CHUNKS | approx. 160 MB | approx. 93 MB | **−42%** | yes |
| macOS | 64 MiB | S_CDC | approx. 160 MB | approx. 93 MB | **−42%** | yes |
| Linux | 16 MiB | S_CHUNKS / S_CDC | approx. 125 MB | approx. 125 MB | **0% measured** | yes |
| Linux | 64 MiB | S_CHUNKS / S_CDC | approx. 377 MB | approx. 377 MB | **0% measured** | yes |

**Linux high-water process RSS is exactly equal per arm** for this test geometry; it cannot be counted as evidence of a Linux peak-memory improvement.

### Independent Linux transfer-point resident memory discriminator

The new Linux-only `/proc/self/statm` observations are taken **in separate traced control processes**, never during timed A/B. Before Reader extraction both arms occupied roughly 24 MB. At **first real RAW stage write**:

| RAW size | Whole immutable snapshot | 64-KiB windows | Current resident difference |
|---|---:|---:|---:|
| 16 MiB | about 58 MB | about 26.6 MB | roughly **31.5 MB** |
| 64 MiB | about 158.8 MB | about 26.7 MB | roughly **132 MB** |

At last stage write both arms converged (~41 MB for 16MiB, ~91.7MB for 64MiB), consistent with source mmap residency growing as bytes were read. The first-write separation supports the *physical* ownership difference and explains why Linux peak RSS alone is not a useful discriminator here, but **does not replace high-water metrics or prove globally lower process memory**. It is a Linux current-residency sample and a controlled lower evidence rung, not guaranteed page-cache decomposition. On macOS these fields intentionally remain null.

### Critical negative: **Linux timing conclusion reversed across source-identical measurements**

Initial same-source Linux extract wall medians: J24F05 **+14–16%** vs J24F04 across four scenarios (CPU similarly +14–16%, absolute >3ms at 64MiB). Subsequent hosted **same Reader blobs, same archive SHA, same CPU type not yet pinned** Linux A/B showed **near parity**, wall/CPU within approximately −0.2% to +0.34% on all four scenarios. Both were full ABBA. The isolated hypothesis that 64-KiB windows impose a *stable 15% Linux regression* is therefore **not established**; neither is a zero-cost claim. Runner conditions, adaptive system behavior or interpreter implementation sensitivity remain alternative explanations. **Preserve both sets of raw samples and the first negative.**

macOS has repeated 64-MiB window **~42% lower RSS** with visibly variable and sometimes favorable wall/CPU (some original whole-chunk runs much slower); 16-MiB CPU/wall results are mixed. Do not claim a universal speed win. The first macOS 16MiB S_CDC CPU delta was **+33.5%** before later near parity, another caution.

### Exported work: stage syscall amplification

Uninstrumented timings were isolated from hooks; separately instrumented real stage writes: **2 write calls** for whole-chunk J24F04, versus **257** for 16MiB or **1025** for 64MiB under J24F05. Same exact logical stage bytes; 64-KiB maximum transfer enforced. The syscall count/exported Python loop cost is a material implementation concern even when actual CPU measurements are ambiguous.

## Decisions, counterfactual, and limits

**Primary scientific decision: `REAL_MEMORY_CUSTODY_ADVANTAGE_WITH_LINUX_TIMING_AMBIGUITY`.** The parent J24F05 candidate preserves source-custody security on its own hostile courts and now has physical macOS RSS and Linux instantaneous RSS evidence. It is **NOT a universally dominant product improvement**; Linux max-RSS benefit did not materialize in this setup and timing noise reverses across hosted attempts. Preserve J24F04 whole-snapshot baseline, do not tune performance thresholds, benchmark corpus, comparators or test safety assumptions.

The earlier mechanism-level `tracemalloc` result could already establish a bounded Python-owned copy but **could not predict** high-water Linux RSS or syscall amplification. Current/transfer-point RSS is a cheaper counterfactual discriminator for that specific ambiguity, after preregistration. There is no justified Discovery Engine policy modification. Stage path substitution [Issue #528](https://github.com/FCMO-AI/.CMPCT/issues/528), mmap concurrent truncation [Issue #460](https://github.com/FCMO-AI/.CMPCT/issues/460), Windows source extraction/metadata parity, complete mixed-codec locality/temp I/O, numerical same-runner release parity and stronger whole-product CI remain **unmeasured/unfixed** in this research lane. No release authority earned.

**Next executable owner action:** before product promotion, source-authenticated additional repeated A/B on explicitly controlled Linux host class to classify varying timing, while independently composing J24F05 with stage-inode publication custody #528. If Linux transfer-loop cost is materially persistent, consider fewer Python/syscall crossings with *the same immutable owned transfer bytes* rather than removing the protection. Do not open another duplicate Reader patch while owner #540/#537 exist.

## Exact-head CI facts and ownership

At exact source `e2d8ebae37135b4d92770d7d6b93d6eec1a71cc8`, scientific workflow 2/2 SUCCESS, Version Discipline SUCCESS, R36 attribution SUCCESS, CI Topology SUCCESS. Engineering Evidence check initially failed from missing PR metadata heading/markers, then passed when the authentic required dossier and falsifiability markers were added; it is a metadata defect, not product functional red. General Tests at the initial observation were **IN PROGRESS** (do not infer success); current exact-head status must be checked again before any further promotion. No numeric performance gate was run by this scientific workflow. This is a stacked research PR, never a release candidate.
