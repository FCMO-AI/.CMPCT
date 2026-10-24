# O14 hosted result — reproducible archive mode equivalence

Date: 2026-10-24  
Status: **SCOPED SCIENTIFIC POSITIVE; NOT A PRODUCT OR RELEASE FIX**

## Frozen prediction and authoritative source
Preregistration was committed first, at `83c30f92b4769de6ec9e365c4ef002c49adc7c12`, before the oracle and workflow. The authentic CMPCT r24 product source is exactly PR #352 HEAD `93e9a00fd352ac567e9b069654aa145148370d42`; no `src/`, Writer, Builder or Reader files were changed in O14.

The original independent baseline was Issue #353 / installed native package workflow [40095303436](https://github.com/FCMO-AI/.CMPCT/actions/runs/40095303436): same source member bytes and correct extracts, but Linux/macOS archive SHA `6824f2b5...` and Windows `3722374c...`.

Question preregistered: does replacing **only** `stat.S_IMODE`-derived serialized row modes after real Builder scan make complete authentic archives byte-identical across the three OS, without modifying any physical record or any other index field? The fixed research mode profile is directory `0755`, regular file `0644`, not a claimed product policy.

## Hosted experiment and source evidence
- Workflow: [40119076117](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117), all **four** jobs SUCCESS (Ubuntu-24.04, macOS-14, Windows-2025, independent referee).
- Exact experiment HEAD: `a7c8d2738ad7ff22a5a16c420604357215a7bd79`.
- Raw platform artifacts: [Ubuntu 12569514199](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117/artifacts/12569514199), [macOS 12570229230](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117/artifacts/12570229230), [Windows 12569498353](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117/artifacts/12569498353); [independent referee 12570004226](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119076117/artifacts/12570004226).
- Three-host referee decision: `H1_SUPPORTED_IN_TESTED_THREE_HOST_CORPUS`.
- Each platform built **twice per variant** (original Builder and scan-only fixed mode). Repeat archive/index SHA and structured result equality PASS on each host. Installed Builder and actual Reader `verify()`, `read()`, `extractall()` checked complete member bytes.

### Actual source modes

| Member | Ubuntu / macOS original | Windows original | Research-only fixed |
|---|---:|---:|---:|
| `nested` directory | `0755` (493) | `0777` (511) | `0755` |
| `nested/data.bin` | `0644` (420) | `0666` (438) | `0644` |
| `readme.txt` | `0644` (420) | `0666` (438) | `0644` |

### Complete archive SHA-256

| Host | Original genuine Builder | Fixed-mode research oracle |
|---|---|---|
| Ubuntu 24.04 | `6824f2b543e188448a37974e79d94f1290afad2b4e87b42a7d8d9ad3b7afc2d5` | `6824f2b543e188448a37974e79d94f1290afad2b4e87b42a7d8d9ad3b7afc2d5` |
| macOS 14 | `6824f2b543e188448a37974e79d94f1290afad2b4e87b42a7d8d9ad3b7afc2d5` | `6824f2b543e188448a37974e79d94f1290afad2b4e87b42a7d8d9ad3b7afc2d5` |
| Windows 2025 | `3722374c51b82887b9ead48543559d2206050225cd5dedba66dff35696e32de0` | **`6824f2b543e188448a37974e79d94f1290afad2b4e87b42a7d8d9ad3b7afc2d5`** |

The baseline *exactly reproduced* Issue #353's historical hashes. The mode-only oracle converged the **complete archive**, not a digest where differing bytes were omitted. The referee independently confirmed `baseline_diverges=true`, `modes_differ=true`, `mode_only_archive_equal=true`, `mode_only_physical_equal=true`, `non_mode_index_equal=true`, `source_logical_members_equal=true`. Within each host, the original and oracle have **identical complete physical payload SHA** and **identical full MessagePack index SHA after replacing mode fields with a common zero for the purpose of diagnosis**. Thus the mode-only changed the authenticated metadata field it was intended to change and did not silently change the codec or other index semantics.

## Scientific decision
**H1 supported and original Issue #353 discrepancy causally localized to source file mode metadata for the two-file, one-directory installed smoke corpus.** That is a decision-changing scientific result. The original product makes the same archived *payload* but serializes OS-specific modes. The original archive remains valid and losslessly reconstructed on all three hosts. No archive corruption, native codec defect or hidden compression benefit was demonstrated.

## Strongest negative / self-critique
The successful normalized SHA is achieved only by **changing directory and file mode semantics**. A naive global `0644` file rule would erase POSIX execute bits and potentially read-only policies or intended ACL interpretation on richer trees. Research-mode equivalence cannot be substituted for a permission-fidelity claim. Windows `0666` and `0777` are observed `stat.S_IMODE` values and do not prove identical underlying ACL semantics to Unix `0644`/`0755`. This one synthetic fixture does not prove reproducibility of hardlinks, symlinks, xattrs, ACLs, sparse trees, nested archives, varying codec versions or host-native filesystem creation policy. We tested default `workers=1` and one fixed epoch, not every possible host/runtime combination.

No new product representation, format revision, released version, conditional win, or full product cost claim is authorized. Builder and installed smoke remain untouched; difference in full archive SHA with unequal filesystem metadata **was not evidence of a product defect under a contract requiring preservation of mode information**.

## Counterfactual / transferable lesson
A **three-row source-vs-index metadata table**, obtained at the moment the first hashes diverged, would have discriminated the family without codec engineering or broad forensic search. Prospectively recognizable because the builder's reproducible policy clearly normalizes times, owner and xattrs but retains modes. The cheapest decisive next action was a genuine same-source physical/index A/B across the three hosts, rather than trying to make unequal tree semantics identical by a digest transform. This lesson is useful but no change to Discovery Engine policy is earned by one episode.

## Next product decision (not implementation)
Make the `--reproducible` product contract explicit: reproducible archive for **identical source metadata**, or an **opt-in documented portable-build metadata profile** accepting loss of certain physical permission information. Before proposing the latter, falsify its usefulness with held-out executable files, read-only files, directories, hardlinks/symlinks, raw POSIX names and cross-platform extraction; quantify mode/ACL fidelity, complete archive bytes, verified/read/extract behavior, hash identity and user-visible permission consequences. Do not weaken the existing fidelity-preserving default or benchmark release comparator. The cheapest first held-out falsifier is an executable regular file on Linux: a naive `0644` mode rule provably loses its executable bit.

## CI and continuity
Original scientific O14 exact-head workflow **SUCCESS** at measurement HEAD `a7c8d2738ad7ff22a5a16c420604357215a7bd79`. An unrelated `ci-topology` check reported missing declaration `# ci-lane: deep`, requiring an administrative fix in the workflow; an initial Engineering Evidence failure was caused by nonliteral PR headings and subsequently fixed in the PR body, with [rerun 40119180273](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119180273) SUCCESS. The CI label issue is not a scientific failure; it must be fixed without weakening existing checks. A later docs-only/CI-only HEAD must obtain independent exact-head checks; do not silently transfer status from the observed experiment. Official release gates remain separate.

Decision/handoff: mark Issue #353's **specific tested archived-hash cause established**, do not close the broader reproducibility contract question. PR #352 owner untouched. O14 branch/PR stays DRAFT and independent; no release/merge.
