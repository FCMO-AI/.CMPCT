# O66 — Exact historical Builder custody under O63 single-buffer + rollback composition

Date: 2026-10-25 UTC. Status: PROSPECTIVE PREREGISTRATION — before implementation/results.

## Authority, ownership and isolated question
- Canonical `FCMO-AI/.CMPCT` development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; released checkpoint v0.30.0 / r24.
- Parent **O63 PR #418** locked at `18e32cae012f5dca9fc47f10d194f8b81005c85c`, candidate Builder Git blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`, codec `dc3446b0eed82edfba9380e3885a20aa45577899`.
- O59 PR #414 and O62 PR #417 already own the historical O47 custody mechanism, not O63. This O66 is a **new composition court on O63**, not a replacement of O59/O62, O60, O63, or canonical development.
- Explicit source negative: generic O63 Tests run #40170913670 had 809 pass / 7 fail; three historical parent parity tests lacked O47 commit in shallow checkout. Other four v0.30 fingerprint/surface failures are independent, remain unmodified and unclaimed.
- Primary question: **Can the unchanged original O59 historical Git blob comparator, with immutable original O47 Builder fixture, execute against the real O63 product in both shallow and full Git histories on all three installed platforms, while O60 and O63 tests still pass?**

## Prediction and controls
- Transplant O62's exact O59 test source **unmodified** Git blob `20faf26980693342439c7730f62bd0bab8daca0f`, and full untouched historical O47 Builder fixture Git blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`. Do not approximate or rewrite history. O50's original 3 assertions remain identical.
- Five hosted jobs: Ubuntu full + shallow, macOS shallow, Windows full + shallow. Genuine `pip install .` of O63, imported Builder/Codec/Reader outside checkout. Exact HEAD and product/test/fixture blobs asserted. Full-depth jobs must execute actual immutable Git parent; shallow jobs must use the Git-verified frozen original fixture. No skipping result-bearing tests.
- Run O59 original historical tests (3; one POSIX-only FIFO skip on Windows), O60 inherited real mutation product court (12), O63 genuine rollback/opaque result court (7). Require **22 JUnit cases per job**, zero failures/errors and exactly one justified Windows skip (zero elsewhere), with source custody route in actual logs. Preserve raw JUnit/logs even on failure.
- If bytes differ on same stable source from original O47, historical source hash differs, the composed candidate changes the O63/O60 result, a non-OS skip occurs, installed source identity is wrong, or any matrix job cannot obtain result-bearing evidence, **O66 FAIL**.
- Explicitly check that the fixture is *actually* exact O47 bytes, not code regenerated from memory; never use a fake mock as parent.
- Generic inherited four v0.30 fingerprint/surface tests may remain RED; do not change their assertions or hide the official failure. Official r24/ZIP performance is unmeasured until its **effective** job runs, not merely administrative success.

## Alternatives / BONK
- Simply declare parent failures infrastructure: insufficient, no actual proof on O63.
- Force full git history in generic CI: expensive, resolves one environment without making shallow evidence valid.
- Relax or remove historical tests: disallowed.
- Copy exact source-bound O59/O62 mechanism into O63 child; verify strong original byte comparator and O63 functionality together: cheapest discriminatory experiment and no production-byte cost.
- Direct O63-vs-O60 full archive parity is already proved in PR #418's targeted positive/negative control; do not claim new general compression benefit from this court.

## Scope, cost, follow-up
- New work is CI/evidence-only, not code-format change. Fixture adds ~22 KiB to test tree, not archive product. Test runtime includes genuine Builder/Reader, but no new whole-product CPU/wall/RSS or size/performance claims.
- A successful O66 reduces the three shallow-parent custody failures for **this child branch** only; does not erase other four generic inherited reds, certify a release, or grant transfer of evidence to different HEADs.
- Historical results must be append-only and link authentic hosted run ID, exact SHA, actual job state, JUnit and provenance. No modifications to `docs/discovery/STATE.json` absent decision-changing shared frontier truth. No merge/release.
