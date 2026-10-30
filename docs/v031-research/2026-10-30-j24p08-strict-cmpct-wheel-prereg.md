# J24P08 — CMPCT-specific strict wheel member contract (prospective)

Date: 2026-10-30 UTC. **Candidate only — do not publish, merge, bump version, or claim release credit.**

## Provenance / why this is a different frame
Parent #854 exactly `57bc9a00a6dbba079131de15f88995fd75ea91b6`. Prior positive evidence: three authentic official-style wheels (Ubuntu, macOS, Windows, 23 ZIP entries each) carry **zero PEP 427 `.data/` entries**. #858 proves `.data/purelib` can overwrite installed native bytes; #862 studies `.data/purelib` overwriting Python. **New decisive negative**: J24P07 #863's general member-to-installed-target mapping passes `.data/data/lib/python3.13/site-packages/cmpct/native_codec.py`, yet real Linux venv's `sysconfig.data=<venv>`, `purelib=<venv>/lib/python3.13/site-packages`, and real pip overwrites native_codec.py with inert payload. Thus a portable, scheme-independent static relocation map is not sufficient; stop attempting to emulate arbitrary pip destinations in a general tool.

## Distinct hypothesis
For official CMPCT wheel packaging (not all valid third-party Python wheels), require **no wheel member under any top-level `*.data` directory** and reject any duplicate, path-traversal, Unicode normalization/casefold alias, Win32 reserved name or file/ancestor ambiguity. A positive official-style wheel must remain accepted on all OSes without hard-coded fixture bytes or Python minor versions. Compose with existing #854 complete physical SHA/RECORD/Mach-O/minOS gate and #852 Intel runtime evidence. No format, ABI, Reader, Writer, codec or runtime change.

## Alternatives / bounded carrying cost
A complete pip scheme-aware destination oracle and post-install full-tree hashes would be stronger for arbitrary wheels but carry version-, scheme-, filesystem- and installer-specific obligations. Conservative CMPCT-specific no-`.data` policy eliminates that complex namespace entirely because no current official-style wheel depends on it. Adversarial route: a zero-`.data` wheel still collides through root path normalization/casefold; reject via portable strict lexemes. Remaining risks (malicious files outside wheel, future packaging changes, forged record signatures, extraction races, pip post-processing) do not disappear and must not be misclaimed.

## Frozen hosted acceptance (before new source/test)
- Exactly one root .dist-info/WHEEL, no `*.data` top-level members.
- Accept three fresh genuine official-style Ubuntu/macOS/Windows wheel artifacts and one self-consistent unrelated package-member extension.
- Reject PEP427 .data/purelib, .data/platlib **and .data/data**, both orderings where relevant, even when targets are not syntactically duplicated.
- Reject path alias `..`, `.`, doubled separators, backslash, leading slash, trailing spaces/dot, NFD/casefold-equivalent names, Windows device components and a regular file shadowing a descendant path.
- An isolated pip install must show that .data/data actually overwrites the Python member in a normal venv (inert file only; no execution).
- Hosted Ubuntu/macOS 15/Windows 2022 test the same source file and at least the same cheap control fixtures, with exact source SHA and uploaded logs.
- Do not weaken #854, remove its real Mach-O/minOS/RECORD tests, or replace the already-proven Intel runtime control with static matching.

**Kill:** any authentic current official-style wheel rejected, or any alias/.data payload admitted. If future official packaging genuinely needs `.data`, this deliberately narrower rule must be reconsidered with a stronger *actual installed-state* proof; do not silently disable it. Strictly O(number of member names × path length) metadata work and no runtime cost. A green unit test is not publication authority.

## Coordination
#854 owns physical wheel guard; #850 owns publication; #858/#862 own falsifiers; #574 owns shared Discovery STATE. This independent bounded strict CMPCT publishing profile does not edit those owners or shared state. Post-result evidence must separate local exploratory data, new hosted controls and release/installed product truth.