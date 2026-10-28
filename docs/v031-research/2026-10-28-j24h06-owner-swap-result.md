# J24H06 — First-party hardlink owner-swap result (source-pinned)

**Date:** 2026-10-28 UTC. **Decision:** `SILENT_SIGNED_OWNER_MISMATCH` on **two actual POSIX hosts** for a *hostile mutable extraction directory*. **Scientific negative, not corrected product**; do **not** merge, release, alter r24 or claim general exploitability.

## Prospective custody and source

- Prediction [preregistered before instrumentation](2026-10-28-j24h06-owner-swap-prereg.md) in Git commit `dd890124dea2654be9eb9d6c75e234837a56f9e6`.
- Product source parent is [PR #629](https://github.com/FCMO-AI/.CMPCT/pull/629) exact `22fb832777211a5aa19ccb1c9df54fa4714ff22f`; real Reader blob `931545520b5a649903a8bdac4e9a1806bc38d58d`; Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`.
- Real scientific script `research/j24h06_owner_swap_court.py`, blob `e9cfd1ade4bf4c72715846ea835b4d4e38bd73c2`; workflow created on HEAD `31044e698dd7057b2791771655f21d58366bd3db` (prior to later documentation/CI-topology edits).
- [Hosted Actions #40614754496](https://github.com/FCMO-AI/.CMPCT/actions/runs/40614754496), two separately installed genuine CMPCT wheel jobs, both **SUCCESS** with detached independent receipt referee: Ubuntu job `122574517002`, raw artifact [#12783938029](https://github.com/FCMO-AI/.CMPCT/actions/runs/40614754496/artifacts/12783938029), artifact ZIP SHA256 `a97fd6798f8dee0de4220b025cae985485d06dc4fcb6354a3a4475c70a3ba959`; macOS job `122574517550` and its separate artifact in the same Actions run. The word **SUCCESS** describes the *scientific falsifier*, NOT extraction safety.

## Actual product path

The genuine Builder created physically hardlinked `b-owner` and `z-alias`, then authentic Writer `append_rename` generated a revision-24 journal containing forward `a-alias → b-owner`. `preflight_archive`, full `CMPCT.verify`, `read` and `read_range` accepted exact bytes. Normal `extractall(metadata=True)` to an untouched fresh directory was **correct**, both paths regular files sharing a genuine inode, independent of a distinct external sentinel.

For the second extraction, a deterministic single callback triggered at the **genuine `os.link` OS invocation**, after the Reader's actual `os.path.isfile(target)` and `not os.path.islink(target)` checks. It moved the already-extracted authentic owner to a quarantine name and placed a symlink to an unrelated external sentinel at the original owner pathname. It then delegated to original host `os.link` **without forging a successful OS result**, and restored the test instrument afterwards. Both hosts returned from `extractall(metadata=True)` **without an exception**, without a final hash/topology check.

## Observations / independent host comparison

| Evidence | Ubuntu 24.04 | macOS 14 |
| --- | --- | --- |
| Full installed-product court | SUCCESS | SUCCESS |
| Control normal extraction | exact SHA and shared regular-file inode | exact SHA and shared regular-file inode |
| Signed logical payload | 5,080 bytes, SHA `a69bfe17aa9fa686e152e3fb6b344cb2236b5b434972b3fe5edd50eefdd1c23e` | same |
| External sentinel | 5,289 bytes, SHA `03c6d4219afe44a7be4fd9b69d98502ceda7d06805915fe941ec6216fd569b4c` | same |
| Signed archive size | 1,097 B | 1,097 B |
| Signed archive SHA | `ce3075e2817c85f8d8cf919c7f0f53c5973dc0bd271b7961badb69fbb071adc3` | `187657edd8f32478afdb0ef36b8dc7a712a589ed2a79e98c7dd0586491452385` |
| `extractall` after owner swap | returns without exception | returns without exception |
| Extracted `a-alias` physical type | **symlink** to external sentinel | **regular hardlink** to external sentinel inode |
| Extracted `a-alias` content | external, not signed | external, not signed |
| Original authentic owner | safely present at displaced name, different inode | safely present at displaced name, different inode |
| External sentinel SHA | unchanged | unchanged |
| Scientific classification | **SILENT_SIGNED_OWNER_MISMATCH** | **SILENT_SIGNED_OWNER_MISMATCH** |

**Causal conclusion:** `isfile/islink` pathname prechecks followed by `os.link(source_path, dest_path)` do not preserve physical owner identity under this particular late destination mutation. The unchanged authenticated archive and successful normal control rule out codec, source, hardlink-recognition and Writer defects in this test. Host-specific symlink dereference behavior changes *how* the inconsistency manifests; not the shared violated invariant.

## Strongest negatives / scope boundary

- The test assumes a hostile actor can mutate the caller-selected extraction directory at the precisely controlled boundary. This is **NOT** an observed spontaneous failure rate, remote vulnerability, privilege escalation, real attacker process race probability, Windows/Android validation or general POSIX guarantee.
- It is a **controlled single-interposition scientific experiment**, not a separate-process concurrent workload. The real host `os.link` executes; instrumentation only fixes the scheduling point. Actual concurrently racing process and directory-fd protection remain open.
- No product code was changed. The earlier healthy three-host default Win32 metadata court on [#629](https://github.com/FCMO-AI/.CMPCT/pull/629) remains **valid for its uncontested fresh destination**. It cannot earn a hostile-destination extraction safety claim.
- An additional `lstat` immediately after the link can detect this *particular* deterministic schedule but creates another check/use boundary and is not a concurrency-robust fix. Merely toggling `follow_symlinks`, or checking the path a second time, does not establish original owner-inode custody on all platforms.
- Distinct prior threats: [#265](https://github.com/FCMO-AI/.CMPCT/issues/265) preexisting/ancestor destination symlinks, [#528](https://github.com/FCMO-AI/.CMPCT/issues/528) post-SHA chunk temporary-file inode substitution, [#619](https://github.com/FCMO-AI/.CMPCT/issues/619) forward-hardlink ordering, [#626](https://github.com/FCMO-AI/.CMPCT/issues/626) Windows timestamp restoration. Reuse architectural ownership, not one-off check gardening.

## Decision / cheapest decisive unclaimed action

Under a threat contract that includes concurrent mutation of an output directory, treat current #629 as **unsafe to promote without stronger owner identity + directory capability guarantees**. Preserve its proven normal three-host hardlink/mtime behavior. Product remedy should be owned/coordinated with Reader #569 and existing extraction safety owners: hold the **verified physical owner** through alias publication, use directory-relative no-follow primitives or equivalent supported native platform primitives, prevent ancestor pivots and protect final destination/rollback. Explicitly state supported trust model when a platform cannot provide that guarantee, rather than weakening the claim.

Next smallest full-product experiment: compose a genuinely fd-owned and source-identity-pinned hardlink creation on POSIX with authentic Builder→Writer→Reader and repeat this unchanged J24H06 hostile scheduling court plus #265/#528 controls, then measure extra syscalls, full extract CPU/wall/RSS, Windows fallback and recovery. Linux-only descriptor/linkat mechanism microtests can inform feasibility but cannot earn release credit without actual product integration.

**Discovery Engine:** changed the scientific decision that #629's normal fresh-directory success sufficed for hostile-destination safety. No concurrency collision (separate stacked research PR #632, other owners untouched), no warrant for discovery-policy rewrite or state-cache mutation. Prospective lesson: inspect the transition from verified inode to late pathname publication; a post-check mutation falsifier often provides a cheaper decisive discriminator than another happy-path test.

**CI truth at first run:** specialized hosted 2/2 SUCCESS with RED product-safety verdict. Engineering Evidence initially RED for missing PR description sections; CI Topology initially RED because fast workflow used `cancel-in-progress: false`. Both are evidence/workflow-policy infrastructure obligations; their correction does not modify the original scientific result. Full General Tests, official benchmark parity, Windows race scope and release promotion are not established.
