# v0.31 static destination symlink containment — bounded interim product candidate (2026-10-23)

## Source, claim and ownership
- Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Scientific reproducible negative: [PR #264](https://github.com/FCMO-AI/.CMPCT/pull/264) / [Issue #265](https://github.com/FCMO-AI/.CMPCT/issues/265).
- Independent adjacent owners: #255 sparse atomic+SHA, #256 chunked NAME_MAX, #262 hardlink order, #268 Reader composition. Do not reimplement them.
- Scope: a **static, non-concurrent** fail-closed preflight for preexisting symlinks in the selected destination tree, before any archived member is materialized. This is an intermediate correctness improvement, **not** the final race-resistant solution to Issue #265.

## Primary falsifiable question and preregistered prediction
Can a conservative preflight of the *destination filesystem* reject inherited symlink ancestors and unsafe ordinary-file leaf pivots before a single archive object is written, while keeping ordinary non-symlink reuse and intentional safe symlink replacement working? Predict:
1. Exact-source hostile ancestor and BLOB-leaf falsifiers from #264 change from outside overwrite to `IOError`, outside bytes/inode unchanged.
2. A symlink ancestor of any archived entry (directory, file, hardlink, symlink) fails before materialization, including a lexically *later* pivot after a benign entry.
3. Existing regular files/directories without symlinks still extract normally; a safe archive symlink entry may replace a preexisting leaf symlink by unlinking the link inode (without following its target); a hardlink target that is a preexisting symlink fails.
4. `safe_symlinks=False` retains the established opt-out behavior; physical output and archive format never change.
5. A source root explicitly selected through a symlink may be treated as the *trusted selected root*, but symlinks **below its resolved root** are disallowed as parents.
6. Separate before/after source/outsider SHA and no partial member writes; on a rejected case, no archived payload is published anywhere.

## Competing approaches and why this one is deliberately limited
- Strong final route: POSIX directory capability handles, `openat`/`dir_fd` component-level no-follow, and fd-relative write/link/metadata/atomic publication for all storage kinds. This is the race-resistant direction supported by #264's microcontrol, but rebuilding the Reader during concurrent #255/#256/#262/#268 work has a much larger collision and regression risk.
- Mere `Path.resolve()` archive-name validation: wrong security boundary; rejects only lexical input.
- Preflight of the entire destination tree: irrelevant entries can be symlinks and need not block extraction; inspect only member paths and hardlink targets.
- This candidate is a smaller **static-only guard**. It does **not** close TOCTOU: a concurrent actor can substitute a parent after preflight and before path-based I/O. It MUST NOT be advertised or released as a complete security fix for attacker-controlled mutable destinations.

## Controls, economics, and kill/narrow
- Build valid r24 archives through the real Builder; verify content/SHA with the real Reader before each extraction; use synthetic TemporaryDirectory victims only.
- Exercise ordinary BLOB and symlink/hardlink controls plus an archive whose clean member sorts before a malicious later member; unchanged outsider bytes and no partial clean-member materialization are necessary.
- Use fast local/scoped hosted test and subsequently general suite. A test that checks only the thrown exception without inspecting outside bytes does not earn pass.
- Static preflight adds `lstat` per existing path component and bounded O(number of paths × depth) work, reducible with cached parent components; it does not add archived bytes, codec passes or decoded payload. Measure product overhead before promotion.
- Any failing benign overwrite, safe symlink replacement, zero-height tree or >NAME_MAX legitimate scenario blocks. Any observed concurrent pivot bypass narrows claim to static (already expected) and requires capability-root design; do not patch over it with timing-based retries.
- No new format/release, no threshold/benchmark evaluator changes, no weakening of strong tests or public safety claims.

## Continuity
Treat this as a short-lived composition-safe interim candidate. If the final POSIX directory-capability implementation overtakes it before promotion, subsume/remove the guard rather than carrying two expensive path-safety policies. Preserve the scientific negative and the independent stronger control in #264. Do not mutate the Discovery STATE cache for this intermediate state.
