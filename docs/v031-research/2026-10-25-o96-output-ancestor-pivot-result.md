# O96 result — output leaf custody does not bind a mutable ancestor namespace

**Date:** 2026-10-25 UTC. **Decision:** `O96_ANCESTOR_NAMESPACE_REBIND_CONFIRMED_POSIX` for the exact O93 product described below. **Status:** scientific counterexample, NOT product fix, merge or release.

## Prospective hypothesis and source custody

- Original immutable scientific prereg: `cf94adc0760df6af52aab2b22ea0ad4ec0c004b0`, before the O96 test or CI instrument existed.
- Historical O93 Builder product head: `15aac3f81c23e0a54ae66de3f6b2146642afa350`, PR #451, `src/cmpct/builder.py` Git blob `7214a46b781bb10051e6782ba7731989ebf05edb`. The installed source blob was independently recomputed from Python module bytes on both hosts; neither product nor format was modified in O96.
- Result-bearing science head: `f09d0d559bae89a931c130b6168f46bd935ae316`. Genuine [GitHub Actions run #40215874503](https://github.com/FCMO-AI/.CMPCT/actions/runs/40215874503); jobs Ubuntu `121236758672`, macOS `121236758918`.
- Raw receipt artifacts (unexpired at report time): Ubuntu [#12607476620](https://github.com/FCMO-AI/.CMPCT/actions/runs/40215874503/artifacts/12607476620), macOS [#12607925608](https://github.com/FCMO-AI/.CMPCT/actions/runs/40215874503/artifacts/12607925608).
- Scope Ubuntu 24.04 and macOS 14 only. The installed Builder runs outside the source checkout; the original `scan` executes in full. A deterministic test-only barrier after `scan` allows a separately scheduled actor to atomically swap an ancestor symlink. The Builder's original publication code continues unmodified. No Windows behavior is inferred.

## Direct observations

| Test | Ubuntu | macOS | Scientific meaning |
| --- | --- | --- | --- |
| Direct existing source-root output | PASS | PASS | Static preflight correctly refuses inside-root destination. |
| Initially absent output through stable symlink to independent external directory | PASS | PASS | Genuine archive created externally, verified and read; source unchanged. |
| Initially absent output; post-scan **ancestor symlink** replaced atomically to point into source root | **CONFIRMED** | **CONFIRMED** | Builder returns success, creates `source/archive.cmpct`, Reader verifies/read original leaf, source leaf bytes intact; source root now has a new artifact not inventoried. |

**JUnit:** 3 PASS / 0 FAIL / 0 ERROR / 0 SKIP on each host; the independent raw JUnit/marker auditor succeeded. **Interpretation:** those scientific PASSes prove an *undesired product behavior* reproduces, not that O93 is globally safe.

### Mechanism

1. `Builder.build(out)` resolves `realpath(out)` while `active-parent` points to an external directory. Its static source-containment predicate is false; `os.stat(out)` reports `ENOENT`. Thus `expected_stat=None`.
2. Genuine `Builder.scan()` reads the single original source file.
3. A controlled actor performs `os.replace(pending_parent_symlink, active_parent_symlink)`. The output **leaf** is still absent, but `active-parent` now resolves directly to the original source root.
4. O93 `_publish_bound_output` executes `os.open(out, O_WRONLY|O_NONBLOCK|O_CREAT|O_EXCL)`. `O_EXCL` protects the leaf from being replaced, **not any traversed ancestor**. The open creates a fresh regular archive *inside the source*; `fstat` and subsequent `stat(out)` agree because both see this same newly created leaf.
5. The Builder reports success; `result['logical_files']==1` from its original scan, while two regular entries now exist inside the source directory (`leaf.bin` and `archive.cmpct`). The original leaf bytes are unchanged and the created archive passes Reader `verify()` and exact leaf `read()`. The independently admitted external directory remains empty.

The result establishes a narrower guarantee: O93 addresses source-clobber/FIFO pivots of the **final pathname component** (O91), while output-parent namespace custody is not bound over the scan→publish interval. This is an explicitly acknowledged limit in the original O93 prereg, now experimentally confirmed as a real Builder side effect rather than inferred only from POSIX primitives.

## Lower-rung independent controls — no product credit

An independent Linux POSIX primitive experiment used the same existing-parent-symlink/absent-leaf pivot. `os.open(full_path, O_CREAT|O_EXCL)` and `os.open(full_path, O_CREAT|O_EXCL|O_NOFOLLOW)` both created the new leaf inside the redirected source root. `os.open(leaf, O_CREAT|O_EXCL, dir_fd=previously_opened_external_parent_fd)` created only inside the *original* external directory; in that arm the newly redirected user pathname no longer resolved to the created object. This is a useful **control** proving a descriptor-pinned parent can prevent this particular unauthorized write, but also exposing remaining namespace/publication semantics: pinning a directory descriptor alone does not guarantee the final user-visible path resolves to the created archive. No O96 product implementation was written.

## Strongest negatives and unmeasured boundaries

- No original source **payload** corruption was observed; the changed state is insertion of an archive file into the original source directory. Do not reuse O91's actual source-byte-clobber claim here.
- The actor must be independently capable of modifying the output ancestor symlink. Ordinary stable-parent builds remain correct.
- Tests establish no broad TOCTOU immunity, Windows portability, crash/power durability, filesystem ACL semantics, or protection against ancestor changes after any final verification.
- No independent complete-size/create/read/extract/RSS benchmark is owed for this **unchanged science-only** candidate. O93 is not promoted by the negative or the green test workflow.
- O93's known existing-inode/failure-atomicity tension with O75/O78 remains unsolved. A blanket staged `os.replace` would not preserve all prior destination hardlink/inode/xattr semantics.

## Counterfactual and next decisive product design

The cheapest discriminator was an **absent destination** through a mutable ancestor symlink, tested after real scan and before original `os.open`; checking only the final component would misleadingly report security. The prospectively recognizable lesson is: **an authenticated output inode does not authenticate the containing path namespace, particularly when the inode did not exist at admission**.

Owner #451 should decide whether its contract explicitly excludes hostile mutable ancestor namespaces, or whether broader destination custody is a promotion requirement. For the stronger contract, evaluate descriptor-pinned parent resolution/creation *plus* coherent final pathname publication semantics and a bounded hostile ancestor replacement court, preserving O78's inode/alias semantics where claimed. Distinguish POSIX directory-fd controls from Windows handle/rename behavior. Do not silently replace this with a second static `realpath` check or claim `O_NOFOLLOW` guards ancestors. Stop this exact narrow O96 lane at the confirmed negative; other agents may progress the separately owned product architecture.

## Discovery-engine outcome

**Question changed decision:** yes — a directly observed ancestor rebind proves O93's leaf-descriptor fix cannot be described as global source/output namespace lifetime protection. **Concurrency:** independently preregistered adjacent mutation surface, no other agent's product branch/tests rewritten, no actual claim collision detected. **Counterfactual:** preflight checked actual basename but not ancestor custody; a cheap parent pivot could have distinguished this before expanding any publication claim. **Policy:** no evidence-backed general discovery-policy rewrite earned. The detailed evidence belongs to this PR and original Actions receipts, not duplicate `STATE.json` edits.
