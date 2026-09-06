# ONE-G0.2 simple-relation linear phase attribution — result

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Exact evidence

- source/head: `3d801313803aa8c890a09cd6dd440a9d4e95da43`
- workflow: `ONE-G0.2 simple relation linear phase attribution`
- run: `34052833203`
- job: `101539386114`
- artifact: `9995080287`
- artifact digest: `sha256:f4076491e6871bbd4b7fa863846469ac4e1ffef4d8cc9b4bf66e54772a3fb3b0`
- rounds per isolated/full timing: `63`
- CI: install PASS, `tests/one` PASS, attribution PASS, evidence upload PASS
- semantic failures: **0**

## Frozen simple-shift attribution

The profiler timed the exact ref-fused shared-native candidate as an uninstrumented full path and independently timed the four broad charged phases. Isolated shares are diagnostic and are not forced to sum to one because cache/call boundaries differ.

For mature `shift_plus1`:

| bytes | full ns | root SHA + digest prep | admission/proof | native segmentation | native writer/output |
|---:|---:|---:|---:|---:|---:|
| 16,384 | 46,918 | 48.81% | 7.09% | 25.63% | 14.03% |
| 32,768 | 79,188 | 54.68% | 4.98% | 27.95% | 9.19% |
| 65,536 | 146,594 | 57.39% | 3.69% | 28.88% | 6.27% |
| 131,072 | 276,056 | 60.08% | 3.14% | 29.99% | 5.07% |
| 262,144 | 551,411 | 59.94% | 3.39% | 29.85% | 5.04% |

Frozen median shares:

- root SHA-256 + current digest preparation: **57.3946%**; >=15% on **5/5** rows;
- native segmentation: **28.8818%**; >=15% on **5/5** rows;
- native writer/output: **6.2738%**; >=15% on **0/5** rows;
- admission/proof: **3.6905%**; >=15% on **0/5** rows.

Decision: **`attack_largest_credible_linear_owner`**, ranked `root_hash_prepare` first and `native_segmentation` second.

## Interpretation

This explains why both the original shared-native transfer and final-ref fusion retain dramatic segment-rich wins yet approach parity on large two-segment relations. The final native writer is not the broad owner in that regime. Root integrity work plus segmentation together account for roughly 86% of the isolated/full ratio at the median simple-shift size.

The root hash obligation cannot be deleted or weakened: canonical roots still require exact SHA-256. The exploitable structure is instead that `previous` and `current` hashes are independent and therefore may be computed concurrently or through a multi-buffer implementation while preserving exactly the same root identities. Any such experiment must charge synchronization/executor cost and preserve exact raw SHA-256 bytes.

If hash concurrency is not economical at 16–256 KiB, retire it and attack the second owner: fuse/eliminate segmentation passes without altering Segment/Law semantics. Do not move root hashing outside the charged boundary simply to manufacture a win.

## Claim boundary

Diagnostic adjacent-version writer attribution only. No stored-byte, product, RSS/native peak, authenticated placement, v0.29/v0.30 or 15-workload Genesis authority.