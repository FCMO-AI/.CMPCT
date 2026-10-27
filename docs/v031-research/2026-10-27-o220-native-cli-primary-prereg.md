# O220 — Existing Rust r24 native CLI versus Python Reader: primary-only execution and journal divergence

**Prospective freeze — 2026-10-27 UTC. Science-only.** Exact baseline: J24C02 #569 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; published v0.30.0/r24 remains unchanged. No product code, native ABI, parser, comparator, format, release or owner branch changes.

## Question / PARETOBONK

O218 #577 demonstrates 6.02–7.33x **function-level** CPython direct-PyList admission. O219 #578 already charges MessagePack decode and fails the >=2x generality discriminator on fully distinct 262,144 owners (1.510x/1.598x), narrowing a new CPython extension. O216 #570 demonstrates severe full-Reader S_CHUNKS open tax. **A different execution architecture already exists**: the Rust `native/cmpct-core/` r24 shared read-only handler, not a new native parser or implementation. Read `native/cmpct-core/src/lib.rs` before assuming equivalent journal semantics: it explicitly authenticates only the primary index and states that transactional recovery is unsupported.

The narrow question is whether **existing** Rust native CLI already exhibits a meaningful same-primary-index process/open performance advantage on authentic signed-wire-independent r24 S_CHUNKS archives with 4,096/65,536/262,144 repeated refs, while demonstrating and preserving its known signed-journal semantic limitation. This is a capability/proof-boundary comparison, **not** permission to replace the Python Reader.

## Hypothesis and controls

- **Prediction:** For a primary-consistent authenticated archive, both existing Reader and Rust native CLI admit the same valid geometry, refuse identical overdeclared/missing-owner corruptions, and return correct selected four-byte ranges. On the 65,536 and 262,144 repeated-reference profiles, Rust native CLI process-level info will plausibly consume less wall/CPU and RSS than fresh Python Reader info; require >=2x median wall *and* >=5ms absolute wall saving at 262,144 to call the full-CLI economic gap material. No threshold gardening.
- **Control:** Same physical archive SHA-256 for both, original authentic builder-independent O215 fixture; no source patches. Native `info` compared to Python subprocess info. Measure repeated fresh-process wall, child CPU, peak RSS and archive bytes; do not compare native process to warm Python library timing as a speedup.
- **Negative control / semantic limitation:** An r24 archive with a contradictory primary index but a later valid authenticated checkpoint is accepted by the Python Reader while native primary-only open may reject it; if observed, classify `NATIVE_JOURNAL_DIVERGENCE_CONFIRMED` and **never** claim native whole-product parity, even if CLI timing wins.
- **Hostile controls:** exact admissibility on primary-only overdeclared logical size and missing reference, plus selected range bytes; no raw ZIP mutation, no synthetic re-interpretation of clocks.

## Kill/narrow

Any unexpected acceptance, mismatched logical bytes, or identity drift invalidates the performance claim. If both CLIs are slower/equal, retire this Rust CLI performance route for these profiles. If Rust is faster but journal semantics diverge, preserve `PRIMARY_ONLY_NATIVE_ECONOMIC_HEADROOM_WITH_RECOVERY_DEBT`; next genuine prerequisite is independently gated transactional recovery (plus Python API integration), not promotion. If Rust itself exceeds 5ms/2x threshold, narrow as immaterial. Existing Rust handler's lack of journaling is known **in advance** and cannot be rescued by dropping that negative control.

## Scope and accounting

Hosted Ubuntu-24.04 only, native release binary prebuilt outside timings; Python package independently installed. Fresh process wall includes startup/import and flags symmetric CLI-to-CLI; native compilation is excluded but recorded as packaging/preparation cost. CPU + child VmHWM captured by OS wait4. No full Builder/extract benchmark, three-host platform proof, native signed journal parity, live file mutation, package/wheel economics, final release gate or v1 domination credit.

## Concurrency

Existing owners #569 Reader composition, #577 direct CPython list micro, #578 MessagePack decode cost; no product code overlap. Branch exists only to preserve decisive independent evidence. Discovery STATE is not a lock and not edited. If native compatibility is disproved from source or observations, classify explicitly and avoid implementing a duplicate native Reader.
