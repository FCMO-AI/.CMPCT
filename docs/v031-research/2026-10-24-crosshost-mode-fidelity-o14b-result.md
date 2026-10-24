# O14b result — fixed-mode byte equality exports permission loss

Date: 2026-10-24  
Classification: **NEGATIVE PRODUCTIZATION / POSITIVE SCIENTIFIC DISPROOF**

## Authority and prospective controls
Preregistered before implementation at `4f21f554d2b875ff75d2793596e38dee82d692d3`. Experiment `benchmarks/v031_mode_fidelity_o14b.py` was committed later at `3b3eca36b5da689d0e75d3c7eb19b2cfa09bca24` and hosted with the unchanged PR #352 installed Builder and Reader at HEAD `efb4700005cd212b02725a4bcc7ef93a89785eb9`.

Authoritative hosted court: [40119698872](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119698872), independent `fidelity-hostile` Ubuntu job ID `120948404453` **SUCCESS**. Raw original evidence: [artifact 12569948852](https://github.com/FCMO-AI/.CMPCT/actions/runs/40119698872/artifacts/12569948852).

Each fixture file was explicitly created and `chmod` verified on the host before building. Every arm uses authentic installed `Builder(reproducible=True)`, real `CMPCT.verify()`, individual `CMPCT.read()`, and `CMPCT.extractall(metadata=True)`. All member bytes are exact. Three arms: (1) shipping Builder untouched, (2) O14 fixed `0644` regular-file modes, (3) `mode & ~022` mask preserving some mode distinctions but removing group/other write.

## Observed archived AND extracted modes, Ubuntu 24.04

| Source file | Verified source | Original Builder | Fixed 0644 research mode | Mask group/other write |
|---|---:|---:|---:|---:|
| `run.sh` executable | `0755` | **`0755`** | **`0644`** (lost executable bit) | `0755` |
| `locked.dat` read-only | `0444` | **`0444`** | **`0644`** (adds write permission) | `0444` |
| `shared.log` group/other writable | `0666` | **`0666`** | **`0644`** | **`0644`** (loses group/other write) |

The fixed-mode arm changes the meaning of three distinct source permission profiles while preserving all content bytes. The simpler mask-only alternative reduces but does not eliminate metadata loss. The genuine original Builder preserves the tested source mode contract.

Hosted decision: `SILENT_PORTABLE_MODE_PROFILES_FALSIFIED_FOR_FULL_POSIX_FIDELITY`.

## Exact abstract bound (no platform-specific statistics needed)
Let `X_1` and `X_2` be distinct logical filesystem trees with identical content but **different mode metadata that the archive contract promises to reconstruct exactly**. Let `E` be deterministic archive creation and `D` exact reconstruction. Assume `D(E(X_i))=X_i` for both trees. If one additionally demands `E(X_1)=E(X_2)` (same complete bytes), applying `D` yields `X_1=X_2`, contradiction.

Therefore *byte-identical archives for different source metadata and exact preservation of those metadata values cannot both be required under a deterministic lossless contract*. This is not a crypto lower bound or a claim that unrelated filesystem metadata representations are identical. It identifies the missing equivalence decision: what does an opt-in reproducible or portable filesystem profile intentionally normalize versus preserve? O14 establishes a particular Windows/POSIX mode mismatch; O14b prices its semantic consequence.

## Scientific decision and generality limit
- O14 original sample root cause: **source mode field**, established through authentic whole-archive SHA convergence under a mode-only oracle on Ubuntu/macOS/Windows. Original negative persists, see `2026-10-24-crosshost-mode-equivalence-o14-result.md`.
- O14b: **silent fixed mode or write-bit masking is NOT fully metadata-lossless** for the held-out POSIX files. Both candidate families are retired as silent replacements for the current archive contract; they may be considered only as explicitly lossy *metadata profiles* with user consent, not as improved general-purpose exact archive representations.
- Content byte losslessness is maintained in every tested arm; the negative is filesystem permissions. This is a real cost and must not be misreported as encoder failure.
- The hosted proof applies to explicitly chmod-able Ubuntu POSIX source and successful metadata-restoring extraction. Other mode/ACL/identity/symlink/read-only Windows cases remain untested.
- No performance, compressed-byte superiority, release authority or format change earned.

## Counterfactual / cheapest next action
The abstract injectivity proof could have rejected **silent** mode normalization as a product design *before* any expensive suite. The hosted held-out test complements it by showing that real CMPCT extraction indeed restores the divergent modes rather than merely displaying them in an index. A future truly portable-build profile must document which user-visible semantics may be discarded; compare it only against a control with the same explicitly chosen semantics and test executable/read-only/cross-OS behavior. Given this disproval, stop threshold-gardening on this mode family and return to Reader/safety and general representation/product debt owned in other PRs.

## Concurrency / engineering law
Same O14 isolated branch, distinct prereg+tool+artifact. Original #352 branch/installed package smoke untouched; no shared discovery cache mutation; parent r24 and released v0.30 remain unchanged. Open PR stays DRAFT. No merge, no release.
