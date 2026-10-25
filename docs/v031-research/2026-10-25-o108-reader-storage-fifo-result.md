# O108 — Exact Reader storage-mode FIFO destination differential: HOSTED RESULT

Date: 2026-10-25 UTC. **Status: SCIENTIFIC DECISION COMPLETE (Linux only); PRODUCT REPAIR NOT IMPLEMENTED.**

## Authority, frozen hypothesis, and source identity

- Canonical v0.31 development ancestor: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Released product v0.30.0, physical archive revision 24, neither modified here.
- Original exact Python Reader Git blob: `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Original exact Builder Git blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Immutable prospective scientific claim committed **before test/observation** at `fcba42de69b191a11f968e92ff3770f48efbf787`; see [preregistration](2026-10-25-o108-reader-storage-fifo-prereg.md).
- Result-bearing branch HEAD: `214094d3627f3a289c22211e2379e56e7a588c58`; science instrument Git blob `0505587b8a3623c3032ca326d50a5e21f82cf15c`.
- This is a separate physical representation question from the already proven O106 `S_BLOB` defect, [PR #461](https://github.com/FCMO-AI/.CMPCT/pull/461), [Issue #462](https://github.com/FCMO-AI/.CMPCT/issues/462). Reader destination implementation belongs to [PR #269](https://github.com/FCMO-AI/.CMPCT/pull/269).

## Hosted original product evidence (scientific court)

- [GitHub Actions run #40226200194](https://github.com/FCMO-AI/.CMPCT/actions/runs/40226200194), Ubuntu 24.04, Python 3.11, **completed SUCCESS: 12 PASS, 0 FAIL, 0 SKIP**, full run `32.77s`.
- Real `cmpct` Builder and Reader installed outside the repository checkout, source/installation SHA verified in workflow.
- [Raw artifact #12610624446](https://github.com/FCMO-AI/.CMPCT/actions/runs/40226200194/artifacts/12610624446); GitHub artifact ZIP digest `sha256:be996c40c5b9f2935ca1f4289fcc83ee13133930b077bb2522ead8071cefcbda`.
- Independent JUnit/JSON auditor asserts all 12 combinations ran; 4 expected true child timeouts; no hidden skip; exactly one physical archive SHA and source SHA within each storage class. `O108_CHILD_INDEX_OPENED` is present before every negative timeout.
- **Scientific test PASS on FIFO direct-open cases means product defect reproducible; it is NOT a repair, safety approval, or successful extraction.**

| Stored representation | Fresh regular output | Existing regular output | Existing FIFO without reader | Existing symlink to FIFO |
|---|---|---|---|---|
| **S_BLOB = 0**, 4,096 logical B | Exact 0.068689s | Exact 0.061380s | **Timeout 8.010692s** | **Timeout 8.011548s** |
| **S_CDC = 5**, 1,081,344 logical B | Exact 0.065597s | Exact 0.065339s | **Exact 0.067412s; FIFO replaced** | **Exact 0.068332s; symlink replaced, target FIFO intact** |
| **S_SPARSE = 3**, 6,291,456 logical B | Exact 0.076680s | Exact 0.065134s | **Timeout 8.010518s** | **Timeout 8.011285s** |

Each representation was genuinely produced by unmodified Builder, witnessed inside the installed Reader and verified with `read()` and `verify()` before the hostile output court; no synthetic index row was inserted. The sparse source has real sparse allocation (`st_blocks*512 < 0.75*logical size`) and Builder emitted `S_SPARSE`. All successful destinations reconstructed the exact original file. Timed-out children were killed; source, original archive SHA and FIFO objects remained unchanged. The symlink's external FIFO target remained intact in the CDC case.

### Exact archive/source identities (per storage class)

- BLOB archive SHA-256 `4e9092bb1971b518e63c8434ae1f98518a41ff8375dfa3fbba2c0144e3238f32`; source SHA-256 `55d5ade381779b31e43d8ec99fba06b76af1b9e1330427dd9f1ea40d07bf431d`.
- CDC archive SHA-256 `ed859a96267e7634b5c5565f1031fa2ceedd4831dbb0b8509eee7ab831ea7686`; source SHA-256 `94233111480609bfce291a2a7a755ea0c3d315bab10d774341613fd44eb48e23`.
- SPARSE archive SHA-256 `7fa334dc2fa689014fbc1f9e6a72fd35b3fdbcf6d1d88824fd9a77509784fe57`; source SHA-256 `c64a3e73bd5edc83219a75c2609a043db9eb67feff283fe05a8ae9d61e548e23`.

## Causal decision and strongest controls

**Primary prediction CONFIRMED in the tested Linux regime**: Reader direct-file output open is availability-unsafe on pre-existing FIFO in *two independent genuine storage classes*, `S_BLOB` and `S_SPARSE`. `S_CDC` has a different output ownership/publishing model, so the same leaf does not block; it is **replaced with a verified regular file**. The simple alternative explanation “Reader startup or decompression exceeded eight seconds” is rejected within these fixtures by matched fresh/regular controls completing at approximately 0.06–0.08 seconds and the child's opened-index receipt before the stall.

This is a representation-sensitive **filesystem output semantic divergence**, not a representation compression gain and not an on-disk format defect. Neither an S_BLOB-only patch nor a sparse-only fix would close the full direct-open exposure. The separate S_CHUNKS path uses the same staging helper as CDC but was not separately run with a genuine S_CHUNKS Builder product archive. Do not award S_CHUNKS hostile evidence.

## Falsification scope, limitations, and product debt

- The observed >8s children prove a bounded availability defect under unconnected POSIX FIFO conditions; not mathematical infinite blocking, not network/remote exploit, not Windows named-pipe or macOS sparse proof.
- A FIFO may be replaced by the CDC staging path; this is not necessarily an acceptable general inode/metadata/hardlink policy. Existing direct-write regular-file reuse preserves inode; staging does not necessarily. Do not blanket-replace all outputs with `os.replace` as if semantically neutral.
- An early pathname `lstat` type check before output opening may stop a static FIFO but does **not** solve a concurrent swap between check and open, as documented by Reader destination security owners.
- No impact on actual archive storage bytes versus release base, fresh-process startup, decode throughput, cold selected read, CPU/RSS, temporary I/O, native Reader, full portability or full parity benchmark has been measured. Child times are narrow controls, not promotion economics.
- No canonical source, benchmark gate, release/format/version, Discovery policy/state, native ABI, other owner PR, or evaluator threshold was modified.

## Counterfactual search lesson and handoff

A single 3×4 instrument executing Builder-authentic representations on the same source and per-class same physical archive revealed the separation without implementing competing safety fixes, proving a strong discriminating control was cheaper than a generic Reader rewrite. **Prospectively reusable rule:** classify output publication by physical ownership path and test special existing leaves against *every distinct writing primitive* before calling a product-level availability fix complete. This is a local evidence-backed experimental lesson, not enough repeated evidence to rewrite the Discovery Engine's normative policy.

**Owner action** (PR #269, Issue #462): define and implement a storage-class-neutral fail-closed type policy for existing destination leaves, covering both direct `S_BLOB` and `S_SPARSE`, preserving normal files and intentional staged cases. Evaluate descriptor-bound and no-follow alternatives against TOCTOU, symlink, inode, hardlink, xattr, permission and parent-root constraints. The cheapest next decisive product court is original 12 O108 cases reused *unchanged* against the proposed Reader safety composition, with expected safe immediate refusal for nonregular leaves when stipulated by the new contract, rather than replacing a failing observation with a green timeout test. Match release-law full CI and official same-semantics ABBA before any promotion.

**Disposition:** O108 scientific question decision-complete on Linux; distinct macOS/Windows platform verification remains unmeasured. No product credit, no merge, no release.