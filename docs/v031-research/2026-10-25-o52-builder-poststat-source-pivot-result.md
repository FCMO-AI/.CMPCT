# O52 — source-exact Builder post-stat pivot: installed three-host result (2026-10-25 UTC)

**Decision:** `POST_STAT_SOURCE_LIFETIME_GAP_CONFIRMED_POSIX`. Static supported-type recognition from O47×O48/O50 is necessary and is independently green, but is **not sufficient** to bind the bytes eventually archived to the inode admitted by `DirEntry.stat(follow_symlinks=False)`. Two different failure classes survived in the actual unmodified O50 Builder. No product fix or release credit is claimed.

## Immutable source / preregistration
- Parent product: O50 [PR #405](https://github.com/FCMO-AI/.CMPCT/pull/405), exact commit `17c96603e33b02b3f2f9e0079eec2b128f293be8`.
- Tested *installed* Builder Git blob: `21a9ec696df13961c25301654feb607a7e161a4c`; installed Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, unchanged on all hosts.
- Original [preregistration](2026-10-25-o52-builder-poststat-source-pivot-prereg.md) committed **before** tests/CI as `49b11e1ffb99c3d6343e643895f8eff05dbd28ce`.
- Research source+workflow: [PR #407](https://github.com/FCMO-AI/.CMPCT/pull/407), executed exact head `0562591fa8842c0d4f0214a6f7ca2a273a857968`. Product source diff against O50 parent: **zero**.
- Genuine hosted [Actions run #40160804316](https://github.com/FCMO-AI/.CMPCT/actions/runs/40160804316). The push created a three-OS workflow; this specific run executed actual pytest and persisted independent JUnit and log evidence.

## Falsifiable mechanism
O50 invokes `DirEntry.stat(follow_symlinks=False)` to classify a pathname as a regular file. For an ordinary `.bin` member it subsequently opens `e.path` by **pathname**, using Python `open(e.path, 'rb')`. The earlier type fact is not bound to the later open's descriptor. O48 correctly rejects an already-present FIFO and O47 correctly handles stable Windows hardlink identity; neither protects this interval.

A deterministic scheduler hook surrounds the **real** builtin Python open of the exact victim path, swaps an actual POSIX directory entry after the genuine lstat/type decision, and delegates unchanged to the original builtin. It changes filesystem state only; the Builder and Reader implementations, codec, parser, formats, comparison thresholds and source identity remain untouched. The hook makes a possible interleaving reproducible, but **does not measure probability of spontaneous exploitation**.

## Direct measurements / source-bound receipts

| Hosted runner | Job ID | Tests | Result / artifact |
| --- | --- | --- | --- |
| Ubuntu 24.04 | `121071758670` | **4 PASS / 0 SKIP** | [raw artifact #12586227582](https://github.com/FCMO-AI/.CMPCT/actions/runs/40160804316/artifacts/12586227582) |
| macOS 14 | `121071758826` | **4 PASS / 0 SKIP** | [raw artifact #12586476397](https://github.com/FCMO-AI/.CMPCT/actions/runs/40160804316/artifacts/12586476397) |
| Windows 2025 | `121071758774` | **1 PASS / 3 POSIX SKIP** | [raw artifact #12586552380](https://github.com/FCMO-AI/.CMPCT/actions/runs/40160804316/artifacts/12586552380) |

**Total: 9 actual test passes / 3 explicitly classified skips, zero errors/failures**. Workflow insists on four actual testcase names, exact installed Builder Git blob, full installed Reader identity, exact source commit, and real JUnit counts. Successful original O50 functionality on Windows is not extended to a Windows pivot claim.

**Positive controls:** on stable input, the real Builder makes a SHA-verifiable r24 archive, reads original bytes exactly, and classifies an already-present symlink as `K_SYMLINK`; an already-present POSIX FIFO raises a supported-type error before output and preserves an existing output sentinel.

**Adversary A — after-lstat regular→external symlink:** Ubuntu and macOS both executed an actual substitution of `source/victim.bin` with a real symlink to `outside-secret.bin` *outside* the source tree immediately before the original regular-file `open`. The genuine Builder generated a valid SHA-verifiable r24 archive; `victim.bin` remained encoded as **`K_FILE`** and `CMPCT.read('victim.bin')` returned the **external bytes** rather than the original bytes. This is an integrity/completeness/privacy boundary of local mutable source capture, not a cryptographic SHA collision.

**Adversary B — after-lstat regular→FIFO:** the same real pathname was switched to a real no-writer FIFO exactly before the original regular-file `open`. A killable independent Python subprocess ran the genuine Builder. It did not terminate by the prospective **3.0-second watchdog limit**, was killed, and no archive output was produced. This is a bounded demonstration of availability failure in that controlled scenario, not a benchmark of normal creation latency.

Raw source-bound hosted artifacts have GitHub recorded ZIP checksums:
- Ubuntu `02cb53b8eef96e827f0cad926a17816f7f11fb23c45706e47bffbcb47218e0f0`
- macOS `debc8e73be5e96525360a865736deea392f2fd45ca79cc881058c3b561d3b42f`
- Windows `ae82b6454b5b11b5a1e71ae714efb4123e2afeb564753738b2f5f71de3ad7b7e`

These are artifact ZIP hashes emitted by GitHub Actions, not new source/feature release identifiers.

## Negative/scope boundaries
- O50 static-source gains **remain true**. This finding tests a *new*, post-admission source lifetime boundary; do not reclassify prior PASS as false.
- POSIX Linux/macOS only for both adversaries. No assertion about Windows, NFS/network shares, an uncontended stable tree, remote attackability or adversarial directory-ancestor replacement.
- No claim of immutable-source snapshot semantics, inode continuity on all paths, or prevention of concurrent in-place same-inode mutation. `O_NOFOLLOW` on the final file component alone cannot prevent all ancestor substitution or content rewrite.
- The immediate failed-to-return case is a deterministic **3-second lower bound on blocking** under an unwritten FIFO, not an unbounded-time measurement.
- No memory/CPU/whole-product size/regression economic measurement; no product code changed, no release. Previous full-tests red cannot be turned green from this research pass.

## Concurrency and product decision
O47/#401, O48/#402 and their owner-composition O50/#405 retain exact product ownership. O51/#406 owns the separate Writer source-fd admission. O52 remains an independently declared research/falsifier only. Future Builder implementation should coordinate with O50 before writing product code.

**Cheapest next decisive product test:** a disposable candidate that binds a POSIX regular-file descriptor to its admitted type using `os.open` with `O_NONBLOCK` and `O_NOFOLLOW` where supported, then `fstat` on the **same opened handle**, and reads from that handle rather than reopening the path. Verify both O52 adversaries are rejected promptly while stable ordinary source and preexisting symlink semantics remain unchanged, and then test directory ancestors, deferred ZIP, sparse files, CDC, hardlink ownership, xattrs and Windows as separate obligations. Merely adding a second pathname stat before the open does not close the scheduling gap. Linux `openat2 RESOLVE_BENEATH` and descriptor-relative path traversal may be required for a stronger untrusted-tree containment contract; they are not implemented or proven here.

The next action for a zero-history operator is **not** to remeasure these two already-decisive POSIX adversaries, but to reconcile O50 ownership, choose a source-custody threat contract, construct the smallest descriptor-bound falsifier, and then measure complete Builder create cost plus exact filesystem semantics before considering promotion.

## Adjacent independent CI finding, not part of O52 scientific decision
O50 [generic General Tests run #40158561054](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561054) failed **7/790**: four longstanding v0.30 fingerprint/public-surface assertion reds also reproduced by unrelated Writer O51's [run #40160029064](https://github.com/FCMO-AI/.CMPCT/actions/runs/40160029064) (**4 failed / 791 passed**), plus three O50 parent-parity tests that attempted `git show 29d9688...:src/cmpct/builder.py` from a shallow CI checkout (exit 128). O50's dedicated full-fetch source court [40158561118](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561118) passed. Do not relabel generic Tests green or weaken the source-exact test; supply parent source custody on that runner or via a bundled exact hash-verified fixture, then rerun both.
