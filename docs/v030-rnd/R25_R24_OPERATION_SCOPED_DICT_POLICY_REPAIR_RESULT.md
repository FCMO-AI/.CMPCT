# r24 operation-scoped dictionary-policy repair — result

Status: **REPAIR CAUSALLY VALID / FORGE-CUSTODY / NO RELEASE CREDIT**

This record preserves the exact result of the frozen repair contract in `R25_R24_OPERATION_SCOPED_DICT_POLICY_REPAIR_PREREG.md`. It promotes the implementation only to the next product/runtime authorities; it does not unlock v0.30.

## Authority

- branch: `agent/v030-authoritative-integration`
- exact source: `b1b5e78c9f0a3624b7847b6c2c6d270db485128d`
- workflow: `CMPCT v0.30 r24 operation-scoped dictionary-policy repair`
- workflow run: `33635640059`
- substantive job: `100268002109` (`exact-repair`)
- artifact: `v030-r24-operation-scoped-dict-policy-repair-b1b5e78c9f0a3624b7847b6c2c6d270db485128d`
- artifact id: `9849007106`
- artifact digest: `sha256:cb13256db6720e457fc0ff28a2752a09429e6aed4c33fa0c94eed7b256c339e5`
- schema: `cmpct-v030-r24-operation-scoped-dict-policy-repair-v1`
- runner: Ubuntu 24.04.4 / Python 3.11.16
- release credit: false

Frozen terminal decision: **`REPAIR_CAUSALLY_VALID`**.

## Exact Shifted worker-determinism result

Target: `resemblance_hostile_v1 / 01_shifted_versions`.

| repaired arm | workers | dictionary state | complete archive | archive SHA-256 | logical tree |
|---|---:|---|---:|---|---|
| normal release r24 | 4 | `dictionary-live` | **29,883,732 B** | `5c3ba63f7c185911aa3877a24e8c086f87c85f2baa41932b73df7989b1ad878f` | `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16` |
| one-worker release r24 | 1 | `dictionary-live` | **29,883,732 B** | `5c3ba63f7c185911aa3877a24e8c086f87c85f2baa41932b73df7989b1ad878f` | `a42fb1e70517025f0ad0bf2e76ea01963e0e6c14a7308e4243c5fbc9ce7b7d16` |

Stable build statistics were exact between worker counts; only the intentionally diagnostic `encode_workers` and measured `create_s` fields differ. Both archives strongly verified all 18 user files.

The repaired four-worker build therefore restores the Builder's intended worker-count determinism while retaining parallel encoding. It also reproduces the exact smaller representation discovered by the accepted worker-policy causal experiment: the trained dictionary remains live instead of becoming invisible after thread dispatch.

For context, the immediately preceding inherited four-worker behavior on the same deterministic Shifted regime stored about **30.276 MB** and reported `dictionary-dead`; the causal v2 experiment measured the policy-correct answer as **391,869 B smaller**, with a substantial standalone RSS reduction but explicit create-time debt. This repair result does not re-measure or waive that runtime debt.

## Historical negative control

The ordinary historical Builder remained exactly unchanged when the new operation-scoped transport hook was present versus when its two Builder methods were restored to their original implementations:

- complete archive: **9,583 B** in both arms;
- SHA-256: `cf3d5241f5e0b133b1f145a3dda7c3f675bf45fbed20f9ddb24f76a4330e2300` in both arms;
- logical tree: `0c2310bb53a386cd5c4ae8077d994f1bef40a273c3446fb8b3bbfbdb59fe754b` in both arms;
- stable build statistics: exact;
- 24/24 files strongly verified in both arms.

This passes the frozen `historical_repaired_equals_unpatched` requirement. The repair is therefore policy transport, not a new global `.bin` classification rule and not a historical-format rewrite.

## Causal interpretation

The predecessor experiment proved that the release `.bin` dictionary policy was selected in the parent build thread but lost when `_encode_candidate()` crossed into worker threads because the predicate lived in `threading.local()` state. The production repair captures the exact dictionary-eligible content hashes immediately after training, still in the policy-owning thread, and lets workers consume that immutable operation-scoped fact.

The repair does **not** mutate process-global `TEXT_EXT`, does not alter the shared Candidate, does not reduce worker count and does not change reader-visible grammar. A private encoder-only Candidate view supplies an already-existing stable text hint only when the parent thread had previously marked that content hash dictionary-eligible and the worker cannot observe the same dynamic predicate. Hints are encoder evidence and are not serialized.

The hostile historical control demonstrates that this hook is inert outside the release-owned dynamic policy.

## Strongest surviving critique

Causal correctness and deterministic bytes are now established, but product performance is not. The predecessor v2 diagnostic measured the intended dictionary work as slower than the buggy four-worker path. A faster implementation may therefore still be needed; the repository may not preserve the old larger bytes merely because the bug skipped work cheaply.

Likewise, the measured standalone r24 memory improvement does not automatically translate one-for-one into complete r25 product RSS because r24 and r25 construction overlap and other product allocations remain live. Only the normal exact product/runtime authority can price that exported debt.

## Forge decision

**Advance the repaired operation-scoped worker-policy transport to ordinary product/runtime/release evaluation.**

Do not tune the repair by weakening dictionary eligibility, locality, complete-byte accounting, recovery, integrity or runtime thresholds. If full product create time remains red, rehabilitate the intended dictionary path itself (for example by removing redundant compression work or improving dictionary-candidate execution) while preserving the now-proven worker-count byte identity.

## Release state

No release credit is granted by this diagnostic. The exact-source final-release workflow on the repair fingerprint is classifier-only: `contracts`, `compression-and-product-parity`, `external-frontier`, and `runtime-and-selective-read` were skipped. Full Python/native/platform/product/runtime authorities must be regenerated and accepted before v0.30 can unlock.
