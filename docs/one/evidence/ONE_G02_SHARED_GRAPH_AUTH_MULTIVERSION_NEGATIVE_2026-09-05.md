# ONE-G0.2 shared stored-graph authentication — multi-version transfer

**Experimental line:** `ONE-G0.2`  
**Result-bearing source:** `7c7902a461d6c623fff34a46669de5150627abea`  
**Workflow:** `33952503909` (manual rerun after an earlier concurrency cancellation)  
**Result-bearing job:** `101270050294`  
**Artifact:** `9965325117`  
**Artifact digest:** `sha256:b694ac77a61ea0aba231f552f6ea1217de0a9b353c7b5c52ed1f29dd0d959ee4`  
**Decision:** `complete_manifest_addressability_blocks_multiversion_transfer`

## Question

The edited-pair experiment established that authenticating one stored basis and reconstructing a second root through Law + Surprise can preserve full SHA-256 integrity, beat two literal roots in complete bytes, and keep 4 KiB authenticated reads bounded. This transfer asked whether the same representation survives as one basis serves 1, 2, 4 and 8 independently edited children.

The representation was deliberately simple: the graph manifest contains one fixed 72-byte descriptor per derived version, and the reader authenticates/reads the **entire manifest** before selecting the target version. That makes manifest addressability a falsifiable cost owner rather than silently gifting control metadata.

Frozen corpus:

- 64 KiB and 256 KiB roots;
- four independent bases per size;
- derived mutation counts 1, 2, 4, 8, 16, 32, 48 and 64;
- family prefixes of 1, 2, 4 and 8 derived versions;
- leaf grid 32, 48, 64, 80, 96, 112, 128, 160 and 192 bytes;
- every byte alignment modulo the basis leaf;
- complete persisted representation strictly below an unauthenticated independent-literal family;
- median authenticated 4 KiB traffic <=1.20x on every target row;
- exact reconstruction required everywhere.

## Result

All result rows reconstructed exactly: **zero semantic failures**. No leaf size passed the full transfer gate.

The failure is not density. Law sharing becomes increasingly favorable as the family grows. For example, the 112-byte basis leaf has a worst complete-family fraction of **78.8124%** of independent literals across all tested prefixes, and the 192-byte point reaches **66.8495%**. The failure is selective control traffic.

At eight derived versions the complete manifest reaches **632 bytes**, and because the simple reader consumes all 632 bytes for every 4 KiB request, the previously viable pair locality is lost:

| Basis leaf | Worst complete-family fraction | Worst row median authenticated touch | Eight-version manifest |
|---:|---:|---:|---:|
| 48 B | 116.8739% | 1.279785x | 632 B |
| 80 B | 90.1894% | 1.279785x | 632 B |
| 96 B | 83.5243% | 1.295410x | 632 B |
| **112 B** | **78.8124%** | **1.311035x** | **632 B** |
| 192 B | **66.8495%** | **1.295410x** | **632 B** |

The pair result therefore transfers in density but not in selective-read control locality.

## Causal interpretation

This is a useful scoped negative because it isolates the next representation debt. The authenticated basis is not the new owner: the same basis geometry already passed for a pair. The derived Surprise payloads are small and target-specific. The new cost grows with **unrelated version descriptors that the reader is forced to read even though the requested target needs only one descriptor**.

The correct Builder is not to coarsen basis leaves and sacrifice the pair gain. It is to make generic graph control selectively addressable and authenticated: authenticate a small graph header plus the requested Law/Surprise descriptor and a proof for that descriptor, while charging all descriptor-tree bytes and proof traffic.

This remains ONE-native. A selectively authenticated descriptor is generic Law/Surprise control, not a temporal codec opcode.

## Scoped negative constraint

Do not promote a complete-manifest-on-every-read design for growing ONE graphs. Do not reopen it by raising the 1.20x access target or by omitting unrelated descriptor bytes. Reopening requires a control representation whose authenticated read work grows with the requested reconstruction cone rather than total graph width.

## Claim boundary

This result compares against independent literal families only, not frozen v0.29 or deferred v0.30. It changes no canonical wire, product access guarantee, or release authority.
