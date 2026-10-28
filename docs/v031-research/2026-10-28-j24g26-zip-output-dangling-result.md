# J24G26 — signed r24 ZIP export output-symlink contract, narrow result

**Date:** 2026-10-28 UTC. **Classification:** bounded research / interoperability and publication-ownership evidence, **no product source mutation, merge, release or benchmark credit**.

## Immutable prereg, corrected prior-art disclosure
Original prior-to-test prereg: `9c8ecec2f48450b0a34fa8f80aeb68676e856a9e`, retained unchanged for temporal honesty. Published source: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (released v0.30.0, revision 24). Staging candidate #492: `ca01d885fedc8ffc343b9c3c624eddd134158452`, Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`. Result-bearing exact research HEAD `b7702f490fd43a953bb92652514b4c44512ac4f5` (no modified Reader source).

**Important concurrency/novelty correction:** after preregistration and the initial work, the owner discussion for #492 exposed the already-completed [O151 PR #493](https://github.com/FCMO-AI/.CMPCT/pull/493) / [six-job Actions #40271338947](https://github.com/FCMO-AI/.CMPCT/actions/runs/40271338947), dated 2026-10-26. O151 had **already** established that O140 follows an *existing output symlink to a regular file* and O149/O150 replace the symlink while preserving the referent. This part of J24G26 **is not new** and must not be counted as a discovery. The bounded new extension here is the **dangling output symlink** with a frozen direct Deflate control, plus source-alias rejection as inherited safety replication. Ordinary symlink behavior is only a stronger inherited control.

