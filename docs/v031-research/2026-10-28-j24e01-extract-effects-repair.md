# J24E01 — prospective test/implementation repair (frozen before edit)

2026-10-28 UTC. Initial hosted exact-source workflow [#40784919546](https://github.com/FCMO-AI/.CMPCT/actions/runs/40784919546) on `f8f2e6987801523e8fb8651539b57cec06f8ddef` found **131 valid-graph errors** and **200 mutant-test failures** on Ubuntu (full log job 123155578087). Preserve this RED as independent evidence, not an infrastructure failure.

## Mechanism-error diagnosis

1. **Valid alias-of-alias chain rejected.** The model detects an already memoized alias at the end of a new walk and checks the *immediate row kind* rather than the underlying regular-file owner. This wrongly rejects valid K_HARDLINK -> K_HARDLINK -> K_FILE chains. Repair: memoize *root owner identity* alongside effective bytes at every resolved node; require the root to be K_FILE for all aliases. Remains iterative and O(n). Add an explicit alias-of-alias positive and alias-to-directory negative. Retain the 50k chain.
2. **Some purported hostile mutants were actually valid.** The court grew the declared size of a valid sparse file by one without moving its data extent; that simply adds a permitted trailing hole. It is not an invalid input and correct acceptance must not count as a candidate failure. Repair the test constructor to inject a truly invalid negative declared length for every seed, plus a second contradictory positive-length direct S_BLOB mutation where available. Keep **all 2,000 original seeds**, all valid graph comparisons, four known hostile shapes and the long chain; no threshold loosening.

The original frozen preregistration remains immutable. Retain raw failure and compare repaired hosted result at new exact SHA. Neither fix changes released Reader code or creates product security credit. If root memoization does not restore valid alias chains, or any truly invalid mutation is accepted, preserve the new negative and revisit representation assumptions.
