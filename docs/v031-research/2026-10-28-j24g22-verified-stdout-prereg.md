# J24G22 — Verified-stdout custody: memory vs integrity (prospective research)
Date: 2026-10-28 UTC. Parent/source: immutable published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, format revision 24, v0.30.0.

## Preregistered primary question
Can a bounded-memory `cmpct cat` style implementation avoid the Reader's full logical member materialization **without releasing any logical bytes before the whole member has passed the inherited authenticity checks**, on genuine first-party direct and CDC archives?

## Baseline and controls
Published CLI performs `sys.stdout.buffer.write(ar.read(member))`; `read()` completes before output. Published `read_range()` exposes bounded ranges but does NOT promise whole-member integrity (notably RAW slicing and CDC/CHUNKS). Repeated ranges may add index scans and decoded cache. Compare (A) actual `ar.read()` then sink; (B) premature emit-on-range counterexample (never promote); (C) stage range bytes into a `tempfile.TemporaryFile`, validate SHA before sending, and only then replay. The strongest simpler control is A; the meaningful architecture alternatives are (i) spill to disk, (ii) two-pass verification with fd/snapshot immutable custody, or (iii) changed streaming authentication semantics.

## Predictions and killing conditions
P1: on a pristine, first-party archive, A and C agree exactly on all output bytes and SHA for direct and CDC (record actual storage kinds, do not assume).
P2: a physically corrupted late RAW byte that preserves earlier bytes, valid signed index, and original BHDR causes A and C to refuse, while B emits a prefix or corrupted bytes before learning of failure. If not RAW, do not claim RAW evidence.
P3: C's authenticated staging can bound **emitted pre-verification bytes to zero** in the evaluated cases. This is not an assertion of low **global RSS**: Reader chunk cache and VZIP decode may dominate; record them honestly.
Kill productization if source's first-party direct admission is too small for meaningful memory savings, if C changes accepted/rejected semantics, or if CPU/temp I/O is too high. Do not weaken `read()`, change CLI product API, change format, relax any tests or classify partial stdout as authenticated output.

## Independent adversarial checks
Use actual first-party Builder archives plus intact/mutated physical variants, fingerprint/archive SHA, source refs, subprocess-separated RSS/CPU, output-prefix counter, original Reader verify/open, and paired same-input comparisons. Any unproven data paths remain unmeasured.
Benchmarks only justify their examined regimes, not whole-product claims.

## Concurrency/ownership
Searched live open PRs/issues for `cat streaming`, `stdout verified` and `cat spool`; no directly owned narrow implementation found. This branch touches ONLY research and CI. Do not modify neighboring Reader/Writer/CLI owners. Discovery STATE.json belongs to #574, stays unchanged. This is independent science, not a new default feature or release authority.
