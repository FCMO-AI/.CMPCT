# J24C12 — Published-vs-strict-vs-native Reader triplet: preregistration

Date: 2026-10-28 UTC. **Science/economics only; not a release or safety-equivalence claim.**

## Source custody / current authority
- Published release baseline: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Correctness-composed strict candidate: PR #630 `0a128ff55c7ae0f14c6bdf019a81b40f0d894eff`, Reader blob `b37b786966ac1506a0439567d4a58eea472d85f8`.
- Optional installed ABI3 candidate: PR #641 `a639570c1e9f9b36decae3893265be74a6d185b0`, Reader blob `9bca5d1047f9c78984b945d7ca90e3149fe429ab`.
- Product/format release remains v0.30.0 / r24; compare *valid* identical authenticated r24 bytes. The published baseline has weaker corrupt-input rejection and is **not safety equivalent**.

## Primary question / alternative explanations
Does ABI3 recover enough of the strict Reader's measured admission overhead for the combined *real installed Reader* to avoid a meaningful wall/CPU/RSS regression against the actual published v0.30.0 Reader on many-reference valid archives?

Do not infer this from #641's 10–15x strict-Python constructor ratio or #644's 2.35–2.66x strict-Python session ratio: neither uses published main as economic control. A plausible counter-hypothesis is that the released Reader already opens fast because it omits the stronger admission, so ABI3 can still be slower than main even as it greatly outperforms strict #630.

## Fixed experiment and eligibility
- Authentic non-editable wheels, built from exactly the three Git sources, separately installed in isolated virtual environments; no source imports, monkeypatching, or mixed installed packages.
- Single Runner Ubuntu 24.04 / CPython 3.11 first (cross-host not asserted).
- Independently serialized r24 records via the preexisting O215 Builder-free generator, identical bytes for all arms; full signed archive SHA pinned in each emitted receipt; user-facing logical bytes and six exact range answers checked against generator independently of either Reader.
- Profiles: 4,096 references/one owner; 65,536 references/one owner; 65,536 references/256 owners; 262,144 references/one owner. Each owner has four bytes. Six fixed ranges covering early, middle and late; no fixture-identity-dependent dispatch.
- Each profile runs 3 ABBA cycles, balancing all three arms through a 6-worker sequence with an alternating mirrored order; each worker executes 3 fresh Reader sessions. Order and worker identity retained raw. Three arms: released, strict, native. Strong full read/verify only for the 4,096-ref profile, all three arms; the others are *selective-session* questions, not full-file verification.
- Separately measure open, list, six ranges, optional full-verify, close, complete-session CPU and wall; process startup separately. High-water RSS from Linux `/proc/self/status`; never treat missing RSS as 0.
- Each worker asserts installed Reader Git blob identity (with only LF/CRLF transport normalization), archive SHA and exact answer digest. Native worker must prove C entrypoint available and returns a positive result on the authenticated index, otherwise the native claim fails.

## Preregistered decision
For each 65,536+ profile, report median-of-worker-median for each phase and complete session. The specific *published-floor debt* signal is **both** `native/released >=1.05` *and* `native-released >=3 ms` in **wall** (and likewise CPU separately); report wall and CPU flags independently, never combine a convenient subset. No negative/debt signal is not proof of universal parity. Confirmed positive native-vs-strict differences serve only as mechanism attribution, not as an independent product win.

RSS growth **>8 MiB** for native vs published is an additional caution flag; absent data is unknown. Preserve any negative even when the independent installed-native-vs-strict comparison is strong. Exact outputs, source identity, and all recorded samples are hard gates. Full extraction, mutable sources, recovery, Windows, other Python ABIs, full parity corpus, creation, compressed data and distribution are outside this rung.

## Cheapest evidence / opportunity cost
Re-use O215 fixture provenance and J24C09 phase semantics instead of designing a new Reader or optimizing a single threshold. This closes a missing baseline-comparator fork and determines whether future convergence should focus on Reader admission, per-read execution, or integration overhead. If no material comparison is possible (environment/build failure), mark **infrastructure-blocked**, not a product loss. Original raw data and a separate auditor must be durable; decisions remain unlocked until evidence exists.

## Coordination
This is a source-identity-pinned, independent triplet replication with **zero product source edits**. #641 owns ABI3; #630 owns strict custody; #644 owns strict-vs-native session evidence; #574 owns discovery-state reconciliation. No concurrent implementation claim is taken over. Do not modify the existing PRs, released source, frozen oracles, thresholds, or discovery state.
