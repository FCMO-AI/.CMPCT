# O103 — real installed Reader mapped-source lifetime: POSIX SIGBUS result (2026-10-25)

**Decision: SAME_INODE_TRUNCATION_FATAL_SIGNAL_CONFIRMED on Linux and macOS for the tested immutable-r24 Reader code, with valid stable/different-inode controls. Negative product evidence, not a fix or remote-exploit claim.**

## Source identity and prospectively frozen question

- Canonical prospective development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Released v0.30.0, physical format r24 unchanged.
- Original source Git blobs: `src/cmpct/reader.py@e716233403dabd0966863c45635e18fa5ac6afb8`; `src/cmpct/builder.py@663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Prospectively registered science at `ed5389a1c1f969cbd93ec7abfe30aaba759d177e`, before experiment implementation.
- Original installed Builder and Reader, same 262,144-B random member, genuine r24 physical BLOB, source SHA-256 `1e0aeef712511bfe9b480565bba3716c4953986fabe59d75c931cf24a63f88d3`; baseline Reader `read()` and `verify()` succeeded. All destructive operations occurred in child processes under temporary directories.

## First experiment: meaningful instrument red, not product evidence

Original hosted run [40222624382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222624382), original HEAD `ec56a89fa3da8623f5a4252c322bab7c782ab1d7`, produced **two red jobs** (Ubuntu/macOS). Both authentic positive controls (stable content and replacement of the path by another inode) passed. The truncation arm threw `OSError: [Errno 22] Invalid argument` because the test mistakenly used `os.ftruncate(reader.f.fileno(), 0)` on the original Reader's intentionally read-only descriptor.

Preserved first raw artifacts: Ubuntu `12609767467` ZIP SHA-256 `dc2d4be7a39ec646aed99a8cb277139ad79bf8f982d9de215e3246a6080b249d`, macOS `12609687625` ZIP SHA-256 `6d9e0586fd0e95218b868d4c0eca9796a40aaa15bbc3959dcac9be6ba91c7b66`. **First conclusion was NOT_CONFIRMED, due to experimental actuator permission, not because the Reader proved resistant.** The preregistered external-mutation claim was not altered or retroactively reworded.

The only scientific instrument correction, commit `99f2f969f99fd73b5f603e9435062f264264bbb1`, opens a **separate writable** handle to the same input path, verifies matching `(st_dev, st_ino)` against the actual Reader descriptor before truncation, runs `os.ftruncate(writer.fileno(),0)`, and verifies the original Reader's mapped inode is the same now-zero-length object. This precisely realizes the original concurrent external-actor hypothesis rather than mutating the Reader implementation.

## Corrected source-exact hosted product court

[Run 40222894752](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222894752), exact scientific source HEAD `99f2f969f99fd73b5f603e9435062f264264bbb1`: **SUCCESS 2/2 jobs**.

| Authentic scenario | Ubuntu 24.04 | macOS 14 |
| --- | --- | --- |
| Stable Reader read + strong verify | VALID / 262,144 B / SHA match | VALID / 262,144 B / SHA match |
| Replace pathname with different inode after mmap | VALID: reader returns/verifies old original bytes | VALID: reader returns/verifies old original bytes |
| Truncate the **same mapped inode** to zero then read | **fatal SIGBUS (child return code -7)** | **fatal SIGBUS (child return code -10)** |
| Timeout | None | None |

Evidence is direct and independently machine-read from both ZIP artifacts:

- Ubuntu run artifact [12610042441](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222894752/artifacts/12610042441), ZIP SHA-256 `06c854fdb64e61ed4d548dfaaed63c1fca2d7c358dfb34ef79acd52300691577`; source-exact receipt decision `READER_MMAP_SAME_INODE_SIGBUS_CONFIRMED`.
- macOS artifact [12609394645](https://github.com/FCMO-AI/.CMPCT/actions/runs/40222894752/artifacts/12609394645), ZIP SHA-256 `aac0b634214e7cc9507c4ca1f61348a697b417c0ace3831e63c9c5975c99107f`; receipt decision `READER_MMAP_SAME_INODE_SIGBUS_CONFIRMED`.
- Both logs confirm the original source Git blob and package installation before the test. For both paths the recorded `OPENED` physical inode was stable, the next event `SAME_INODE_TRUNCATED` declared size 0, then the process terminated with POSIX SIGBUS rather than printing a successful read or managed IOError.

**Importantly:** the test naming `scientific success` means it confirmed a product negative; it says nothing about repaired resilience.

## Interpretation, competing explanations and limits

Direct causal contrast supports **inode-content lifetime**, not path naming, as the trigger: the same installed Reader survived atomic replacement by an entirely distinct physical file and continued to verify its original mapping, but died when a separately opened writable descriptor truncated its own mapped inode. The Builder is not being tested for concurrent source scanning here. This is not evidence that malformed immutable archive bytes cause SIGBUS, nor any specific remotely exploitable path.

A simple `fstat` before read cannot eliminate the race if writers are allowed concurrently. A process-local try/except cannot catch SIGBUS. Potential repair classes must preserve original Reader performance/semantics: enforce immutable-source lifetime and safe external update semantics; snapshot/copy the entire archive with fully charged I/O/RSS; or replace/guard mmap with bounded descriptor reads (which still needs consistency/race semantics). Linux/macOS ABI differences and Windows open/sharing semantics must be tested independently. Neither an OS capability hack nor exception suppression is accepted as a fix by this result.

No benchmark, archive-byte, read throughput, RSS, full native parity, hostile static parser, Windows, filesystem network, or actual power-loss claim is earned. Official same-corpus full-product performance has not been measured on this research branch. No release promotion.

## Counterfactual / transferable method

The first experiment's failure was prospectively diagnosable from `open(path, 'rb')` in Reader source before dispatch. The cheapest better discriminator is to verify actuator permission and `(device,inode)` equality in the child before invoking expensive installed-product CI. This is a **local experiment-design lesson**; there is no durable repeated causal process evidence to justify changing the Discovery Engine policy or `STATE.json`.

## Next action

Open/coordinate a focused Reader source-lifetime issue (existing Deflate-export mmap mutation PR #286 is adjacent but not the same `CMPCT.read()` semantics). Require an explicit immutable archive-source contract; the smallest candidate fix needs a matching same-inode adversarial test and a control that atomic pathname replacement remains valid, plus I/O/RSS and cross-platform measurement before promotion. Do not place this responsibility on unrelated Builder output publication PRs. Continue complementary measured representation work while reader owner considers this boundary.

**Scientific status: RESULT CONFIRMED, NO PRODUCT FIX, NO MERGE, NO RELEASE.**
