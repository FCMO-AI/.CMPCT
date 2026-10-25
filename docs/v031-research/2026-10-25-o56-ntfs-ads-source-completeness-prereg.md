# O56 — Windows NTFS named-data-stream source completeness preregistration

Date: 2026-10-25 UTC. **Pre-result scientific prediction.** Research only; NOT a format, release or product patch.

## Current authority and source boundary

Released v0.30.0 remains the coherent r24 floor. Exact studied candidate is the unmerged O50 Builder composition [#405](https://github.com/FCMO-AI/.CMPCT/pull/405), frozen commit `17c96603e33b02b3f2f9e0079eec2b128f293be8`, Builder blob `21a9ec696df13961c25301654feb607a7e161a4c`. O47/O48/O50 cover Win32 physical hardlink owners and static special-file refusal, not named NTFS $DATA streams. O52/O54 already research different active-source races; O56 requires stable source bytes and **no concurrent mutation**. Prior [PR #332](https://github.com/FCMO-AI/.CMPCT/pull/332) concerns hostile *archive extraction names* containing colon syntax, not enumeration of named *source* streams.

## Primary falsifiable question

Can O50 return success and produce an authentic, SHA-verifying r24 archive while silently discarding nonempty **named NTFS data streams** attached to an otherwise ordinary, stable source file? This is a source-inventory/fidelity test, not a cryptographic weakness.

**Prediction:** On an NTFS-backed Windows runner, Python's ordinary file iteration/stat/read path will see the unnamed $DATA stream but will not enumerate or capture a nonempty `:cmpct_o56:$DATA` stream. The original Builder will return success, original regular member bytes will read and verify, extraction will produce a regular file without the additional stream. This would show a supported-looking success that is incomplete with respect to NTFS physical source semantics.

**Disproof:** The exact unmodified O50 Builder either explicitly refuses to archive such a source before publishing an output, or both the unnamed and named streams survive archive+extract byte-for-byte with their correct physical association. If NTFS functionality is unavailable or a named stream cannot be proven present before archiving, the experiment is **INCONCLUSIVE**, never PASS or evidence of loss. If the package, source SHA, real Builder/Reader or true tests are not used, no result credit.

## Lowest honest evidence rung

Run a small installed-product test on Windows 2025:
1. Create a stable ordinary file with deterministic unnamed-stream bytes and a nonempty named stream via actual Windows path semantics. Verify the named stream by **independent Win32 FindFirstStreamW / FindNextStreamW enumeration**, direct binary read and unchanged regular-file stat size.
2. Invoke the actual `Builder(...).build(...)` on this tree with a clean installed CMPCT, open the resulting revision-24 archive in the real `CMPCT` Reader, call `verify()`, read the ordinary member, and extract to an independent NTFS directory.
3. Independently enumerate restored streams and check if named bytes are recoverable. Record archive bytes, source/restore ordinary SHA, named-stream SHA, source/restore stream inventories, Builder/Reader installed paths, source Git blob and exact workflow HEAD.
4. Add a **physical hardlink** variant: an alias sharing one NTFS inode also shares named streams. The same experiment should not confuse loss of streams with loss of hardlink identity. Use an ordinary no-ADS positive control.
5. Retain JUnit and machine-readable evidence, including source SHA and explicit observed outcome classification. Include a real test-execution receipt that fails if assertions did not execute.

No static mock of filesystem iteration is scientific proof. No codec benchmark or historical matrix is needed for this binary question.

## Controls and alternative explanations

- A colon-bearing *pathname* being invalid is not equivalent to a named stream attached to a valid file. The experiment creates the valid unnamed file first and independently enumerates stream records via Win32.
- Ignoring named data intentionally may be an explicit **format support limitation**. The scientific claim is narrower: *whether success silently drops source information*, not that r24 already promises to store all NTFS metadata.
- A tool that preserves only the unnamed stream could still be lossless for **its explicitly documented supported subset**; this research seeks an honest refusal or prominent excluded-metadata contract rather than immediately changing format.
- Cross-volume restore is avoided; all source, output and restore roots live on the same NTFS-backed runner volume.
- Original data remain stable; live-file race and snapshot coherence belong to #408 / O52 / O54.
- Current correctness and release gates remain unchanged. No benchmark/threshold/validator mutations.

## Decision and next-action law

If predicted silent loss is confirmed, open one narrow issue on source completeness (without duplicating #408), inform the O50 owner and recommend the cheapest product action **first**: robust Windows source-inventory detection plus fail-closed refusal of unsupported named streams. Only contemplate native stream serialization and matching extraction after a bounded complete-byte, portability and format-evolution design. If the result is inconclusive, preserve the failure/infrastructure cause and rerun only after a discriminator changes.

Research can earn scientific credit; **product credit = 0** until integrated, fully source-bound, portable and gate-valid. Never merge this scientific branch as a cosmetic release or claim improvement in stored bytes.

## Concurrency and evidence governance

The branch is isolated from O50, O52, O54, Reader and Writer owners; no owner PR branch or `docs/discovery/STATE.json` edits. The name O56 denotes this standalone narrow scientific question, not an auto-incremented version or project-state authority. Tests are designed after this preregistration. Future writes must reconcile fresh O50 HEAD and any new owner claims.

## Adversarial self-review

Potential hidden test escape: a Windows runner may mount the temporary directory on ReFS or another stream-incompatible device, or a test may mistake a colon-containing filename for a named NTFS stream. **Independent stream enumeration and unconditional Windows-only source checks are mandatory.** A green workflow containing skipped tests, failed source blob binding, only an ordinary-byte checksum, or a fake Reader verify is a false green, not evidence. No change to O50 bytes or comparator semantics is allowed.
