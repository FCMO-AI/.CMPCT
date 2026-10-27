# J24B03-A — exact-head same-candidate safety admission result

2026-10-27 UTC. **Scientific evidence-enablement / conformance: PASS 3/3**, not a release/promotion verdict.

## Prospective decision and source identity

The [prospective J24B03-A contract](2026-10-27-j24b03-acceptance-composition-prereg.md) was committed in `db54cbc6f69d341b872f12b813f4eedd8106af79` **before** the workflow implementation `5c1b774868a910bf8af34069d3b191b70ecabb94`. On that exact candidate branch head, [Actions #40573053228](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053228) completed **SUCCESS** on Ubuntu 24.04, macOS 14, Windows 2022 (Python 3.11), independently building the exact unchanged released `main@80c358f8824ec1b20d349c92ed94c898090969b0` and candidate packages. Both checkouts were asserted equal to their expected full commits; raw Reader and validator Git object IDs were recorded in original per-platform receipts. Candidate Reader git blob remained `33deb74e196f7e40aa8351b6ec426a24255d5eec`. **No product source mutation was made for J24B03-A.**

The GitHub Actions `github.sha` / artifact filename suffix `ffc67ef48d95fe8006ab11df88b73cc33e511d81` represents the pull-request workflow merge context. The jobs **explicitly checkout and assert** the immutable **PR head** `5c1b774868a910bf8af34069d3b191b70ecabb94`; do not conflate these two Git objects.

## Direct measurements — combined in ONE source-exact job per OS

Each platform reproduced unchanged original J24B03 24-authenticated-wire corpus and unchanged separate H2 forensic on the **same paired source revisions**:

| Measurement / acceptance | Ubuntu | macOS | Windows |
|---|---|---|---|
| Original paired 24-image court and detached referee | PASS | PASS | PASS |
| Valid size controls | 6/6 | 6/6 | 6/6 |
| Contradictory signed direct-size cases correctly rejected by candidate | 18/18 | 18/18 | 18/18 |
| Historical next-index RAW spills absent from guarded candidate | 2/2 | 2/2 | 2/2 |
| Independently frozen codec vectors | 3/3 | 3/3 | 3/3 |
| Original/H2 independent reference receipt verification | PASS | PASS | PASS |
| H2 historical malformed physical BHDR acceptance observed | 10/10 | 10/10 | 10/10 |
| H2 candidate malformed physical BHDR rejections | 10/10 | 10/10 | 10/10 |
| H2 valid file and symlink controls | 2/2 | 2/2 | 2/2 |
| H2 historical one-byte physical-metadata-offset shift | CONFIRMED | CONFIRMED | CONFIRMED |

The original scientific H's immutable `assert selection['hex'] == PAYLOAD[7:15].hex()` for every hostile field **remains falsified**. Its existing [workflow #40565133857](https://github.com/FCMO-AI/.CMPCT/actions/runs/40565133857) was RED on all three OSes exactly because the published Reader's `rml=1` case returns the shifted eight bytes. **J24B03-A does not rewrite H, mark it continue-on-error, waive that historical negative, or turn its scientific prediction green.** The independently preregistered H2 observation supersedes the *physical explanation*, not the truth/status of H's failed prediction.

### Original hosted artifacts

[Run #40573053228](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053228) retained the original signed-wire H2 corpora, the unchanged two separate independent audit receipts, source identities and controls from each OS:

- [Ubuntu artifact #12766945908](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053228/artifacts/12766945908), GitHub-provided ZIP digest `sha256:bab34dfec7be0e2c7ca50fcc57dde7202ef8650b69416f5cca7ecd4c6cfa0904`.
- [macOS artifact #12765598511](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053228/artifacts/12765598511), GitHub-provided ZIP digest `sha256:6e2192da6e53e39c3cd6c5ff3be3531e3ef2aa886ba95ff79b65f0a1c11a44d1`.
- [Windows artifact #12766131841](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053228/artifacts/12766131841), GitHub-provided ZIP digest `sha256:9ac59784c70a17806f366dbbabcd5bea6e726e04f1ad7f0e846b7d4e6fae8ac9`.

The artifacts were enumerated via GitHub's hosted metadata, and the independent referees ran to PASS inside the jobs; this author does **not** claim an additional off-host byte-level redownload/audit of these three ZIPs.

## Decision boundary, negatives, economics

**`DIRECT_SIZE_AND_BHDR_SAME_HEAD_3OS_ACCEPTANCE_CONFIRMED`** (conformance/evidence-enablement only). This stitches two already successful, independently frozen original safety courts together on the same source/OS matrix. It adds no format, Builder, Reader, index, policy or codec improvement.

- This does **not** make the old frozen J24B03-H test green. The existing combined H workflow can still report a red check despite the candidate's supported security repair; preserve this distinction.
- The guard's [J24B03-P](2026-10-27-j24b03-direct-range-cost-result.md) standalone economic result is a measured **+135.47 ns / +37.94%** RAW selective-query cost versus released main. It did not trigger its **pre-existing +500ns absolute** kill gate, but neither proves end-to-end parity nor erases the cost.
- The J24B03-A pass does not address `K_HARDLINK` alias sizes (separate #610/#615), other storage kinds, payload-level strong SHA on a valid physical header, mutable source inodes, positional read/extract concurrency, exact full-product parity, or #569's measured **27–28×** structural cold-open debt.
- At previous candidate `afcffd59...`, General CMPCT Tests had **782 passed / four fingerprint-or-surface failures**. Source-level identical test/related blobs suggest inherited drift, but no exact main-run differential proves that attribution. Native Authority previously also failed an undiagnosed multi-command precheck. New head's statuses are separate volatile CI facts and must be checked afresh; no red waived.

## Counterfactual / Discovery Engine

A host-specific original 24-wire + H2 side-by-side execution is a cheaper decisive integration gate than inventing more malformed fixtures or rewriting the historically false premise. The prospective observable is **same source revision, same OS, two independent audited courts**. The mechanism can be reused when Composer #569 eventually pulls the guard. One successful evidence-integration run does **not** earn a new Discovery Engine policy: `docs/discovery/STATE.json` is staleable and its reconciliation belongs to #574; this PR did not mutate it.

**Next:** hand the confirmed guard semantics/receipt to #569's owner, preserve their same-effective-index/fd-owned Reader constructor, minimize additional cold-open O(N) work, and run complete combined correctness/performance/recovery/portability gates before any merge or release. No source or on-disk format changed.

## Post-result direct historical source-run reconciliation (2026-10-27 UTC)

The preceding cautious statement about missing a released-`main` CI differential is **now superseded** by an actual existing archived original main run retrieved **after** the initial result was recorded:

- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` [General CMPCT Tests #37243801009](https://github.com/FCMO-AI/.CMPCT/actions/runs/37243801009), executed **2026-10-04 UTC** on Ubuntu: **782 passed, four failed in 370.39 s**. Its raw [pytest artifact #11318004000](https://github.com/FCMO-AI/.CMPCT/actions/runs/37243801009/artifacts/11318004000) and actual full job log show exactly these failure test IDs:
  1. `tests/test_performance_base_native_release_custody.py::test_historical_native_materializer_is_release_fingerprinted`;
  2. `tests/test_public_attribution.py::test_surface_revision_records_attribution_campaign` (`0.30.a` vs test's `0.29.k`);
  3. `tests/test_v030_ci_topology_split_receipts.py::test_authoritative_v2_classifier_is_release_fingerprint_driven`;
  4. `tests/test_v030_release_fingerprint_surface.py::test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs`.
- At candidate source `afcffd59a0ab3ac1133f1a968fcf649fd96a9eda`, [General CMPCT Tests #40565134324](https://github.com/FCMO-AI/.CMPCT/actions/runs/40565134324) also directly executed **782 passed and these same four failed in 319.40 s**. Both are **genuine separate GitHub-run observations on different UTC dates/runners** and do not claim execution-time equivalence. They support a precise **inherited four-test failing-set** attribution. This is now stronger than the prior blob-identity-only inference, but still **does not authorize ignoring** the four failed release/evidence requirements.
- At candidate `5c1b7748...`, [Native Authority workflow #40573053147](https://github.com/FCMO-AI/.CMPCT/actions/runs/40573053147) has overall conclusion SUCCESS **only because the `native-authority` job was SKIPPED** behind `latest-head-impact`. It **did not** repair or rerun the older actual native-authority command failure; do not report its workflow-level green as a Native Authority gate PASS. Similarly, `CI Topology` and `Engineering Evidence` truly ran and passed at that head.

This post-result comparison changes the **cause attribution** of the four General Tests, not the product conclusion. Preserve the original cautious historical claim above as the earlier knowledge boundary rather than silently rewriting it.
