# J24X02 — Preregistered optional sparse file descriptor mode operation

Source: PR #270, head 5a5909d6a902e22778463eb2ea11b3e732c988d2, stacked branch. Existing owner PR #255 supplies verified sparse extraction; PR #270 supplies NAME_MAX repair. Scientific J24X01 PR #571 and issue #572 demonstrate released sparse corruption/recovery defects. Distinct Windows optional-mode defect mirrors chunked extraction PR #536 but occurs inside sparse_extract.py. No duplicate sparse implementation.

Prospective prediction: Valid independent r24 sparse archive extracts on POSIX but fails when os.fchmod is absent. A feature-detected descriptor-only mode operation allows exact extraction on all three OS without skipping SHA or CRC. Logical SHA mismatch and physical blob corruption must fail before publishing, preserving existing content and cleaning temporary files. Unexpected ValueError from a present mode function must not be swallowed. Legacy S_BLOB controls stay valid.

Alternatives: no mode operation on all platforms loses POSIX fidelity; pathname chmod creates race exposure; broad exception catch hides bugs. Use the narrow existing chunked-platform pattern. Compare original/candidate where possible and retain negative results.

Kill conditions: a positive valid sparse file rejected; malformed SHA or physical blob published; target damaged; unexpected failure hidden; source mismatch; or inherited test failures. O(logical sparse size) SHA overhead from PR #273 is unchanged and remains release-blocking (~102ms at 128MiB). Inheritance from #270 does not establish integration with newer #567/#569. Format r24 and release v0.30.0 unchanged; no product/release or benchmark credit from a focused passing test.

Next: independent signed-wire three-host installed package court with original source fingerprint and raw evidence, then owner handoff and full gates.