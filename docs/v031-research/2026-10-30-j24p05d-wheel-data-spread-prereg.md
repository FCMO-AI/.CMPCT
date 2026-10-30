# J24P05d — Pre-result wheel .data/purelib spread-collision oracle (2026-10-30)

**New structural route / prospectively preregistered before executing a .data collision test.** Prior J24P05/J24P05b adversarial evidence proves raw ZIP names are not sufficient due to path normalization/casefold. A simple guard rejecting dot/parent/repeated separators might fix those cases, but **PEP 427's .data spread step** is a different destination mapping even for canonical path names. This is independent source-exact research stacked on #854; no owner code modified.

## Primary hypothesis
A wheel with perfectly canonical, unique ZIP paths and full SHA-256 RECORD can contain one legitimate `cmpct/cmpct_core.cpython-311-darwin.so` native Mach-O member and an additional `cmpct-0.30.0.data/purelib/cmpct/cmpct_core.cpython-311-darwin.so` inert member. #854's independent validator may accept because it sees exactly one direct native and all ZIP/Mach-O/RECORD checks pass. A normal PEP 427 wheel installation may spread the second member into the same `site-packages/cmpct/cmpct_core...` destination, overwriting the validated native. This would falsify the adequacy of a simple noncanonical-path-rejection patch: normalized installed-path projection must account for `.data` installation scheme ownership.

**Strong controls:** original authentic dual-arch wheel without extra member; same wheel plus disjoint `.data/purelib/cmpct/unrelated.txt`. Inspect with original #854 validator; install with `pip --target` in separate temporary roots and compare exact installed native SHA/size. *Do not execute or import altered native data*. Record if pip rejects or gives an ordering-dependent result; those are valid negatives. Avoid arbitrary `.. /` or path traversal for this test.

## Cost/proof/decision
Small local source-bound A/B first (same input native, same target and pip version; final RECORD fully rehashed). If it reproduces, physical hosted two-host run is stronger later but not required to decide that raw-casefold normalization alone is insufficient. If no overwrite, retire this .data family pending changed installer semantics. All claims research only; zero product/release/format/ABI credit. Neither #854 nor #850 mutation authorized by this note. Preserve negative observations and exact source SHA and wheel SHA; subsequent result must distinguish static gate from installed bytes.

## Coordination
Existing #854 validator owner, #850 installed native packaging owner, and #574 Discovery state remain untouched. This court is independent of the prior J24P05b path-alias tests, and does not need a second source-of-truth state database. PEP 427 calls installation unpack+spread with .data/purelib relocation; normative reference https://peps.python.org/pep-0427/.
