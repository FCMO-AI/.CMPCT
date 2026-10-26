# O181 — ZIP postcheck publication authenticity, deterministic cross-platform negative witness

Date: 2026-10-26 UTC. **Decision: O179's last `fstat/lstat` verification does not bind the inode published by a subsequent pathname `os.replace` when another actor can write to the staging directory.** This is a measured scoped concurrency defect, **not** a correction to the Reader, and not a claim about ordinary exports or attacker prevalence. Published product remains v0.30.0, physical format r24 unchanged.

## Provenance and preregistered fork

O179 owner #512, exact parent `427a47badc2c6bf6f32c97ec0b35d00d6a8a9ff8`, original installed Reader Git blob `9e399aa9cbc25c3d7b7c8663f5a039ade9d80aa7`. O179 had already closed O157's *pre-write* symlink/hardlink overwrite through original-fd writing; it explicitly identified an unfixed postcheck `os.replace` race. O181 preregistered this distinct late-publication question at `7e1053413056c1d5788e57cc5e9c735c6c1e8b0a` before adding its instrument.

The input is frozen, independently authored `tests/conformance/v24-direct-codecs.json` (blob `d10b7dab9126d39e819a74279c186363a163f2ef`), `raw.bin` carrying exact bytes 0..63, independently SHA-verified archive `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d`. Genuine Reader installed outside checkout, original Git source blob authenticated separately on every host. No product changes, no regenerated weaker fixtures, no relaxed inherited comparator.

## Exact negative witnesses

The instrument `tests/research/o181_zip_publication_falsifier.py` runs **clean same-reader export controls** for both direct-Deflate and stdlib ZIP writers. In the hostile cases, the only interception point is the real Reader's final `os.replace(stage, output)`, which follows the exact existing `fstat(fd)` versus `stat(stage, nofollow)` check. Before calling the real OS replacement, a deterministic independent directory actor replaces only the staging path. The writer's original stage is first verified to contain the **correct complete ZIP**. Source archive, originally valid prior output, unrelated victim file, and stage cleanup are independently checked.

1. **Wrong member, valid ZIP**: stage path replaced with a new ZIP containing `attacker.txt`. Reader returns success; output is regular and parseable but the authenticated `raw.bin` is missing.
2. **Same member, wrong bytes, valid CRC**: stage path replaced with a valid ZIP containing `raw.bin` of exactly 64 but incorrect bytes (`X` repeated). Reader returns success; superficial filename, member length and ZIP CRC checks pass, but CMPCT's authenticated bytes are absent.
3. **POSIX symlink**: stage path replaced with symlink to an unrelated existing valid ZIP; after Reader reports success the requested output is a symlink to that unrelated inode.
4. **POSIX hardlink**: stage path replaced with hardlink to an unrelated existing valid ZIP; after Reader reports success requested output is regular but shares the unrelated inode. **The victim's bytes are not modified by the export**; this is an output-alias and authenticity failure, not an O157 pre-write overwrite replay.

These are direct observations of the authentic Reader under a controlled interleaving. The same-name case defeats a repair narrative based solely on valid ZIP or correct member paths. This is **not a random-race probability measurement** and cannot show hostile actors can modify every deployment's staging directory.

## Hosted result and raw evidence

Initial decision-bearing run [40324289640](https://github.com/FCMO-AI/.CMPCT/actions/runs/40324289640) at exact `1991793db7c5fe0702d07d990174c72302e10078`: **Ubuntu 24.04 8 PASS; macOS 14 8 PASS; Windows 2022 6 PASS / 2 POSIX-only SKIP; total 22 PASS / 2 SKIP / 0 FAIL**. Here PASS means an expected negative **product** witness was successfully reproduced; it is not a positive product/security outcome. Windows separately reproduced ordinary wrong-name and same-name wrong-byte publication, but did **not** execute symlink/hardlink cases. Raw artifact IDs: Ubuntu `12651005414`, macOS `12649839466`, Windows `12650132849`. Each workflow job confirms installed Reader blob `9e399aa9cbc25c3d7b7c8663f5a039ade9d80aa7`, frozen independent archive and `O181_AUDIT` JSON/JUnit.

An initial hosted run [40323652551](https://github.com/FCMO-AI/.CMPCT/actions/runs/40323652551) at `25992231c996f9ebf34842471269e3eccd56f253` also passed its smaller 16-PASS/2-SKIP court. The later court strengthened adversarial scope to same-name wrong-byte, self-consistent ZIP CRC. An audit refinement after 1991793 includes these cases explicitly in negative-attack **counts**, not merely per-case assertions. Latest audit-only commit `6ef8a06027d56ee14249e4411cd9d95d9b2e7b19` requires a fresh exact-head hosted confirmation; do not call that final commit green until observed.

## Strongest self-critique / product boundary

O179's valid positive claim survives: binding the original stage *during writing* prevents O157-style victim overwrite in the tested pre-write scenarios. O181 falsifies only a **stronger publication-authenticity inference** under directory mutation rights. It does not destroy prior ZIP before the final rename; under an attacker-injected successful rename the requested output is deliberately replaced, by a different inode. No cross-host performance, crash durability, unsafe ancestor, filesystem ACL or eventual release claim is earned.

A further `lstat` just before `rename` cannot close the logical time-of-check/time-of-use gap against an actor who can schedule between distinct calls. The next owner should evaluate enforceably controlled publication namespace, real handle-bound publication, or a narrowed/verified writable-directory threat model; preserve O143/O149/O157/O179 tests. Do not create a third independent ZIP writer or silently drop ordinary successful-overwrite semantics.

### Cheaper lower-rung primitive bound (local Linux, not CMPCT/CI product evidence)
A standalone local Linux `O_TMPFILE` + `linkat(AT_EMPTY_PATH)` experiment directly published an unnamed fd inode to an **absent** target, preserving byte and inode identity. Retrying link to an existing filename returned `EEXIST` and preserved the prior output; it therefore does **not** by itself implement CMPCT's existing successful overwrite semantics. This is a route discriminator only, not an attempted CMPCT repair. Primary system documentation: [open(2)](https://man7.org/linux/man-pages/man2/open.2.html), [link(2)](https://man7.org/linux/man-pages/man2/link.2.html); Microsoft's [FILE_RENAME_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info) describes a different handle-based platform option, **not tested here**.

## Handoff and release truth

Question answered: **YES, the last-check/name-rename window allows success with unauthenticated output** under a deterministically injected directory actor on all three tested platforms. The cheapest counterfactual discriminator was a single correct staged ZIP inspected immediately before an intercepted `os.replace`, with the forged output valid by independent ZIP parsing. No discovery-policy change is justified. `docs/discovery/STATE.json` is staleable and intentionally untouched; other agents own its reconciliation. No merge, release, format, benchmark, policy or source-evaluator mutation. Recheck exact-head CI and notify #512 (owner) and #497 (negative scientific baseline) using links to raw evidence. Completion of this research episode does not complete the CMPCT campaign.
