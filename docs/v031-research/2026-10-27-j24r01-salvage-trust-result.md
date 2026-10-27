# J24R01 — result: truthful forensic candidate classification

Date: 2026-10-27 UTC. Scientific parent PR #291; product candidate PR #558. Preregistration commit `00d5a9feced0e198bd0b3dfef3ebfb7c55def1c4` preceded the first product modification `161def4db3fa3748dce5492cb0d033e58bea04c7`.

## Decision

**ACCEPT SCOPED TRUST-LABEL CANDIDATE; DO NOT CLAIM VERIFIED SALVAGE OR RELEASE READINESS.** Public `recover_blob_records` still enumerates plausible framed headers without decoding/authenticating payloads or authenticating committed-generation membership. It now labels every result `verified: false`, including genuine records. Existing `sha256` remains a *declared, unverified header claim*. The CLI emits the same JSON with the explicit marker. No change to archive format or the normal Reader's SHA-based integrity rejection.

## Baseline and inherited negative

O0 PR #291 / issue #292 / hosted negative run [40028078600](https://github.com/FCMO-AI/.CMPCT/actions/runs/40028078600): real revision-24 RAW Builder/Reader; a one-byte payload corruption leaves framed metadata unchanged and passes cheap salvage enumeration while genuine Reader rejects; separately forged uncommitted physical frame is also enumerated. This is a **forensic enumerator** not verified recovery. Original source Writer blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.

## Product implementation

`src/cmpct/transactions.py`: surgical additive boolean `verified=False` in every returned candidate dict, plus function docstring describing the exact trust boundary. Product blob after edit: `f901734c0a9785da2a2053b7cc01c5ffc3072a3d`. Existing offset, codec, usize, csize, crc32, declared sha256, scan admission and return list order unchanged.

## Independent hosted acceptance

GitHub Actions [40432643802](https://github.com/FCMO-AI/.CMPCT/actions/runs/40432643802) evaluated exact code head `18f17ff69304be33ea3c093504d1d4a7b51dbf35` with source/ancestry checks and genuine package installation. **All three OS jobs SUCCESS**:

| Host | Result | Raw artifacts |
| --- | --- | --- |
| Ubuntu 24.04 | SUCCESS | [12702208090](https://github.com/FCMO-AI/.CMPCT/actions/runs/40432643802/artifacts/12702208090) |
| macOS 14 | SUCCESS | [12703220648](https://github.com/FCMO-AI/.CMPCT/actions/runs/40432643802/artifacts/12703220648) |
| Windows Server 2022 | SUCCESS | [12702642433](https://github.com/FCMO-AI/.CMPCT/actions/runs/40432643802/artifacts/12702642433) |

Each job uses genuine Builder, genuine Reader and actual `cmpct recover-blobs` command; asserts positive valid RAW control, one-byte payload corruption rejected by Reader but still enumerated, malformed uncommitted physical candidate, plus **self-consistent digest/CRC frame appended outside the committed generation**. All four retain `verified: false` and CLI JSON is identical to the public library output. The unchanged O0 negative instrument runs in the same installed package and must still identify `SALVAGE_RETURNS_UNVERIFIED_FRAMED_BLOBS`; this was verified on all three hosts.

**Source-bound evidence only:** the hosted test result covers `18f17ff...`, while later documentation-only commits must be assessed separately. Do not claim a green exact final-documentary head until its checks actually complete.

## Strongest negative and unmeasured debt

- A valid header, a corrupted frame, a fake matching-header frame and a self-consistent uncommitted frame all remain unverified: **the patch does not recover data nor authenticate content**.
- The scanner reads the **entire** archive via `Path.read_bytes()`; peak memory still scales with full archive size, including when there are zero candidates. No throughput, memory, temp-I/O or full-product benchmark advantage is claimed.
- A consumer assuming dict equality to a six-key legacy schema may need updating; all legacy keys remain available, but exact shape is now seven keys.
- Checking member/codec authenticity requires a separate bounded decode, CRC, SHA, resource-limit and generation-ancestry design. Indexes may be damaged, so physical salvage and committed membership must not be conflated.
- The inherited scientific negative still detects corruption; "three-host PASS" here means **honest labeling**, not content salvage being safe for trusted restoration.

## Counterfactual and discovery

The decisive lower-rung experiment was already available in PR #291: compare a real Reader rejection with a salvage-listed same-header corrupted RAW payload. A single machine-readable `verified: false` discriminator suffices to prevent downstream callers from interpreting a header-declared digest as an authenticated result. A second self-consistent-but-uncommitted frame exposes why full CRC/SHA alone would still not establish archive membership. **No Discovery Engine policy mutation justified.** No collision found on `recover_blob_records` beyond O0 #291, which is intentionally inherited.

## Integration and next decision

PR #558 remains draft and stacked on PR #291; safely rebase/cherry-pick only after owner review. No version, format, benchmark, public claim or released Reader changed. The highest-leverage remaining recovery work is a separately preregistered bounded scanner or authenticated salvage mode with strict codec/decompression limits, disk/RSS economics and independent commitment proofs. Promotion requires inherited CI, hostile-input compatibility and release law, not just this three-host court.
