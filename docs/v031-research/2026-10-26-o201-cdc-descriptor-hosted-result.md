# O201 — Authentic S_CDC descriptor-length versus range semantics (hosted result)

Date: 2026-10-26. Status: **SCOPED NEGATIVE CONFIRMED ON POSIX; WINDOWS RANGE NEGATIVE OBSERVED WITH INDEPENDENT EXTRACTION BLOCKER. RESEARCH ONLY.**

## Source/provenance
- Scientific [PR #534](https://github.com/FCMO-AI/.CMPCT/pull/534), preregistered **before** the instrument: `3fb392abbdfa53f9ca9b960b8871f6d960476018`.
- Frozen canonical source parent: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, unchanged Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`; product sources untouched.
- Result-bearing scientific run [#40384239325](https://github.com/FCMO-AI/.CMPCT/actions/runs/40384239325) generated from PR head `c142e5ab1a0067b1b740509f4c438491ee32dc20`, using exact-source installed packages on Ubuntu 24.04, macOS 14 and Windows 2022.
- Raw data: [Ubuntu artifact #12680135467](https://github.com/FCMO-AI/.CMPCT/actions/runs/40384239325/artifacts/12680135467), [macOS #12679862245](https://github.com/FCMO-AI/.CMPCT/actions/runs/40384239325/artifacts/12679862245), [Windows #12679538525](https://github.com/FCMO-AI/.CMPCT/actions/runs/40384239325/artifacts/12679538525). Each contains the head/source identities and `decision.json`; the job logs also emit all per-case operation results as `O201_CASES`.
- Instrument adapted with attribution from O198/#532's complete-r24 wire court, changing S_SPARSE to the separately owned S_CDC descriptor. The archive contains one physical RAW `ABCD` blob, correct CRC, correct logical SHA, complete primary/tail indexes and footer.

## Direct outcomes

| Host | valid ln=4 verify/read/range | valid ln=4 extract | malformed ln=1,2 full verify/read | malformed ln=1,2 read_range(2,2) | malformed extract | Scientific job |
| --- | --- | --- | --- | --- | --- | --- |
| Ubuntu 24.04 | PASS / ABCD / CD | PASS / ABCD | PASS / ABCD | **empty bytes instead of CD** | rejects chunk length | SUCCESS |
| macOS 14 | PASS / ABCD / CD | PASS / ABCD | PASS / ABCD | **empty bytes instead of CD** | rejects chunk length | SUCCESS |
| Windows 2022 | PASS / ABCD / CD | **FAIL: missing os.fchmod** | PASS / ABCD | **empty bytes instead of CD** | fails at os.fchmod earlier | **FAIL** |

With `ln=1`, `read_range(0,4)` returns `A` on all three hosts. With `ln=2`, it returns `AB`. With `ln=5`, the late range `CD` happens to be correct, but POSIX extraction still rejects the chunk-length mismatch. These are exact observed operation outcomes. Native Reader and actual Builder malformation frequency remain **unmeasured**.

**Primary scientific conclusion (scoped):** malformed yet internally checksum-consistent CDC descriptors can pass full `verify()` and `read()` while producing silently truncated `read_range()` answers, including on Windows; the POSIX extraction path independently refuses to publish malformed chunks. A scientific job marked SUCCESS classifies a reproduced negative, not a passing Reader safety gate.

**Secondary independent product defect:** Windows valid S_CDC extraction fails on `AttributeError: module 'os' has no attribute 'fchmod'`, raised in `_extract_chunked_verified` before its `except OSError`; recorded separately as [issue #535](https://github.com/FCMO-AI/.CMPCT/issues/535). This failure makes Windows's overall positive control fail and is **not** evidence that extraction published incorrect bytes. It may affect S_CHUNKS sharing the same method; that S_CHUNKS manifestation still requires its own genuine Builder control.

## Decision, alternatives and self-critique

The lower-rung authentic-wire falsifier changes the decision from source-inspection hypothesis to a verified inconsistency of the Python r24 Reader on POSIX, plus direct corroborating selective-read outputs on Windows. A row/index hash is not a signature, so the adversarial index itself does not constitute breaking a trusted external author. No remote code execution, actual Builder bug, or release promotion has been demonstrated.

Do **not** implement another isolated S_CDC-specific patch in this scientific branch: O198/#532 [issue #533](https://github.com/FCMO-AI/.CMPCT/issues/533) already established the corresponding S_SPARSE inconsistency, with O193/#521 as its Reader owner. The preferred bounded product discriminator is one provenance-authenticated validation of each indexed extent/chunk's declared versus actual physical sizes, plus legal sparse geometry, *before* any full verify or selective reads. It requires true historical r24 archive controls, hostile variants for both storage classes, actual Reader/native compatibility, and O(total index references) admission cost (open/list CPU, RSS, concurrency and recovery). No fixed benchmark or corruption gate may be relaxed.

## Continuation
1. Coordinate the separate O201 CDC negative with O198/#532 and Reader owner #521; require one coherent geometry contract and actual source/CI evidence, not competing patches.
2. Address Windows `os.fchmod` portability under #535 separately; prove valid S_CHUNKS and S_CDC output and metadata on a real installed Windows package.
3. Leave this research PR Draft. No product, benchmark, format, release, or discovery STATE mutation was performed.
