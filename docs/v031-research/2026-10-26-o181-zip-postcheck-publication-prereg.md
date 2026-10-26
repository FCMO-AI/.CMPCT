# O181 preregistration — can the verified ZIP stage be substituted at final publication?

Date: 2026-10-26 UTC. Parent exact HEAD: `427a47badc2c6bf6f32c97ec0b35d00d6a8a9ff8`, O179 PR #512; product Reader blob `9e399aa9cbc25c3d7b7c8663f5a039ade9d80aa7`. This prediction is committed **before instrument implementation**. Historical O157 (#497) demonstrated pre-write symlink and hardlink replacement in O149/O150; O179 subsequently bound writes to the exclusive fd and rejected pre-write pivots but explicitly left a compare/rename gap. This is an **independent final-publication falsifier**, not another ZIP writer or an alternative attack on the already fixed pre-write window.

## Primary question and falsifiable claim

After O179 has verified `fstat(stage_fd) == lstat(stage_path)`, can a directory writer replace that pathname just before the authentic Reader's `os.replace(stage, requested_output)`, causing `CMPCT.export_zip` to report success for ZIP contents or physical identity not produced by its own writer? The strongest control is a correct, unperturbed export on the same independent revision-24 RAW vector and the same exact Reader.

**Prediction:** In a deterministic interleaving at `os.replace`, replacement of the stage pathname with a distinct, valid but incorrect ZIP will make `export_zip` return success while the output holds attacker-controlled member bytes. On POSIX, replacing the stage entry with a symlink or hardlink to another disposable regular inode can create an unauthorized final path alias; the original victim bytes are *not* modified during the export. Each scenario must distinguish output substitution from unrelated-victim overwrite.

**Disproof / narrow:** The installed exact O179 Reader detects/rejects the late pivot, or the resulting output still has the authentic expected ZIP contents and no unauthorized aliases. An independently verified failed archive parse or failure to reach the post-verification rename does not count as a successful attack. A setup/provenance failure is infrastructure, not a product win/loss.

## Oracle rung, controls and action

Use the frozen independently authored `tests/conformance/v24-direct-codecs.json` RAW `raw.bin` vector, exact archive SHA and logical contents, installed O179 Reader outside checkout. Preserve and verify original CMPCT input, existing valid ZIP output and unrelated victim sentinel. As cheap primitive sanity check, local POSIX `fstat` → pathname substitution → `os.replace` already demonstrated ZIP member substitution before this preregistration; **primitive-only evidence gets no CMPCT product credit**. The hosted court will use the authentic Reader unchanged, monkeypatching only `os.replace` as a deterministic scheduler for a concurrent namespace actor, then delegate to the real OS function. Include fast Deflate and stdlib ZIP writer routes. Emit JUnit and structured per-case evidence, retain artifacts even on failure, verify source Git blob and archive SHA; run Linux/macOS and, where meaningful, Windows. Never use protected or real user files.

Alternative explanations: test monkeypatch might alter writer semantics; isolate it strictly to final rename and confirm correct bytes *prior* to the swap in the original stage, stage identity, and correct clean baseline. OS-specific removal of an open inode may fail: classify unsupported cases as unmeasured, never silently skip them. Distinguish injected adversary ability (directory write privilege) from ordinary exports and never infer exploitation likelihood from deterministic scheduling.

## Scope and decision

This could change an integration decision: O179's positive pre-write ownership guarantee does not authorize adversarial **publication authenticity** if its last-check gap is exploitable. If confirmed, an untrusted-writer directory requires either genuinely fd-bound publication or an enforceably private publication namespace / narrowed trust contract, with exact semantics and cross-platform controls. Do not claim a complete fix, performance win, release, or modified format. No change to O179 owner's branch, shared discovery state, historical evidence, validators, or frozen gates. Owner handoff should identify the precise window and minimal witness, not prescribe a speculative universal fix.

## Cost and anti-local-optimum rationale

Compared: (a) repeat pre-write O157 — already answered, BONK; (b) immediate second staged-writer patch — fails evidence/coordination BONK; (c) perform the single inexpensive post-check final-publication oracle — selected because one reproducible wrong-output witness can falsify a **whole publication-authenticity claim** and materially narrow the release boundary; (d) benchmark current O179 — lower VOI before this safety fork. If the outcome is already conclusively known from direct hosted evidence, retire the lane and avoid redundant variants.
