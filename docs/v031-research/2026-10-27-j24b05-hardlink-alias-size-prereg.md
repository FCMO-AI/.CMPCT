# J24B05 — memoized hardlink alias-size admission (prospective, before source edits)

**Date:** 2026-10-27 UTC. **Exact parent:** #342 `a480d7ae2f1480f15e73eda2b04e48b1a75e66b1` (memoized O(N) terminal-owner resolution); published floor `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24. **Independent failure evidence:** J24B04 #610, three-host hosted 2026-10-27. **Different owners:** #609 direct owner/symlink checks; #569 composed Reader; #342 owns graph resolution. This child does not rewrite any owner branch.

## One question and falsifiable prediction

Does one equality guard against the **terminal regular-file owner** close authenticated `K_HARDLINK` alias-size contradictions during **strict preflight**, without a second chain traversal or loss of O(N) graph admission? At this parent, #342 validates target existence, cycles and terminal type but does not compare authenticated row sizes. Prediction: size 128/128 passes; aliases declaring 136, 120 or 0 against terminal owner 128 fail as `ValidationError`, including a mismatch on an intermediate link with an otherwise matching outer alias. Both forward and reversed index order, chain/star, RAW/Zstd physical owners should transfer. The original J24B04 fully reauthenticated archive remains the scientific baseline; tests must use the same semantics.

## Alternatives / PARETOBONK

- Re-walk each alias to locate the terminal and compare size: simpler to write but O(N²) for chain, contradicted by #342 source-exact evidence (4096 chain original 683.797 ms vs memoized 16.427 ms, with ~6–7% star overhead already measured).
- Check only the immediate target at every ordinary Reader call: not equivalent to strict whole-index validation, and touches #569 source ownership. Keep a separate Reader residual-risk claim.
- Compare against cached terminal owner in #342's single graph walk: no new payload decode, no wire changes, one additional integer comparison per alias. This is the candidate.

## Frozen acceptance / disproof

1. Copy original #342 O1 signed-graph inherited tests unchanged, including 1024-link chains/star, reversed order, missing/indirect target, cycles, symlink/dir owner.
2. Add Builder-independent logical-size mutation of a real Builder-made r24 archive with both compressed index copies reauthenticated and physical payload byte-identical. Test owner 128; alias sizes 128, 136, 120, 0. Test RAW/Zstd if tool supports; preserve the actual codec in receipts.
3. Test terminal consistency on deep chain, a middle-link mismatch and reversed index order; a valid 4096-link chain must retain near-linear graph work. Use same input/source rather than comparing archives with different metadata.
4. Independently inspect mismatch evidence by reading authenticated index rows and physical owner declarations; do not treat Builder/Reader roundtrip alone as independent evidence.
5. **Kill/narrow:** any valid archive is rejected, any inconsistent row is accepted by strict preflight, a regression reintroduces quadratic chain traversal, the check requires broad Reader rewrites or a material increase in star/open CPU without compensating protection.

## Scope and debt

Only `src/cmpct/validation.py` strict parser admission plus tests/evidence are in scope. No `reader.py`, Builder, frozen benchmarks, format revision, performance thresholds, release or `docs/discovery/STATE.json` edits. `CMPCT.read/read_range/verify` of an archive opened without strict preflight may still accept malformed alias sizes until the Reader #569 owner composes an equivalent invariant. No product-wide closure, no release, no three-platform claim until hosted evidence establishes each.

Research truth and negative records from #610/#342 remain immutable. Commit this preregistration before changing parser source or tests.
