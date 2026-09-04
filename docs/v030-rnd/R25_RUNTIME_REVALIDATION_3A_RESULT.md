# r25 fresh-process runtime revalidation — independent exact-candidate receipt

Status: **ACCEPTED D0-D3 REVALIDATION / RUNTIME RED REPRODUCED / NO RELEASE CREDIT**

Decision: `CURRENT_HEAD_RUNTIME_DEBT_REPRODUCED_ACROSS_FINGERPRINT`

This record preserves an independent fresh-process revalidation of the runtime debt already attributed in `R25_CURRENT_HEAD_RUNTIME_FORGE_RESULT.md`. It changes no product source, archive grammar, corpus, comparator, timing band, RSS band, locality rule, integrity/recovery condition or release law.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- measured source head: `3a205d4be3b6e9120583db47b6390fb1a3244454`
- measured candidate fingerprint: `10d6e0b63702c6df5f266f3d37a6138f8489b98d69f90913aef720b98eaca2b6`
- workflow: `CMPCT v0.30 authoritative v2`
- run: `33785950132`
- result-bearing runtime job: `100751647938`
- runtime artifact: `9906194622`
- release credit: **false** because the immutable fresh-process runtime bands fail

The measured product source predates later CI-custody-only workflow changes. Those later workflow changes intentionally move the strict release fingerprint, so this receipt does not grant current-head release credit. Its value is causal/reproducibility evidence for the Forge debt split.

## Exact measured rows

| workload | selected representation | v0.30 bytes | accepted v0.29 bytes | create ratio | verify ratio | extract ratio |
|---|---|---:|---:|---:|---:|---:|
| Shifted | PrefixGraph | 1,700,662 B | 1,723,056 B | **1.252428x** | 0.542836x | 0.922086x |
| Logs | logs-inverse | 3,550,342 B | 3,550,609 B | 0.008380x | 0.798960x | **1.316452x** |
| ML | G0-G4 overlay | 13,674,821 B | 13,836,439 B | **1.484204x** | **2.290311x** | **3.014910x** |

Frozen aggregate result:

- median workload create ratio: **1.252428x** — red versus the unchanged 1.10x median ceiling;
- maximum workload create ratio: **1.484204x** — red versus the unchanged 1.25x per-workload ceiling;
- median workload extract ratio: **1.316452x** — red versus the unchanged 1.10x median ceiling;
- maximum workload extract ratio: **3.014910x** — red versus the unchanged 1.25x per-workload ceiling;
- no representation-size regression in these three rows.

The same authority wave's child-aware memory companion remained green. Therefore this independent revalidation again isolates **latency**, not whole-process-tree RSS, as the current product blocker.

## Reproducibility interpretation

The earlier accepted Forge attribution on source `5a316cdc...` reported the same three semantic owners:

1. Shifted loses time after a winning PrefixGraph has already been materialized because the exact product still pays the losing G0-G4 audition;
2. Logs creates extremely quickly but inverse decode remains too slow;
3. ML preserves a real G0-G4 byte win while paying severe verify/extract and creation debt.

This independent run changes the magnitudes but not the owner ordering or the intervention choice. It therefore strengthens `CURRENT_HEAD_RUNTIME_DEBT_SPLIT_BY_OWNER` rather than reopening generic optimization.

## Forge decision

- **Shifted:** preserve PrefixGraph compression and process-lifetime memory gains. A legal shipping intervention must supply a sound candidate-specific stopping/admission bound or reduce the losing G0-G4 work; a heuristic skip is not admissible.
- **ML:** preserve the ~161.6 KiB complete-product saving while the frozen native-FFI/shared-record-cache experiment decides whether reader-side exported debt can be rehabilitated. Do not tune the byte win away to manufacture timing green.
- **Logs:** preserve the near-zero create debt and continue only causally distinct inverse-decode work. The historical whole-reader Rust FFI v1 result is separately preserved as a scoped negative; simple rewrapping is not a justified successor.

## Strongest self-critique

This receipt reproduces the problem; it does not solve it. Because later CI-custody changes are release-fingerprinted, a future shipping fix still needs a fresh same-fingerprint authoritative runtime receipt. The evidence here should be used to prevent strategy restart, not to claim current-head release authority.
