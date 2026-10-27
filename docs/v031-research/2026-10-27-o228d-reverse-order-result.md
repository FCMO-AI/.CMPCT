# O228d result — reverse-order exact archive reproduction

**2026-10-27 UTC | research only | prospective test passed.** Previous O228c optional-native Builder experiment built fixed fallback **before** native CDC in the same Python process. To falsify a hidden global-state/order explanation for the enormous opposite-signed size effects, [O228d preregistration](2026-10-27-o228d-mode-order-replication-prereg.md) was committed first at `c001546b3bffecc1875f0720c2760b99f258471b`, before source instrument `b89497b05db7023134a892dcd40a24e07494f845` and CI workflow.

## Exact evidence

[GitHub Actions #40536440994](https://github.com/FCMO-AI/.CMPCT/actions/runs/40536440994) **SUCCESS**; hosted [artifact #12747399329](https://github.com/FCMO-AI/.CMPCT/actions/runs/40536440994/artifacts/12747399329). The actual tested PR merge ref is `ab190554f9bb07890d37470fa2ca2bcb00df93e7`; source branch was `3b0d34d67086a75fe85b746ad7a439180e63394a`. Original 2,393-byte artifact ZIP SHA-256 `d1002a2dabef509471710675ccca35ad5920b5bcc72548ad9fcfe682cee0b05f`, raw result SHA-256 `d16d47f6592e333876074cb022d1fd58da9a4e564fcc64562b627f057e59b84e`. ZIP member CRCs and embedded checksums passed independent local inspection.

The scientific source was compiled from the **same unchanged canonical** `native/cmpct_cdc.c` and loaded before importing the genuine Builder. In two fresh profile processes, source order was **native first, fallback second**; each source generated the same logical SHA and passed real archive `verify/read/read_range`.

| Deterministic source | Mode | Original O228c expected SHA-256 | O228d independently reconstructed SHA-256 | Full archive bytes |
|---|---|---|---|---:|
| One-period | Native first | `318c46031e40e15efdf7d1e6d2dadfb6adb114d8f33a4a867ebad3ff39c32176` | **EXACT MATCH** | 2,098,336 |
| One-period | Fallback second | `b012bbd91aac855220de3f660c2e8db1f5c84a0d86d138d4eb122baf906c2ff0` | **EXACT MATCH** | 1,049,818 |
| Shifted | Native first | `31d9fe554419ac69e544448fabd597f4e4faf61efeac4358bea8434c6f5bf03a` | **EXACT MATCH** | 2,084,044 |
| Shifted | Fallback second | `3b0199feee2e84f7298a45ddb9d6873fc1fde680645d063b08085117b0cf01aa` | **EXACT MATCH** | 16,782,978 |

**Decision:** `REPLICATED_ORDER_INDEPENDENCE` — all **4/4 exact complete archive SHA-256** outcomes persisted under the reversed execution order with authentic source and unchanged settings.

## Truth boundary and causal interpretation

This eliminates the proposed narrow **same-process construction-order/global-state** alternative for these two sources under the same Linux/Python/toolchain regime. It **does not** establish native cross-platform portability, unrelated workload generality, release-safe CDC extreme-boundary behavior (see #606), or a generic per-file chunker-selection policy. One-period remains a native CDC ~2x regression; shifted remains a native CDC ~8x byte advantage. These are **actual complete archives**, not compressed-index proxies, but still research environment with optional helper and selected synthetic sources.

The O228c *virtual-run* decision remains `NO_NATIVE_BUILDER_TRANSFER_AT_16MIB` and no virtual on-disk tag is accepted. The scientifically live next question is an admission/physical-ownership model that can predict the chunker crossover without paying twice to build the whole archive, and without compromising exact reconstructability. Until such evidence exists, no unconditional native/fallback policy change is justified. Existing Reader/extraction/release owners and Discovery STATE are unchanged.

**No product-code change · no release · no merge · PR #600 stays DRAFT.**