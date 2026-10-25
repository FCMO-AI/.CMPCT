# O93 — descriptor-bound Builder publication (preregistration)

Date: 2026-10-25 UTC. Status: PREDICTION FROZEN BEFORE PRODUCT EDIT OR RESULT.

## Exact inherited authority / concurrent owners
- Released CMPCT v0.30.0, revision 24; prospective v0.31 branch.
- Product parent: O90 PR #448 exact HEAD `1beb733da61da8e1c562e7c3190b1f18f1cc45d1`, Builder blob `bfb37fcd06e6ff05742606ece365348150f477fc`.
- O91 PR #449 independently proved **real post-scan output-pivot** source clobber and FIFO blocking on that same exact Builder, Linux/macOS, Actions #40209092155. This campaign does not edit its instrument or branch.
- O75/#432 and O78/#435 own failure-atomic rename and its incompatible inode/xattr/hardlink semantics. Do not adopt rename, rebase, or rewrite those owner branches.
- Read current AGENTS, discovery/release laws and PR collision landscape. Isolation: new O93 branch and draft PR.

## Primary falsifiable question
Can binding an already-admitted output to an actual OS file descriptor **before** the destructive truncate, with nonblocking open and inode identity comparison, reject the genuine post-admission symlink-to-source and FIFO pivots WITHOUT changing normal in-place publication semantics or revision-24 archive bytes?

## Baseline / dominant failure
O90 stat preflight and `Path.write_bytes` are separated by arbitrarily long scan/compression. A hostile process can swap destination to a new regular/source alias or FIFO after stat; the final pathname open may corrupt a one-link source or block. Existing O90 admitted ordinary external regular destinations (including symlink to regular) should still succeed, preserving destination inode, hardlinks, POSIX mode and xattrs.

## Hypothesis / proposed mechanism
Retain the O90 preflight's identity (or explicit absence). At publication, open existing path O_WRONLY | O_NONBLOCK (plus O_BINARY if offered), **without O_TRUNC**; inspect `os.fstat(fd)` and require the originally admitted regular dev/ino before truncation. If the path was absent originally, use O_CREAT | O_EXCL instead of following a newly planted alias. Only after accepting the pinned regular fd, truncate/write/flush through that fd. No unbound pathname write. This is a *single-output lifetime binding*, not atomic snapshot/rename/durability.

## Strong simpler controls and alternatives
- Static check immediately before `write_bytes`: still admits an unbounded check/use race.
- `os.replace` staging: avoids torn overwrite but O78 shows inode/hardlink/xattr/permission regressions; not a drop-in.
- Refuse all symlinks or all existing output: avoids pivots only by sacrificing existing legitimate cases.
- Re-scan full source identities for late checks: O(N) work and still leaves check/use race.
- Descriptor-open + fstat before truncate reuses existing preflight facts; no new format, codec, reader or native machinery.

## Predicted evidence and disproof / kill conditions
1. Genuine installed O90 on Linux/macOS under O91's deterministic after-scan pivot to symlink→one-link source: original source overwritten; O93 must raise without source modification.
2. Genuine installed O90 post-scan FIFO no reader: child exceeds 7s; O93 must refuse promptly, with watchdog bound.
3. Ordinary fresh destination, existing independent file, symlink→regular and hardlink→independent regular produce **complete byte-identical archives** to authentic O90 on same host; Reader verifies/extracts.
4. Existing destination inode, valid hardlink aliases, xattrs (where host supports), read-only permission semantics and no orphan output files remain unchanged in ordinary successful paths.
5. No extra full payload in memory, no extra archive-sized temp storage, and no additional `stat` per scanned source entry on the ordinary path. Extra output descriptor syscalls must be measured separately; no official performance credit from micro tests.
6. Windows must reject any unsupported flags; no claims of unsupported POSIX FIFO/xattr behavior. Any actual host failure is evidence, not an invitation to weaken the evaluator.
7. Falsifier: any source overwrite, FIFO hang, normal archive-byte divergence, lost output inode/hardlink/xattr behavior, silently allowed changing output identity, or unacceptable measured economic debt blocks promotion.

## Scope and limitations
- No global filesystem TOCTOU immunity: source-root path, parent components, path rebinding after opening, actor races and crash/power-loss durability remain separate unproven cases.
- In-place truncation still exposes the known O75 failure-atomicity debt; do not claim O75 solved.
- Fast control of accidental new output path races via exclusive creation means benign concurrent creation may now fail rather than overwrite. Record this as deliberate safety/compatibility change.
- Fail-closed attack cases are negative product evidence. Only exact-head installed, source-fingerprinted, hosted tests count as product evidence.

## Decision
If a small descriptor patch survives authentic O91 attacks and O78 physical controls on installed packages without material negative economics, hand off for ownership/release convergence. Otherwise preserve the negative and consider stronger ownership/explicit publication API; do not relax invariants.
