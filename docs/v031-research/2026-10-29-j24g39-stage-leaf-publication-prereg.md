# J24G39 — preregistered post-verification stage-leaf publication test

**Time/source boundary:** 2026-10-29 UTC. Parent #745 exact `3e6b1c75a303ba638d420e49b658b90c7b573773` (unmerged POSIX compaction candidate). Published `main` remains v0.30.0 / revision 24. **Research only, NO merge/release/product claim.**

## Scientific question
Does pinning the Builder/Reader write FD and stage/parent directory FDs ensure the bytes and inode that were *verified* are the bytes/inode actually *published* when a same-UID actor can mutate a private stage directory entry immediately before `os.replace`?

## Mechanism / forecast / disproof
In #745, the verified archive is accessed via `write_fd`; final POSIX publication is `os.replace("payload.cmpct", dst.name, src_dir_fd=stage_dir_fd, dst_dir_fd=parent_fd)`. The source filename still resolves a mutable directory entry, **not** `write_fd`. Predict that replacing that leaf in the narrow verified→rename interval causes publication of (A) an attacker-controlled symlink, or (B) attacker-controlled regular non-CMPCT bytes, while the original FD-backed verified inode remains intact. Predict non-attacked control publishes the correct archive. If the candidate rejects either planted leaf before publication, or publishes the verified inode regardless of the rebind, reject/narrow the hypothesis. Neither stage-name randomness nor checking the source FD alone is a sufficient control.

## Cheapest decisive evidence
Execute the actual installed Builder→Reader→`compact_archive` on a synthetic legitimate revision-24 file. Freeze source hash and logical rows; record baseline valid output. Deterministically interpose **only** on the genuine fd-relative stage→destination `os.replace` boundary; atomically move the already-verified stage leaf to an adjacent private witness name, plant a symlink to an outside sentinel or ordinary invalid bytes, then call the original OS primitive. Assert the source, outside sentinel and moved verified archive are unchanged, and explicitly classify the destination type/bytes. Repeat Ubuntu/macOS because the candidate is POSIX-only. Store exact HEAD/source blobs and machine receipts. Do not weaken any inherited verifier, success rule or release threshold.

## Alternative explanation / limits
The actual product may revalidate source inode at rename (contrary to static source); tests may be intercepted too early/late; a symlink might be rejected by OS publication; an attacker granted the **same UID** has powers beyond ordinary distinct-UID isolation. The test does not prove exploitability by distinct-UID actors nor undermine v0.30.0 published code; it tests an **unreleased** candidate. The deterministic hook is a concurrency schedule witness, not a demonstration of an asynchronous exploit frequency. It cannot establish Linux/Windows universal safety, durability, power-failure resilience or product performance.

## Decision and handoff
If both attacks succeed, **veto** any claim that #745 binds verified inode to published inode under a same-UID stage-leaf adversary. Do not rush a standalone forked fix: owner #741/#745/#738 must choose a coherent OS-specific inode-bound publication primitive or explicitly weaken the threat-model *claim* (not the verifier), backed by new adversarial evidence. If fail closed, preserve raw negatives and investigate why. No changes to canonical format/version, main, Discovery STATE, frozen tests or benchmark/release law.

**PARETOBONK:** cheaper than another large compaction matrix; strongest control is source-identical no-attack export, not merely an OS-level model; materially different from pre-open ancestor substitution (#744) and cleanup ownership (#745). 