# J24P01 — macOS source-fingerprint utility repair, preregistered before workflow change

**Observed original run:** GitHub Actions [#40769201049](https://github.com/FCMO-AI/.CMPCT/actions/runs/40769201049), macOS job `123101475537`, exact HEAD `06d8e62a5983e642b5b202cd83fb37738bdd3283`.

**Original failure:** `sha256sum: command not found` inside workflow's *pre-install provenance capture*. The checkout and ancestry/source-unchanged checks all succeeded; the actual Reader, corruption, extraction and independent referee steps were **SKIPPED**. This is **INFRASTRUCTURE BLOCKED**, not a product defect or a pass. Preserve the failure and artifact #12852145931.

**Prospective smallest repair:** replace only that shell `sha256sum` invocation with Python standard-library SHA-256 on the same unchanged `tests/conformance/v24-pack.json` bytes, writing the same `manifest-sha256.txt` receipt. Leave frozen manifest, installed product/codec test, referee, adversarial cases, thresholds and all other workflow semantics untouched. No assumed cross-host result before the new source-bound job actually executes.

**Disproof:** repaired source fingerprint differs from the actual manifest file, checkout SHA mismatch, changed frozen conformance bytes or a test/independent referee failure. All retain their original force.