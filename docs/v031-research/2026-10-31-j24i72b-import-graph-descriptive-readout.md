# J24I72b — Import-graph attribution discriminator (post-result, prospective readout)

**Date 2026-10-31 UTC. Status prospective to adding a new *reporting* stage, not prospective to the completed J24I72 result.**

## Immutable starting observation
Original J24I72 exact-head `7dedc86bf433bef8208918c91e5ab446620b29f5`, Actions `41157356706` on Ubuntu/Windows, finished scientific court SUCCESS; preregistered H1 (gross Owned-A over Public-A) passed at N8192 on both hosts, H2 (gross Owned-A over Public-B checkpoint <=1.20x) failed on both hosts. **These results are frozen; this second question cannot reclassify either hypothesis.** Source archives, raw observed medians, complete artifacts and independent original referee remain intact. J24I72b is not a replacement benchmark, promotion vote or optimization.

## New question and counterfactual
The private `OwnedCMPCT` class is defined in `research/j24g74_owned_decoder_court.py`, which imports research helper modules `j24g73_reader_open.py`, `j24g64_mixed_fsmeta_oracle.py`, and their original Writer/Builder/scientific instrumentation. The published public Reader class does not import those research helper modules. Is the 35–38% gross owned-A/checkpoint-B difference partly an *import-graph effect* rather than just journal replay? At minimum, do observed per-child import timings and import-only-process medians reveal a large differential in the predicted direction?

## Cheapest evidence rung
Reuse the exact code's **already-produced and originally audited raw per-phase data** if accessible; current run original artifact URLs and provider SHA identities are preserved in PR comments. If the runtime cannot independently retrieve those binary ZIP bytes, run one exact same-protocol source-locked hosted replication that only adds an after-the-fact **descriptive stdout summary** derived from original in-run receipts. No changed original hypothesis/evaluator, no new archive fixture, no codec or runtime modification. Source sample sizes and ordering remain 8 subprocesses per Reader/archive/size, 4 import-only subprocesses per Reader/size on Ubuntu and Windows.

Report actual medians of: (i) parent-observed complete process wall, (ii) child-selected-class import wall, (iii) child Reader constructor wall, and (iv) import-only process wall. Also report full-process variability between first and second hosted runs. These components are **not algebraically additive at the median level**; do not subtract independent median components to claim causal attribution. Independent import-only process cost is a stronger control for module graph effects, not a measure of Reader core work.

## Decisive boundaries and failure
- If `OwnedCMPCT` import time is materially higher than public across both hosts, classify **IMPORT_GRAPH_CONFOUND_PLAUSIBLE**; do not attribute H2 failure entirely to imports absent same-source module ablation.
- If import differences are small relative to gross H2 gap and constructor differences account for most variation, classify **INTRINSIC_REPLAY_GAP_REMAINS_PLAUSIBLE**, not proven; new correct-source integration gate still required.
- If host signs contradict, raw process variance is large, or source/physical identity differs, classify **AMBIGUOUS**, retain original H1/H2 outcome and stop this local family without threshold gardening.
- Fail all evidence claims if row labels, git blobs, physical archives, per-iteration source or original detached referee change. The original hard H1/H2 labels must be carried through unmodified.

## Ownership and safety
Only descriptive CI/readout on original #875 research branch. #823 owns original `OwnedCMPCT` source, #853 owns original DELETE-only control and #871 owns source-locked A/B physical comparison. No Reader, Writer, native codec, actual SHA, format, release, optimizer, frozen benchmark, Discovery engine or evaluator modification. H2's already-confirmed negative remains a valid gross-process result for those exact research classes and physical workloads. Any source-integrated, import-graph-normalized product candidate must be a separate source-owner-controlled study with correct semantics and release gates.
