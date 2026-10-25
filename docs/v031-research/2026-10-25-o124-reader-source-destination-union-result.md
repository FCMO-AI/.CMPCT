# O124 — Reader own-source and destination safety union: exact-hosted result (2026-10-25)

**Decision: LINUX STATIC UNION POSITIVE; MACOS INHERITED STORAGE-MODE CONTROL NEGATIVE / FULL PORTABILITY NOT ESTABLISHED. NO MERGE / NO RELEASE.**

## Provenance and research custody

Prospective preregistration `67a1b5d11182d0351fd6370ebf8ca9ca9f1d080d` preceded all code mutation. Base owner [PR #294](https://github.com/FCMO-AI/.CMPCT/pull/294) head `700fa74df7d9101b3d00322ab5b3606ee64faf88`, Reader blob `66b1f84d849cc2a8470467e75e478f6dc5927c75`. Independent source-archive guard [PR #468](https://github.com/FCMO-AI/.CMPCT/pull/468) Reader blob `729ddc263f8d2d5ce2bbab7162461d19b0b2768c`. Composition Reader blob `80267375507cb4eca2d0a9e3e839fda3ce4249c4`. Current direct result-bearing CI source HEAD `cdbc1ee8203d3a39563fb05a4b786a54ab2f7b0e`, [Actions run 40239113650](https://github.com/FCMO-AI/.CMPCT/actions/runs/40239113650). First runs are independently preserved, including pre-test infrastructure errors and their corrected exact-copy isolation.

## Direct Ubuntu 24.04 scientific evidence

Real three-engine court **SUCCESS** on the installed authentic original r24 Reader, unchanged PR #294 parent, and O124 candidate, all under exact independent source bindings. Unmodified inherited owner module: **9 PASS / 0 FAIL / 0 SKIP**. Separately audited 12 source-alias experiments: four clean controls exact, three original source-destruction negatives, two parent hardlink/symlink refusals, **one parent single-link same-path source corruption**, and three candidate source-inode alias refusals with exact source SHA unchanged. All twelve child processes opened the real archive before attempting extraction; original and parent same-path returned process success despite source mutation, whereas candidate returned explicit error code 47 and preserved the source. Independent JUnit/JSON audit printed `O124_INDEPENDENT_AUDIT_PASS`, [job evidence](https://github.com/FCMO-AI/.CMPCT/actions/runs/40239113650).

Builder-produced source CMPCT SHA-256 before extraction: `52ed72ce389e5d836c14e156b7a52bc95971eb3c78bcab9f5a1926e40e572a01`; after erroneous same-path write (original and parent): `80754b8c58c7fe6f14a427f31415c4ef2fcffe5c6a43bc12653cffc9f04e6ff3`. Candidate preserved original SHA in all cases. Raw CI artifact **`12615789965`**, with JUnit, twelve complete `source_before_sha256`/`source_after_sha256` records and logs.

## macOS 14 genuine negative — do not relabel as PASS

[Same exact source workflow](https://github.com/FCMO-AI/.CMPCT/actions/runs/40239113650) completed **FAILURE** on macOS while running the *unchanged* nine-case PR #294 module: **8 PASS / 1 FAIL / 0 SKIP**. Failure was the preregistered structural S_SPARSE branch, not a reported source-inode mutation: the real macOS Builder classified the sparse-looking input as storage mode `5`, whereas the unchanged inherited test requires `S_SPARSE == 3`. The test stopped at its `assert reader.by[rel][6][0] == expected_storage`. The subsequent three-engine O124 court did **not** execute on macOS because of fail-fast step ordering, so **there is no independent macOS O124 archive-alias result** from this run. Raw macOS artifact **`12615709921`**. Do not weaken or skip the sparse test or claim three-platform parity to make this green.

## Instrumentation corrections and negative provenance

Earlier runs [40238498327](https://github.com/FCMO-AI/.CMPCT/actions/runs/40238498327) on both hosts failed before running tests: a global `tests/conftest.py` imported unrelated r25 experimental dependencies (missing Python `zstandard` on Ubuntu; non-portable `libzstd.so` lookup on macOS). The later workflow moved an **exact byte-for-byte copied test module outside `tests/`**, audited by `cmp`, without changing assertions, product behavior or test semantics. This eliminated unrelated conftest imports and exposed the authentic macOS storage-admission difference. The engineering evidence checker initially failed for PR-section formatting; it subsequently passed after PR body was completed without any validator changes.

## Hypotheses and causality

**Advanced/confirmed on Linux:** parent static destination guard has a specific remaining one-link same-path source-archive destruction gap; the additional fd-source-vs-output inode preflight closes this while preserving its nine inherited tests. The same file is loaded by three distinct Readers with source hash controls and real process outcomes. **Narrowed, not product-promoted:** macOS inherited storage selector does not satisfy the Linux sparse admission premise in this fixture. This limits the claim; it is not proof the O124 guard itself fails on macOS, and there is no Mac positive court yet. No general Discovery Engine policy lesson is earned from this single host storage difference.

## Limitations and exported costs

The new guard is **static only** and reads destination pathnames with `os.stat`, so TOCTOU attacks, relocated ancestors, reparse points and atomic destination ownership remain unresolved; #269/#294/#297/#468 own related pieces. Extra destination-stat calls cost O(number of existing non-directory leaves). No full same-runner extraction CPU/wall/RSS, temporary I/O, selective-read, native portable reader, or release performance ABBA measured. The performance CI workflow may report administrative SUCCESS with substantive benchmark **SKIPPED**, which gives zero promotion credit. On-disk revision24, original source archive, codec, thresholds and inherited test assert semantics unchanged.

## Counterfactual, decision, and highest-leverage next executable action

The cheapest prospective discriminator would have been **one original + parent single-link same-path Reader extraction with source SHA before/after**, then three-engine diff: it reveals the missing invariant more sharply than adding thresholds or broader fixture sets. Next: run the existing authentic three-engine archive-alias court **independently** on macOS without suppressing the parent's structural sparse negative, keep that negative reported separately. If positive, owner #294 can consider integration against O118, but only after complete inherited source/portability, full extraction economics, and a coherent descriptor-bound publication design for concurrent attacks. The current PR is **DRAFT** and must not be merged/released based on these focused results.
