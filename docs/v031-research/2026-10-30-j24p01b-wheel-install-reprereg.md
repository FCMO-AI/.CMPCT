# J24P01b — wheel-install native loader custody (prospective)

UTC date: 2026-10-30. Starting exact PR #843 head: `6d2dfa4f0f709352e7090dd937a5779d831fc8c9`.
Main v0.30.0/r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`.
The source-exact Ubuntu/macOS/Windows *editable* installation test already passed 16/16 selection adversaries, one native candidate per installation, native Zstd roundtrip and synthetic duplicate rejection (Actions #41091634147). This does not prove wheel installation, despite an identical setuptools-rust `NoBinding` target.

## Distinct question and prediction (frozen before wheel code)

On a clean venv installed from the actual candidate wheel (not `pip install -e`), are there exactly one package-local `cmpct_core*` candidate, one direct regular native file, successful full import and native roundtrip, and pre-CDLL refusal after adding an inert second match? Repeat on Ubuntu 24.04, macOS 14 and Windows 2022 with exact PR HEAD. Both before and after a force-reinstall of that exact same wheel must pass. Prediction: 3/3 hosts for both stages, the same-package version reinstall creates no stale second native file, and the release binary loader behavior matches editable installation.

## Stronger controls and disproof

- Use a fresh venv with isolated site-packages, not an editable path; inspect `native_codec.__file__` and assert it is inside the venv, not the source tree.
- Actually build the distribution with the committed PEP 517 backend. Test before and after a standard wheel reinstall.
- Existing editable-only suite and fake-CDLL tests are inherited controls, not substitutes.
- Any legitimate wheel containing >1 matching native object, symlink-only packaging, failure to import or roundtrip, acceptance of a second candidate, failure to detect source-head drift, or artifact identity ambiguity defeats this candidate on the affected platform.
- Do not change primary selector semantics or make a timing/release claim from a wheel-specific test.

## Bounds, concurrency and negative scope

Only PR #843's existing evidence/tool/workflow files may change. No new shipping source edits, format/ABI/version, ZIP gate, core benchmark, frozen corpus or evaluator changes. Create a second exact-head portable CI receipt and preserve failures. A same-wheel force-reinstall is **not** a cross-version/cross-Python upgrade test. One-current-candidate evidence does not prevent malicious concurrent pathname swaps (known TOCTOU) or attest previous benchmark subprocesses. Work directly in this owner branch; do not alter #841's mapped inode or #574's shared discovery state.

## Decision after evidence

If all three wheel implementations pass, narrow #840's ordinary *fresh/reinstalled wheel* reachability but preserve conditional risk for hostile or interrupted installs; keep PR #843 draft until general product tests and Engineering Evidence are properly reconciled. If any host fails, keep source existing and choose packaging-semantic repair/fallback rather than weaken cardinality. Product/release credit zero.
