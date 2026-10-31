# J24P14 — Bind console-script semantics to final CMPCT wheel, before installation

Date: 2026-10-31 UTC. **PREREGISTRATION / PREDICTION ONLY at this commit.** Research/productization candidate, no merge/release credit. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0 / format r24. Composition parent: #867 `3809fe47b38783d7ce22a4f36f0f8f008b008164`, itself stacked on #864 and #854; #850 owns official packaging. Do **not** change those owners, shipping codec, format, ABI, release lock, benchmarks, or Discovery shared state.

## Question / scientific baseline
#870 J24P10 physically established that two fully RECORD-consistent wheels with all 17 `cmpct/` members identical can install successfully but generate different `cmpct` launchers when solely `entry_points.txt` changes to an inert `sys:exit` target. #867 deliberately attests **only package bytes** and is honest about the exclusion; successful package-byte custody alone cannot certify installed CLI behavior.

**Primary falsifiable question:** Can a small, stdlib-only, pre-install check bind the final retagged wheel's unique `[console_scripts]` entry to the source `[project.scripts]` contract, reject semantically altered or extra commands, preserve three authentic official CMPCT wheels and require genuine installed CLI smoke on each hosted OS, without altering #867's other protections or requiring a duplicate pip mapping emulator?

## Prediction, stronger control and kill conditions
- Source `pyproject.toml` explicitly declares exactly `cmpct = "cmpct.cli:main"`; all three authentic 23-member wheels have exactly `[console_scripts]\ncmpct = cmpct.cli:main\n`. Predict PASS on all three; preserve RECORD/full-package checks and source SHA.
- Modified `entry_points.txt` with consistent RECORD but `cmpct = sys:exit` is rejected; changing the authoritative manifest to the same alternate script **and** rebuilding an appropriately matching wheel should pass source-bound comparison (general contract, not hard-coded only to this version). If that alternative is not realistically runnable, classify as metadata-contract evidence only.
- Reject missing/duplicate `entry_points.txt` (including overlapping metadata root), missing/extra `console_scripts`, `gui_scripts`, unknown sections, duplicate or case-shifted option names, empty/invalid target, duplicate section, malformed UTF-8 and non-UTF-8 path. Avoid parser option-name normalization accidentally accepting a differently named script.
- Check the **actual final wheel** before `pip` installation and before any wheel-supplied script is executed. The authentic installed `cmpct --help` must exit 0 and show usage on Ubuntu, macOS and Windows. Do not execute intentionally modified launchers.
- A preinstall pass plus a successful smoke proves basic CLI routing, not byte identity of the generated wrapper, general installer trust, publisher authentication, concurrency freedom or an adversarial OS. A `--help` invocation can be implemented by altered code that still prints usage; preserve this limitation rather than claiming stronger proof.

**Kill/narrow:** Reject candidate if an authentic platform wheel fails; if changed target/extra script passes; if correct source manifest and wheel disagree; if no real console executable is exercised; if check runs on an intermediate wheel; if CI uses a different SHA than the tested artifact; or if meaningful maintenance/portability cost is disproportionate to the gap.

## Alternatives and boundary
A simple hard-coded `cmpct.cli:main` check (J24P10 oracle) is the cheapest reference; **source-bound contract** is selected to prevent silently drifting from a changed `pyproject.toml`. Parsing TOML with stdlib `tomllib` requires Python >=3.11 for the **build gate only**; installed CMPCT remains Python 3.10–3.14 compatible. Full launch-script hash cannot be a cross-platform invariant without pip/distlib/OS-specific wrapper contracts; use real CLI invocation instead. Do not emulate pip or duplicate #867's 17-file attestor.

## Evidence plan and counterfactual
1. Prospective red test before implementation against the authentic wheels and inert modified entrypoint.
2. Independent stdlib metadata-oracle test and hostile parser cases. Real immutable CMPCT wheels, tampered self-consistent RECORD, source-manifest mutations and clean A/B.
3. Hosted exact-head final-wheel check, 3 OS smoke, 15 Python platform-combinations where feasible, exact-SHA receipts and general CI. No claim of complete gate success until checked.
4. Counterfactual from J24P10: the original product contract should have separately enumerated **installer-generated scripts** rather than treating package-root SHA as an end-to-end execution guarantee. One case does not justify a global discovery-policy amendment.

Question currently **UNDECIDED**; predictions deliberately recorded before code/CI.
