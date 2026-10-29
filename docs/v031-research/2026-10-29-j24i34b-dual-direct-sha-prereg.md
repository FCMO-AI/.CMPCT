# J24I34b preregistration — dual direct SHA commitment must both hold

**2026-10-29 UTC, before modifying native source or generator.** This is a prospective adjacent hardening test to the already-open [J24I34 #759](https://github.com/FCMO-AI/.CMPCT/pull/759) symlink verification candidate. Preserve J24I34 original prediction/test and #754 negative exactly.

## Causal source gap discovered after first candidate

The initial candidate adds symlink kind 2 to the native streaming `verify_complete()` loop. Exact source inspection then found a stricter defect: `complete_member_identity()` in inherited `vzip_dispatch.rs` returns an optional *present logical row SHA* immediately, before looking at the direct CMA4 physical blob SHA. `read_blob_range()` for RAW intentionally performs locality-preserving physical-byte reads without hashing unseen bytes. Consequently, if a r24 direct member declares a 32-byte logical digest matching its **mutated** physical payload but retains an unchanged CMA4 header digest for the **original** payload, the native strong verifier may accept while Python first authenticates the physical blob and refuses. The first J24I34 adversarial cohort did not test this coupled alteration; the simple contradictory-present case changes only the row SHA and is caught. This new question is materially different and more stringent.

## Preregistered prediction and kill

Construct from an actual Builder-origin symlink r24 archive: modify exactly one byte of a RAW target payload, then re-sign both physical-index copies and replace its *optional row SHA* with SHA-256 of the **mutated** bytes. **Do not update the CMA4 original SHA or CRC.** Independent referee must establish: index signatures/checksums valid, physical record SHA/CRC invalid, optional logical-row SHA matches mutated raw, original physical metadata persists and only designated payload byte changed. Python strong verify must refuse. The initial J24I34 candidate with native present-row precedence is expected to report `Ok(1)` (a false integrity proof). The repair is killed if it still accepts that exact wire, if first-party unchanged/valid controls regress, or if broad hash grammar changes appear.

## Stronger architecture / competing alternative

Do not add a second full-payload hash. For `Storage::Direct(index)`, check the optional logical row digest **against the physical header digest** before accepting the complete-member identity; then the existing streamed digest authenticates bytes against that same physical identity. This enforces both independent logical/physical declarations with one streaming SHA. For other storage families, keep inherited semantics unchanged. This adds one fixed-size CMA4 header verification/read to **present-SHA direct entries** in complete verify; bytes/CPU overhead must be explicitly credited, not advertised as free.

## Evidence and ownership boundaries

Use original J24I30 generator and detached `audit_symlink_wire.py.parse()` (no CMPCT imports), plus a new no-product-import independent physical metamorphic referee. Maintain historical result #754, #755 native SHA admission owner and #751 hardlink alias owner. J24I34b remains a product candidate, not an already proved fix; live Ubuntu/macOS actual compiled Rust and Python tests and exact-head artifacts are mandatory. No release, on-disk revision, frozen evaluator, policy or Discovery STATE edit.
