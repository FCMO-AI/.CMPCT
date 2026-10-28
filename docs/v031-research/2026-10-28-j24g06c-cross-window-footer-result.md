# J24G06c — Cross-window physically mutable footer result
**Date:** 2026-10-28 UTC. **Science only; no product/release/format mutation.**

## Grounded identity and controls

- PR: [#654](https://github.com/FCMO-AI/.CMPCT/pull/654), stacked on scientific #651 `2852dd2ebaa203a2b51b5afc92a7b050978d7b74`.
- Preregistered hypothesis commit (before research code) `24f43abe2dcf5a331a23fed3aa93469dd62f011f`.
- First result-bearing HEAD `ba3227908e11830333764b5085995bf540be5ab9`, hosted [Actions #40643918928](https://github.com/FCMO-AI/.CMPCT/actions/runs/40643918928), completed **SUCCESS** on Ubuntu 24.04, Python 3.11.
- Original Reader compiled from published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Candidate installed from same HEAD, Git blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`. Workflow verified installed file bytes and prerequisite Git ancestry.
- Artifact `12797380149`, artifact ZIP SHA-256 `5c1de85594f9d32f88fd3be515a58bbadb350f62f98603a2612f491f89f5ebb5`; contains `source.json`, `court.json`, and `court.log`. Raw court log includes all controls and both exact-source cases. No separate in-archive byte blobs were preserved, only SHA-256 and signed-FTR checks from the execution.
- Authentic Builder logical payload SHA-256 `e5f012a019b3ff6810235ee4c13425670701dcd9859005ecbe1fe811f0b8daef`. Builder source archive SHA-256 `a4ee2a0524f8ecec1a6528382c7b958d443fd8d1a30e2fa102dede9ff2477714`.

## Decisive observations

The original *adjacent-footer* control from #651 was replicated: a physical in-place A-footer rewrite happened and changed complete archive SHA, but both Readers selected original checkpoint **896** (depth 0), even though original history decoded A twice. The most plausible confound is the buffered file read retaining old footer bytes within one small scan block. This is a hypothesis supported by the next isolation, not an independent CPython implementation audit.

In both independently constructed 2 MiB and 3 MiB cases, A is at offset **977** and B is near the physical end (respectively **2097084** and **3145660**). In each unchanged/no-mutation control, both Readers select checkpoint **896** (depth 0) and return exact logical bytes, range and verification. The deterministic injection rewrites only A's same-inode FTR `prev` from zero to Builder checkpoint 896, preserving FTR payload SHA and file length; two Readers receive exactly matching resulting whole-archive SHA in each size.

| Physical archive | Historical Reader after mutation | Candidate Reader after mutation | Outcome |
|---|---|---|---|
| 2,097,152 bytes | Selects A=977, depth 1; 4 decodes | Selects checkpoint=896, depth 0; 3 decodes | **GENERATION_SELECTION_DIVERGENCE** |
| 3,145,728 bytes | Selects A=977, depth 1; 4 decodes | Selects checkpoint=896, depth 0; 3 decodes | **GENERATION_SELECTION_DIVERGENCE** |

Whole-archive SHA-256 before/after, 2MiB: `e144b509ff9c3f096cf221883b0417ba401527527bbeb6d2bc6390d6924397f1` → `b0270eb3b36c02f38d9a4b75732ea5f3d428403e745645856b0be98c30c54cd5`.
Whole-archive SHA-256 before/after, 3MiB: `7ad8f6710b9beb9dc7179f68521147bfa3aac4ff7e3511181dbaf9ff8b737a4f` → `5c9da60889fd9afa55294a8e89e040cf8d5e1b4987411604a5bbfdb16501d910`.

Both Readers returned the same correct file payload and passed `read`, `read_range` and `verify`; only **selection of the generation** differs. No checksum forgery or logical-payload corruption was observed. This is a deterministic **same-inode in-place mutation** attack by a local actor with write access, not normal append-only Writer behavior, not a remote exploit, and not evidence of a supported mutable-source contract.

## Decision, limits and next owner action

**Science decision:** J24G06c prediction confirmed in two scanner-window geometries. The previous #651 nonconfirmation was scoped to a small buffered-read geometry; it was not proof that memoization preserves generation selection under all source-mutation interleavings. This result does *not* invalidate #650's genuine 103.71x static-corpus speed gain or its signed recovery on immutable input.

**Product decision unlocked:** #650 cannot promote general mutable-source temporal-consistency guarantees without a documented source immutability boundary or an actual snapshot/custody method. At minimum, clarify whether external in-place mutation during `CMPCT(path)` is unsupported. If supported, evaluate exact-source fd snapshot/version pinning or mutation detection plus fail-closed semantics and re-run functional+recovery+performance gates. No promotion or merge from this science.

**Self-critique:** The injection is deterministic at one decoder boundary, not a high-frequency adversarial scheduler; the two archives share one payload family and only Linux is measured. The effect may not transfer to filesystem snapshots, Windows/macOS or a specified immutable-input API. Artifacts do not carry the raw mutated CMPCT bytes for an independent second parser; footer structure and SHA claims were checked within the executed test. We make no CPU/RSS, full release performance, cryptographic attack or remote exploit claim.

**Discovery Engine:** Preregistration fixed the new window geometry in advance. Causal discriminator was moving A/B across the scanner read-buffer boundary while holding sources and semantics fixed. No concurrency collision; child branch only, no Reader source edited. No `docs/discovery/STATE.json` or policy edit. Counterfactual prospective lesson: when deterministic in-place mutation fails to alter the re-read result, inspect the I/O buffering/window boundary before interpreting it as cache safety. One replicated counterexample is insufficient for a global policy rewrite.

## Additional source-level contract discriminator (append-only Writer versus hostile in-place rewrite)

The unchanged first-party `src/cmpct/transactions.py` at #650 source is Git blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`. Its `_append_generation` and `append_update` mutation paths write using `open(archive, 'ab', buffering=0)` and fsync new data before committing new footers. Thus the J24G06c direct **rewrite of an older existing footer at the same byte offset is not an operation demonstrated by those first-party Writer functions**. This is material threat-model narrowing: the observed candidate-specific divergence does not by itself establish incompatibility with the ordinary cooperative append-only Writer contract. Even with append-only writers, an independent reader-opening race / truncation / legitimate multiwriter behavior needs separate genuine-product testing before promising full concurrent consistency.

The cheapest product decision is therefore **first determine the supported source mutability semantics** (stable bytes during open, append-only concurrent Writer, or unrestricted in-place mutation) from existing authoritative contract and real Writer tests. Only then select a proportional reader fix or documented refusal boundary. Neither the deterministic challenge nor the parent N=256 speed court proves what the as-yet-unwritten policy must be. Do not silently elevate one adversarial conditional into universal release failure, or silently declare unrestricted mutation supported.
