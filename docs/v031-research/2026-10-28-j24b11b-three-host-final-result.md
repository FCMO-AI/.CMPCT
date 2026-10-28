# J24B11b — final three-host source-exact sparse quota transfer result (2026-10-28 UTC)

**Decision:** `EXISTING_SPARSE_HELPER_PREVENTS_J24B10_OVERFLOW` on unchanged #573 Reader/helper, **scoped to authenticated malformed sparse extent**; original broader J24B11 remains **FAILED** because the Reader creates the destination directory *before* budget preflight. No merge, release, format change or generalized quota safety claim.

## Frozen baseline and experiment separation

- Source owner: PR #573 at `9f269ce8a13b54e44679942d018b226e8dce4d6a`. J24B11b research head `75ce4a56dea85163b7b69c8e66ba9941d9c81514`, Reader and sparse helper untouched.
- First J24B11 original head and three-host run [#40762227735](https://github.com/FCMO-AI/.CMPCT/actions/runs/40762227735): **FAILED** broader assertion. Actual deficit: `dest.mkdir` occurs before `max_bytes` refusal, leaving an otherwise empty destination directory. That negative is not overridden by subsequent narrower evidence.
- J24B11b was **separately preregistered before modifying test code**, commit `d2e0ee1a5923a838c4b418c3530b56ee753866fb`. Narrow question is solely whether the existing SHA-verified sparse helper prevents the confirmed J24B10 signed extent overflow from publishing bytes or modifying pre-existing canaries. The original negative remains recorded.

## Three-host court and actual results

[GitHub Actions #40762489965](https://github.com/FCMO-AI/.CMPCT/actions/runs/40762489965) **SUCCESS** for all three installed-package jobs, as confirmed from each job log on 2026-10-28 UTC:

| Host / job ID | Result | Artifact ID / ZIP SHA-256 |
|---|---|---|
| Ubuntu 24.04 / `123078101626` | SUCCESS | `12849840074` / `645d87ae15ba4fc5a893c9680ad4e45e58b976a07994c38555ade8c40bebc864` |
| macOS 14 / `123078102271` | SUCCESS | `12849700305` / `ab8d00763878a33c3cc381b8ad8aebe1acfdb468fdda4a29a5536d0fd3ac4af1` |
| Windows 2022 / `123078102135` | SUCCESS | `12849375839` / `fff7c8cbbb8252c94ae2d6c8b90ca23d5c648ae67cf491d6cebe6c6ecab2c724` |

All three original logs report the same substantive terminal decision `EXISTING_SPARSE_HELPER_PREVENTS_J24B10_OVERFLOW` and the same rejection paths:

- `malformed_existing_extract_refusal = OSError: sparse extent overrun: sparse.bin`
- `malformed_fresh_extract_refusal = OSError: sparse extent overrun: sparse.bin`
- `malformed_preflight_refusal = ValidationError: file 'sparse.bin' sparse extent 0 length mismatch`
- `malformed_read_refusal` and `malformed_verify_refusal = OSError: file integrity failure: sparse.bin`
- Explicit `original_j24b11_gate = FAILED_PRE_BUDGET_DIRECTORY_CREATION`

The receipts record the installed source from actual external `site-packages` locations and the exact source HEAD. They are genuine installed-host tests; however this entry's independent verification inspected GitHub job status/logs and artifact metadata, not the downloaded payload contents or a separate binary referee.

## Mechanism, limits and decision

The existing staged sparse writer checks actual decoded bytes against the remaining authenticated extent before replacing any target. It rejects the specific signed geometry that the published Reader instead expanded from 16,384 budget bytes to 24,575 output bytes in PR #700 / issue #701. This is evidence **for a preexisting candidate fix component**, not a new implementation or a complete extraction transaction.

Critical remaining product debts:

1. `extractall(max_bytes)` creates a destination directory before budget admission (#573 original J24B11 negative).
2. #573 inherited ~101.6 ms additional 128 MiB sparse-hole SHA latency and unmeasured end-to-end cost.
3. Named-stage race #528, hardlink and symlink size ownership (#693/#697), direct blob physical-size #609 and composite Reader integration remain independent.
4. Final complete same-head General Tests, performance parity and release identity / promotion require their own authorization and evidence.

**Counterfactual:** Source inspection of #573's existing `write_sparse_verified` extent bounds can avoid duplicate candidate implementation, but cannot justify a multi-OS acceptance claim; the installed three-host court was decision-changing. Separating prebudget side effects from malformed sparse-byte publication avoided masking an authentic earlier failure. No Discovery policy change is justified from this single transfer.

**Next:** Return the exact-head result to #573/#255 and owner #701; do not create a competing sparse helper. Preserve the red `mkdir` requirement and address it in the existing Reader/extraction ownership line; then measure sparse-hole performance and cross-kind effective-budget behavior before any candidate promotion.
