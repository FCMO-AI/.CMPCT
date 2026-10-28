# J24I01 — Exact-source v0.31 integration: B06 signed extraction budget × prospective candidate fingerprint

Date: 2026-10-28 UTC. Status at preregistration: **prediction only**; no integration code or CI result exists on this branch.

## Repository and source authority

Released CMPCT remains v0.30.0/r24 at `main@80c358f8824ec1b20d349c92ed94c898090969b0`; current v0.31 development remains `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. No merge/release/version/format authority is inferred.

This branch starts from prospective fingerprint owner **#266** at exact `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1` (eight observed CI workflows SUCCESS, including actual General Tests `39975603659`), with its current unchanged Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, identical to published main and v0.31 development. Independent signed extraction-budget product owner **#690** at exact `adcf38cb5be022567c1faf6538aefeef2f6b72de`, Reader blob `20f6e257a07a61a4c1aebe23ae23e4109d6c41c8`, is the only product modification to transplant. The original signed-wire regression test and targeted three-host workflow are also to be copied **byte-identically** from #690; do not rewrite/ease test or new product behavior. Original owner branches remain untouched.

#690's original installed 3-host court `40734382594` is SUCCESS, while General Tests `40734382711` is 798 PASS / 4 FAIL at exact source: pre-existing historical v0.30 fingerprint/attribution assertions. Its official parity run `40734382793` failed at correctness preflight and **did not produce a substantive base/candidate performance verdict**. These are independent inherited observations, not this branch's results. #266 repairs the epoch-of-authority problem prospectively without modifying historical released fingerprint records. This integration asks whether those two independently positive parts really compose.

## One primary falsifiable scientific/engineering question

Does a minimal **exact-source, no-reimplementation composition** of #266's prospective v0.31 fingerprint/CI custody and #690's signed nonnegative extracted-length guard retain every inherited correctness invariant, reject authenticated negative/boolean symlink/hardlink budget cancellation, pass real General Tests and 3-host installed regression, and enable substantive same-source performance parity without freezing or rewriting v0.30 release evidence?

**Strong simple control:** each owner alone; #266's true General Tests SUCCESS and #690's true 3-host installed safety SUCCESS, plus #690's four inherited general CI failures. The combination must be retested on its own exact HEAD; parent greens are not transferable by assertion.

**Prediction:** 3-host signed-wire tests and ordinary v0.31 General Tests PASS when source-identical #690 Reader/test/workflow are composed on exact #266; all authentic input semantics and r24 bytes remain. The published v0.30 lock, thresholds, evaluator, corpus, package/version and comparator do not change.

**Disproof/kill:** any inherited positive test fails; any signed hostile size publishes more bytes than `max_bytes`; compilation/installation fails; source/blob identity drift; one platform fails without justified skip; CI tests remain red for new causes; genuine official 0-byte size and 5%-AND-3ms timing gate fails; or runtime path is not actually exercised. If performance is skipped/unmeasured or runner/flakiness confounds it, retain an honest pending result, not release credit.

## Concurrency, constraints, and alternatives

#690, #609 and #615 independently own overlapping Reader/validation code; Phased1's new #693/#697 are negative controls of B06 and remain separate. #616 already owns general PR integration topology tooling, and #574 owns discovery STATE. This branch **does not** write their code or state, implement alternative validation, take over their research or add a competing graph tool. It is a direct-v0.31, narrow coherence check of **#266 + #690 only**; separate #609 direct size, #615 alias sizes, #569 Reader and #572 sparse extraction still require later real composition and will not be declared fixed here. If their new HEADs evolve, re-read before any late shared action.

Other available routes: (a) leave all four inherited reds in #690, which blocks executed performance; (b) change immutable v0.30 lock to green tests, explicitly forbidden; (c) skip four tests, forbidden; (d) build a bespoke composite Reader, unnecessary and risky. Copying exact owner source onto an already-green prospective CI frontier is the cheapest trustworthy higher rung.

This is **product integration evidence**, not a new encoding research win, independent new bug fix, release artifact or merge permission. Archive output size must remain byte identical, create/extract CPU/wall/RSS and temporary I/O still require genuine exact-head checks. Preserve all negatives, no false green. No customer or private corpus data.
