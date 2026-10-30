# J24G61 — source-exact public single-delta Reader-open cost attribution

Date: 2026-10-30 UTC  
Status: **DECISIVE ON TWO HOSTS; macOS ATTRIBUTION INCONCLUSIVE UNDER PROSPECTIVE INSTRUMENTATION GATE. Research only, not a release or product speedup.**

## Authority, provenance, immutable comparator

- Published CMPCT v0.30.0, on-disk revision 24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`, unchanged.
- Exact inherited research parent: #800 `fb5d96cdb8855fe3e01868792e65b79d3d61661d`, sharing fail-closed signed journal source from #795 `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`.
- Prospective J24G61 prediction `8eaa7460825fde317aa7338db3f557a2dd9e45bf`, before instrumentation. No change to thresholds after observing data.
- Original J24G61 code result HEAD `4cd27462e9f19dbdb0e523a2283680089e2b4eb2`, hosted [run #40998138423](https://github.com/FCMO-AI/.CMPCT/actions/runs/40998138423). Independent in-repo audit added without modifying product files; later tested at head `e21a3cfe75931b9ca48578a38b8a363eaa9bdae2`, hosted [run #40998543593](https://github.com/FCMO-AI/.CMPCT/actions/runs/40998543593), **SUCCESS on Ubuntu 24.04, macOS 14, Windows 2022**.
- J24G60 physical same-state baseline: real public Writer produces one operation per generation, 63 generations, followed by a 64th checkpoint. Its 2048-member 63-deep chain vs same-logical-state additional checkpoint had 24.857 / 33.632 / 54.303 ms open-only savings on Ubuntu/macOS/Windows. Its checkpoint was synthetic and carried **+12,659 bytes, +4.3294%**, not a shipping same-state public Writer action.

## J24G61 final audited outcome

The new experiment reused all 5 exact #800 source-blob identities, built physical Builder archives with 512 and 2048 members and true public Writer rename histories, and checked SHA/footer lineage, exact effective indices, files, strong verify and bounded preflight. Four cases: N=512,d63 and N=2048,d1/d32/d63; 4 ABBA/BAAB blocks per case × 4 processes per block, plus two uninstrumented ABBA blocks at N=2048,d63. Exactly **72 raw fresh-process observations per host / 216 total**. Process/import time is outside the measured span, disk page cache uncontrolled.

For primary N=2048, d=63, results at **later fully audited HEAD `e21a3cfe`**:

| Host | Wrapped chain / same-state checkpoint open | Extra chain wall | Replay function span | Fraction of extra chain wall | Separate unwrapped-penalty perturbation | Prospective decision |
|---|---:|---:|---:|---:|---:|---|
| Ubuntu | 28.448 / 2.905 ms | 25.543 ms | 25.119 ms | **98.34%** | **0.345%** | **REPLAY MAJOR OWNER** |
| macOS | 50.038 / 3.158 ms | 46.880 ms | 45.385 ms | 96.81% | **16.93%** | **INCONCLUSIVE** |
| Windows | 53.421 / 3.994 ms | 49.428 ms | 48.498 ms | **98.12%** | **0.118%** | **REPLAY MAJOR OWNER** |

**Do not count macOS as confirmed:** its measured 16.93% wrapped-versus-unwrapped penalty discrepancy violates the **predeclared 15% gate**, though the recorded replay span and independent cProfile both qualitatively point to replay. The preceding exact-source run #40998138423 independently found the same split: Ubuntu 98.24% share with 0.015% perturbation; Windows 97.91% share with 0.807% perturbation; macOS 92.55% share but 25.7% perturbation and therefore INCONCLUSIVE. Preserve all contradictory observations and do not pool cross-host timings.

On the final head, cProfile independently reports 63 calls to `journal_replay._apply_journal_ops` during chain open vs zero for checkpoint open. Its profiles identify repeated list/dict construction and per-generation sorting as high cumulative-cost locations. **cProfile itself perturbs runtime**; its milliseconds are diagnosis, never treated as ordinary Reader wall/CPU measurements.

The apparent doubling of Ubuntu absolute chain timing in the first J24G61 run relative to earlier #800 is an additional warning about runner/process environment; the *within-run paired* comparisons, source pins and independent controls are the only basis of this result. Even when span attribution is high, the experiment measures current cost owner, not actual savings from a newly implemented algorithm.

## Independent artifact and hostile audit

[Final three-host run #40998543593](https://github.com/FCMO-AI/.CMPCT/actions/runs/40998543593) produced original GitHub ZIP artifacts:
- Ubuntu artifact **12952497365**; ZIP SHA-256 `e2221dcb628962aa06738c1ba6b1c6150fa8d494a524ec3726da31fb7018682c`; raw JSON SHA-256 `1d1f42f4b9fdaf8a7a24126c7f71a9d27d8e3c1952c1a67e7b896bb331fd7ce7`.
- macOS artifact **12951988348**; ZIP SHA-256 `5cab5aca4be06e78d39cd4a376ff7b6a9f8bb009f146dadb3744898db3f9da02`; raw JSON SHA-256 `04e385e1e589fff1cb17d26eaaa6661e0a4558df4b9e49db69fd576c4d83032f`.
- Windows artifact **12951499641**; ZIP SHA-256 `52078d58c4e4df46ac220eec93e2796c85f6c61e4d775f2635cfa03d899676c3`; raw JSON SHA-256 `b20f2348777d5f00b7feb40a4a47de792abf987973695942f634c86439a73814`.

All three original provider ZIPs were **downloaded separately**, SHA-verified against GitHub digests, unpacked and audited again offline with a separately written Python standard-library receipt auditor; every raw duration, source blob, ABBA sequence, ordinal/depth identity, call count, phase span sum, median, checkpoint-byte premium, attribution and disposition was independently recomputed. The committed `research/j24g61_independent_receipt_audit.py` also executed **inside each host's workflow** and refused **8/8 hostile record mutations per host (24/24)**. This validates raw receipts, not a second independently implemented CMPCT Reader nor separate decoding of every physical archive byte.

### Preserved negative: first hosted execution

[Original run #40997710352](https://github.com/FCMO-AI/.CMPCT/actions/runs/40997710352) failed on all three hosts due to an **instrument evidence ownership bug**: merging `**obs` after the experiment's depth key overwrote checkpoint case depth with the Reader's real depth zero. Thus the expected eight checkpoint samples appeared missing during summarization. Commit `4cd27462` separated case depth from `observed_depth`, retaining the actual Reader observation and original adversarial check; no benchmark threshold, comparator or product code was weakened. Subsequent source-exact runs passed.

The first PR Engineering Evidence run initially rejected missing literal dossier headings; metadata-only PR correction passed on the next exact-head CI. The validators were not changed.

## Decision, alternatives and debt

**Science advanced:** ordinary Writer's multi-*generation* Reader-open overhead on the exact #795 experimental product is overwhelmingly localized to the shared per-generation replay function on two hosts, not to footer payload decompression. macOS remains unconfirmed under its preregistered perturbation limit. This does not transfer the old J24G58 #797 33.266× **within-one-generation** helper speedup to public Writer, since its >=16-operations trigger does not occur for public single-op generations.

The strongest next unclaimed action is a **no-added-archive-bytes cross-generation semantic reuse oracle**: preserve complete per-generation opcode admission, path/fsmeta identity transfer, rename collisions, resource limits, recovery/footer rollback, 64th checkpoint semantics and compatibility with existing r24, while reducing repeated O(N) scans/sorts. Compare against the unchanged #795 source and a fully charged checkpoint alternative. Test mixed put/del/ren histories, true xattrs/UID ownership overrides and hardlink identity, hostile footer recovery, multi-platform installed packages, physical archive SHA, all relevant CPU/wall/RSS/temp-I/O and finally complete official size/create/extract and native interoperability gates. Retain the simpler baseline if exported memory/safety/maintenance cost dominates.

**No product evidence or promotion claimed:** neither the code nor format, native Rust, published release v0.30.0, historical frozen benchmark records, release gate, or `main` changed. Existing O69/O72 fingerprints and unrelated release/correctness/safety debts remain separate and open. This experiment did not run the final full ZIP/Zstd competitor comparison, end-to-end create/extract, power-loss recovery, all-member corruption, cold physical disk or general metadata-heavy filesystem matrix. No merge, release, version bump or Discovery `STATE.json` edit.

**Coordination:** #795 owns implementation, #797 the wide-delta helper, #800 the physical paired-parent court, #574 Discovery reconciliation. Owners #795 and #797 were notified with source-bound conclusions; no narrow implementation collision or shared-state overwrite. The prospective counterfactual lesson is to establish public operation geometry and measured path owner *before* productizing a synthetic speedup. No repeated evidence supports editing discovery policy.