## Exact-head executed evidence
[GitHub Actions #40787247710](https://github.com/FCMO-AI/.CMPCT/actions/runs/40787247710): **Ubuntu 24.04 SUCCESS; macOS 14 SUCCESS** on exact HEAD `b7702f490fd43a953bb92652514b4c44512ac4f5`. Python 3.11 installed both product sources independently, each with its own package-owned compiled core; detached published source SHA and candidate Reader Git blob checked.

- Two **Builder-independent frozen revision-24** authentic archives: `raw.bin`, `deflate.txt` from `tests/conformance/v24-direct-codecs.json`, frozen fixture blob `d10b7dab9126d39e819a74279c186363a163f2ef`.
- Four output topologies × both actual exported Readers × two archives, plus one source-self-alias refusal per archive, totaling **18 original results per host / 36 hosted results**.
- **16 physical ordinary-success ZIPs per host**, checked by Python stdlib `zipfile`, with exact logical SHA and complete ZIP SHA identical across both Readers and both hosts for each member. `raw.bin` ZIP SHA `910e3be250460beac06083166a0641ed1398506ae40949e56efd3c3c73a564db`; `deflate.txt` ZIP SHA `586e20657068a45033a4dba84207fe7ec276ccbe4bf62cb8083d3d4ed7d8c3c2`.
- Published source refuses **no** ordinary symlink case; staged candidate refuses the output symlink **to its own source CMPCT inode**, preserving source and link on both hosts. Never executed the historical unsafe old Reader on this destructive source-alias scenario.

| Destination scenario | Published `main` output | Staged #492 output | Original unrelated referent |
| --- | --- | --- | --- |
| Relative symlink → existing regular ZIP | follows symlink; retains link | replaces symlink with new ZIP | old updates; candidate unchanged (**already O151**) |
| Absolute symlink → existing regular ZIP | follows symlink; retains link | replaces symlink with new ZIP | old updates; candidate unchanged (**O151 extension: absolute path**) |
| **Dangling symlink → missing file** | **retains symlink, creates referent** | **replaces symlink leaf, absent referent stays absent** | none; full ZIP bytes identical (**new narrow evidence**) |
| Ordinary existing regular ZIP | writes through same inode | replaces with a new inode | both succeed with identical ZIP |
| Symlink → source CMPCT inode | deliberately not run (destructive historical control) | rejects before publication | source bytes unchanged |

All entries are signed/geometry-valid fixture inputs. File/link semantics were witnessed inside fresh hosted temporary directories; raw output ZIP bytes and checksums were preserved in original GitHub artifacts.

## Original raw artifacts and independent external auditing
- Ubuntu artifact [12860620162](https://github.com/FCMO-AI/.CMPCT/actions/runs/40787247710/artifacts/12860620162), original ZIP SHA-256 `68a1933ad9c688fbe3020eb5c7634f32caeca947a90f56d6624bd6c0590e99a6`.
- macOS artifact [12860201418](https://github.com/FCMO-AI/.CMPCT/actions/runs/40787247710/artifacts/12860201418), original ZIP SHA-256 `50837f05acdfff6dfdf8440da8e0cf2646bb81abbb230ff883f9d68bab46ab50`.

Original downloaded artifacts were independently analyzed outside the CMPCT instrument with **Python stdlib only**: **903 assertion checks PASS** across both bundles, including original artifact SHA, 32 physical ZIPs, local-file headers, central directory CRC, exact logical SHA, source identity from original receipts and cross-host observed-state parity. **Limitation:** independent post-run bytes audit cannot itself observe transient symlink/inode state in the hosted runners, which is authenticated as source-bound runner JSON receipts; it independently verifies the 32 actual ZIP member files. The local auditor's initial assumptions about self-alias output SHA and cross-host timestamp-dependent old-ZIP referent hashes were wrong and corrected. Both failed audit attempts remain methodological negatives, not altered product evidence.

## Initial hosted infrastructure failure, preserved
Initial HEAD `e2e6bba9` [Actions #40787056772](https://github.com/FCMO-AI/.CMPCT/actions/runs/40787056772) failed on both hosts **before any behavior comparison**: the detached published source worktree was imported directly without the package-owned compiled `cmpct_core` library. Subsequent instrument/workflow commits installed the **original historical package in a separate target**, never lending it the candidate native core, and the terminal source-exact run passed. No evaluator assertions or source fixtures were weakened.

## Causal verdict / no false promotion
`OUTPUT_SYMLINK_ACCEPTANCE_PARITY_FALSIFIED` for a **dangling symlink** also, with the same independent source ZIP bytes. This is **a deliberate contract fork to adjudicate**, not a security exploit or proof that the staged fix is wrong: atomic pathname replacement is naturally different from following an output symlink and overwriting its referent. The existing [O151](https://github.com/FCMO-AI/.CMPCT/pull/493) is stronger evidence of the general fork. Decide one explicit supported output-link policy and document it; do not promote #492 under a blanket statement that published success-path file/link semantics are unchanged.

**No guarantee of** hostile concurrent directory mutation, stage write inode identity (#497 O157 negative), immutable-path publication, power loss, Windows symlink privileges, ownership/xattrs, ZIP64, complete CPU/RSS/temp-I/O, full official performance parity or release eligibility. #284's trailing-Deflate compatibility regression (J24G25 #710) and #707's proposed alternative still require an owner-led single integration. #512 owns separately tested fd-bound stage safety, not a full atomic compare-and-rename guarantee.

## PARETOBONK / counterfactual
Counterfactual cheap predictor: compare `open(out,'wb')` versus `os.replace(stage,out)` and resolve **prior O151 discussion** before preregistering, rather than starting with the current open-PR title list. The latter would have retired much of this lane; the only additional decision-relevant case would be dangling output links. This is a **local process mistake**, recoverable by reading earlier owner results, not evidence to modify normative Discovery Engine policy, frozen gates or benchmarks. The standalone micro proposed later for O(N²) transaction replay was likewise retired immediately when issue #649 revealed owners #344/#358; it is not a new research claim.

**Disposition:** bounded research complete, leave #492 and other implementation owners untouched. Recommend close research PR #713 after retaining evidence, rather than creating another permanent active implementation lane. `docs/discovery/STATE.json` unchanged (separate owner #574). Next high-value action: owner-led convergence of #284/#492/#512/#707 with source-exact compatibility, security and product resource gates; or switch to truly unclaimed representation frontiers, not another ZIP staging variant.
