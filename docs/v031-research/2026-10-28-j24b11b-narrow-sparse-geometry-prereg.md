# J24B11b — superseding **narrower** experiment after J24B11 failed a distinct pre-budget destination gate

**2026-10-28 UTC; frozen before J24B11b code change.** Preserve original J24B11 prereg `05c7ca775ee56d012ca2991a9cb5a303178ad364`, actual original [J24B11 hosted run #40762227735](https://github.com/FCMO-AI/.CMPCT/actions/runs/40762227735), and the failed rule. This is **not a retroactive green**; the original broader gate is RED.

## Observed failure / causal source boundary

J24B11 originally preregistered that even a *valid* original archive under `max_bytes=16383` must refuse **before destination directory creation**. Actual Ubuntu and macOS hosted jobs failed at `assert not undercap.exists()` after the Reader correctly refused the quota; the source of existing #573 Reader has `dest.mkdir(parents=True,exist_ok=True)` **before** the `max_bytes` sum/guard. That directory creation is a real existing side effect and is NOT fixed by #573's sparse SHA helper. Preserve it as separately classified product debt; the original broader test must not be labeled PASS.

## New narrower independent question

Can the same unchanged #573 sparse SHA staging helper specifically reject the authenticated `[16383,1,[0]]` / 8192-byte RAW physical extent without publishing a malicious file, changing a pre-existing content/inode canary or leaking any stage, while the legitimate original remains reconstructible? This is the cross-kind geometry question J24B10 raised, independent from **whether an empty destination directory is allocated by the pre-budget guard**. Neither success nor failure may erase the original `J24B11` red.

New frozen rule for the original undercap: require a correct `above limit` rejection and **no file materialized inside the directory**, allow its preexisting behavior of creating that empty directory, record whether it happened as `inherited_undercap_directory_created=true`. Preserve exact input bytes/hashes, target inode/canary conditions, stronger hostile malformed-extent fail closure, no-stage, installed-source SHA and host matrix; no Reader/Builder/validator/codec source changes.

**Disproof** of narrow J24B11b: signed malformed extent is accepted; any content, inode, or temp-stage corruption; original valid archive mismatch; wrong source identity; or inherited undercap writes a file. Do not interpret allowed empty directory as destination transactional safety. The broader original J24B11 remains falsified and must be corrected by the appropriate extraction authority separately.

## Alternatives / scientific integrity

The better control is not to patch #573 here or drop the original red. Run an independently labelled source-exact J24B11b on the same parent and preserve both the first failed and new measured receipts; post-result evaluator edits without prospective addendum are prohibited. If J24B11b passes, it supports only the bounded sparse decoder/commit seam, not a full product release or global extraction-budget guarantee.
