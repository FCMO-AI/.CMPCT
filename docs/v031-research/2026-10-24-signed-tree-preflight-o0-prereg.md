# O0 preregistration — signed r24 impossible tree versus strict preflight

**Date:** 2026-10-24 UTC. **Status:** preregistered before adding new tests or product changes. **Owner:** this independent preflight-validation lane; no Reader rewrite.
**Source-exact base:** draft PR #338 `c56839b38abc7a744c25f1ae6a4b1d5b4a99f2bc` (stacked on Win32/APFS union #336). Released v0.30.0 / revision 24 unchanged.

## Why this question is worth testing
PR #338 established a real signed r24 tree-topology failure: a regular member and a descendant can both be independently read but cannot be extracted together. Its Reader extraction preflight now rejects it before member writes; the independent strict `preflight_archive()` still validates rows, canonical aliases and hardlink cycles, but appears not to enforce non-directory ancestors. Divergent acceptance between strict preflight and extraction is an evidence/consumer boundary, not a new compression mechanism. **Do not modify #338's Reader owner or its tests.**

## Primary falsifiable prediction
On the **unchanged exact parent source**, two fully reauthenticated r24 indexes containing (`parent.bin`, `parent.bin/child.bin`) and a held-out file/hardlink alias ancestor (`z_alias.bin`, `z_alias.bin/child.bin`) will pass `preflight_archive` even though `CMPCT.extractall` rejects them before writes. Both archives are constructed by the real Builder, mutate only logical index names/rows, preserve physical blob bytes and reauthenticate both index copies / footer.

The disproof is a preflight rejection of these precise signed archives on the unchanged base, an invalid fixture, or rejection already performed in current `validation.py`; any such result stops a redundant fix. Valid explicit/implicit directory parents and legitimate hardlink aliases must still be accepted.

## Alternatives and cheapest decisive instrument
- **No change / document extraction policy only:** plausible because selective read still works, but strict structural preflight exists to reject impossible archive structure before a caller treats it as safe to extract. This is the cheapest control.
- **Invoke extractall inside preflight:** rejected; side effects, memory/IO materialization and host dependencies contradict independent bounded preflight.
- **Share/refactor Reader's component trie immediately:** source overlap and regression risk against active #338 owner, disproportionate to this narrow proof. Prefer separate bounded strict validation, then consider refactoring after integrated evidence.
- **Change wire format / ordinary Reader open:** rejected. Readable members are not necessarily a materializable tree; keep selective reads/recovery intact.

The negative instrument first requires unchanged preflight to raise `ValidationError`; expect failure on exact base, valid controls pass. After proof, implement a single-pass order-independent component trie in `src/cmpct/validation.py` under existing ParserLimits: accept `K_DIR` explicit/implicit ancestors; refuse proper path ancestors marked `K_FILE` or `K_HARDLINK`. Preserve the strict symlink question as a separate safety policy (safe extraction controls it), not an invented format prohibition.

## Controls / kill conditions / economics
1. Same physical archive bytes before and after logical index rewrite; both primary/footer index hashes valid. Real `preflight_archive` is invoked on disk.
2. Same adversarial test remains unchanged between source-exact negative and candidate positive; reject independently of row order, nested depth and hardlink alias. Preserve positive implicit/explicit directory and valid hardlink controls.
3. `extractall` still rejects impossible topology before member publication, and the ordinary Reader retains selective `read` of individually valid members.
4. Memory/time work must be bounded by total validated path components, with no payload decompression beyond existing structural index decoding; measure at least a representative local synthetic profile if feasible, but **no end-to-end performance approval from a microbenchmark**.
5. Exact-head CI must run real installed CMPCT on Linux and at least one other host; no release promotion with inherited red gates or unmeasured performance.
6. Stop/retire if baseline already rejects, or if the changed preflight falsely rejects legal directory parents or aliases, weakens parser limits, changes format, or consumes unnecessary global memory.

## Concurrency and evidence custody
Open PR #338 owns extraction fix and signed-archive fixtures. This lane only touches strict `validation.py`, a new dedicated test/workflow, and the separate hardening note. Coordinate by stacking on #338 exact SHA and linking evidence to owner. No force-push, no rewriting discovery state, no merging or release in this lane. Current discovery STATE.json is stale relative to the signed-tree safety frontier; PR plus exact-head hosted evidence are authoritative. Preserve the failure outcome and unexpected contradictions explicitly.
