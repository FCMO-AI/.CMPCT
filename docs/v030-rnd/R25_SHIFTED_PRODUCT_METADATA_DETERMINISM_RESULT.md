# Shifted product-metadata determinism causal result

Status: **ACCEPTED SCOPED NEGATIVE / MTIME HYPOTHESIS NOT SUFFICIENT UNDER FROZEN DECISION / ZERO RELEASE CREDIT**

This result closes `R25_SHIFTED_PRODUCT_METADATA_DETERMINISM_PREREG.md` without changing its support rule after seeing the data.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `dc731d93604db8e96b5d3c38244b7d025c132234`
- workflow: `CMPCT v0.30 Shifted product metadata determinism`
- run: `33710958420`
- substantive job: `100510140030` (`causal-check`)
- artifact id: `9877028680`
- artifact: `v030-shifted-product-metadata-determinism-dc731d93604db8e96b5d3c38244b7d025c132234`
- artifact digest: `sha256:ccbdfe1f45564fe7224cdecd94adc555002cdfe572e9bbd58ed15dec82590224`
- schema: `cmpct-v030-shifted-product-metadata-determinism-v1`
- experiment valid: **true**
- release credit: **false**

All six independently generated Shifted corpora reproduced the accepted historical content identity `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd` and all selected products strongly verified to the same logical tree `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16`.

## Exact observations

### Fresh arm

The three fresh generations had three distinct metadata manifests and three distinct r24 product sizes:

- **29,883,724 B**
- **29,883,732 B**
- **29,883,726 B**

The selected PrefixGraph products also varied slightly, at **1,700,666 / 1,700,668 / 1,700,666 B**, with distinct archive SHA-256 values despite one accepted historical content identity and one logical verification tree.

### Fixed-mtime arm

The only intervention was setting atime/mtime on the workload root and descendants to `1767225600000000000` ns (2026-01-01T00:00:00Z). Historical content identity remained unchanged.

All three repetitions then produced exactly:

- one metadata manifest: `4b1a4f801c810d90dcb51f5d506483bc5c2c70d2d041524cda2caf3a6dda885e`
- r24 product: **29,883,488 B**
- selected PrefixGraph product: **1,700,594 B**
- selected archive SHA-256: `a86f23a106a91a85cc6f23f4eaeddd5240a12add7620d3c1ec0e759ef36934b0`
- logical tree: `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16`

## Frozen decision

**`SHIFTED_MTIME_METADATA_NOT_SUFFICIENT`**

The preregistered support rule also required more than one `product_tree_sha256` in the fresh arm. That condition did not occur: every repetition had the same logical product-tree hash. Therefore the hypothesis must be recorded as non-support under this frozen experiment even though normalizing mtime empirically collapsed both r24 and selected-product byte variation.

Do not rewrite the old rule or call this result `SUPPORTED` after observing that its product-tree criterion was stronger than necessary for archive-byte determinism.

## Causal interpretation

The result does establish two narrower facts worth carrying forward:

1. the current fresh Shifted fixture has cross-generation archive-byte nondeterminism while preserving accepted historical content and logical reconstruction identity;
2. fixed mtimes are associated with exact repeated r24 and r25 selected bytes under this regime.

It does **not** establish that mtime is the only serialized filesystem fact responsible for the drift, because the frozen experiment did not ratchet every filesystem metadata field that canonical r24 may serialize. A new causal question must therefore compare the complete serialized metadata projection, not weaken this result's decision rule.

## Forge consequence

The old PrefixGraph S6 receipt remains invalid and immutable. Do not supersede its product identity from this result alone. The next justified D2/Custody experiment is to prove whether independently generated Shifted trees differ only in filesystem fields actually serialized by canonical r24, and whether normalizing exactly those fields yields one stable metadata projection plus one stable r24 archive identity. Only that separately frozen causal evidence may justify a deterministic-metadata S6 supersession while preserving every original S6 performance, size, integrity and helper-lifecycle threshold.
