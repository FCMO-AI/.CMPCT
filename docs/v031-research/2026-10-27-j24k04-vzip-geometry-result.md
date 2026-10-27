# J24K04 — Signed virtual ZIP geometry: 3-host observed result

**2026-10-27 UTC.** Preregistration: `1f09a416af80aacbd8a1ee5136b2a6c9fe724c1c` predates test and workflow. PR #622 (draft research); Issue #623 (confirmed signed short-range defect). Published base `80c358f8824ec1b20d349c92ed94c898090969b0` / v0.30.0 / r24 is unchanged.

## Primary question and decision

Can fully reauthenticated S_VZIP metadata claim one more logical byte than physically reconstructed, pass strict preflight and silently deliver zero bytes for a valid-looking one-byte selected request?

**YES** in both independent frozen golden representations on three hosted operating systems; result is decision-changing scientific evidence, not a product correction.

The original independent immutable golden vectors are:
- `tests/conformance/v24-virtual-zip.json`: ZIP_STORED, 39 + 12 + 77 = **128** physical logical bytes, original archive SHA-256 `bed3a5d3bf3987f4c123e782effe9cc21a5d7253a9b2eca8a9af7b2522f4d839`.
- `tests/conformance/v24-virtual-zip-deflate-mode1.json`: retained exact Deflate stream, 39 + 14 + 77 = **130** bytes, original archive SHA-256 `842896d0140844841e02b2c882ca4f81efda16771caacea6248787fe98273573`.

For each, only the recipe `total` and the owning file row `logical_size` changed by +1 (129 or 131), and both index copies and footer were reauthenticated; the original stored physical bytes were preserved SHA-exact.

## Source-exact court

[Hosted GitHub Actions run #40588380742](https://github.com/FCMO-AI/.CMPCT/actions/runs/40588380742): exact HEAD `a81cab21ba6929883870fb1a8bc4400bcd8f2eb4`.

| Runner | Immutable control | Signed invalid stored (129/128) | Signed invalid Deflate (131/130) | Status |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 | exact SHA + ZIP + verify + range | preflight ACCEPT; full read REJECT; selected 1-byte request returns b'' | same | SUCCESS, 2/2 |
| macOS 14 | exact SHA + ZIP + verify + range | same | same | SUCCESS, 2/2 |
| Windows Server 2022 | exact SHA + ZIP + verify + range | same | same | SUCCESS, 2/2 |

Strong cross-host equality: original archive hashes, mutated archive hashes, original/mutant signed index SHA-256, unchanged physical blob SHA-256, reader operation decisions and returned bytes were identical across all three hosts. All six receipt rows indicate **preflight=ACCEPT**, **full_read=REJECT:OSError**, **selective=ACCEPT:** (empty hexadecimal), **returned_bytes=0**.

Original (fully reconstructed) content is an independently parseable exact nested ZIP; a request for one byte immediately *after* its actual end is rejected by the **unmodified** original golden. The modified signed metadata changes only the accepted range boundary, not the bytes. There is no proof of reading data external to the archive.

Raw hosted artifacts:
- [Ubuntu #12772812510](https://github.com/FCMO-AI/.CMPCT/actions/runs/40588380742/artifacts/12772812510); ZIP SHA256 `12f5af75a6dc5257b5099dec0a5533497fa16efce137cffc7cb536aa9f8e9c42`.
- [macOS #12772902383](https://github.com/FCMO-AI/.CMPCT/actions/runs/40588380742/artifacts/12772902383); ZIP SHA256 `b8bdb6057898acd7e8ac84b2dea0b2cc84dd2c4acdcbe22aa56a84059608d9d9`.
- [Windows #12772772717](https://github.com/FCMO-AI/.CMPCT/actions/runs/40588380742/artifacts/12772772717); ZIP SHA256 `108bea2db02b206cedc841b920282b6792c0e9ad4216830aa4e7eaf6cdd619dc`.

The v1 court did not separately execute `verify()` *on the signed mutant*; the prereg predicted it would reject based on `verify` invoking `read`. This additional direct check was added prospectively as a strengthening test at code commit `83d21ca4a2c7a14b343b9af86e58a5627d864a6e`; **requires fresh exact-head hosted evidence**. Do not mislabel the earlier run as proving that unmeasured check.

## Causal localization and stronger independent implementation control

Released Python `src/cmpct/validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`: `_validate_recipe` checks shapes and types, and `_validate_storage` checks `row.size == recipe.total`, but no enforced equality to physically projectable bytes. `src/cmpct/codec.py::range_vzip` projects Python slices with that overpromised size, returning fewer bytes without error. Ordinary `CMPCT.read` independently checks reconstructed length and refuses the mutation.

Independent Rust native `native/cmpct-core/src/vzip.rs` blob `8996112d923df552a817ba85210c4d49d60e229f` already enforces:
- `sum(literal_lengths) == skeleton physical blob usize`;
- `sum(literal_lengths) + sum(stream compressed lengths) == file logical size`.

This is an **existing stronger native static control**, not a hosted execution of the identical mutant against Rust ABI. Reuse the shared invariant rather than inventing new parsing law. The result is a Python/native admission divergence in source logic, not yet a measured Python/native cross-runtime case.

## Strongest negative, counterfactual and safety

Source-static accounting would have caught the oversize mismatch earlier for much less cost; it was prospectively recognizable from schema and the native cross-reference. However static alone would not establish that the actual installed Python Reader returns empty bytes rather than a typed error across host operating systems. The tiny fixed golden plus full index reauthentication was the cheaper decisive runtime rung; no large Builder test or performance matrix was needed.

No new format, release threshold, evaluator change, benchmark win, archive exfiltration, CPU/RSS gain or proof of all VZIP mode behavior is claimed. Independent archival-wire referee outside the test, native mutant ABI test, mode-0/mode-2 coverage, arbitrary hostile combinations, and composed Reader integration remain open. Initial CI topology / Engineering Evidence aggregate SUCCESS is administrative unless its individual measured tasks actually ran.

## Next executable and owner handoff

**Priority:** strengthen strict preflight *and ordinary Reader admission/range* with physical/projected geometry equality under overflow/resource bounds. Check per-mode actual compressed stream length, zero-length and boundary requests, and native Rust parity. Reader composition owner: PR #569; VZIP SHA owners #436/#443. This scientific branch must not overwrite that owner. Source-locked product correction, full inherited controls, CPU/RSS/open performance and release parity remain mandatory.

Discovery Engine state shared with #574 remained untouched; no repeated evidence to modify its policy. Collision search found no same narrow VZIP geometry implementation; neighboring Deflate and VZIP hash work is distinct.
