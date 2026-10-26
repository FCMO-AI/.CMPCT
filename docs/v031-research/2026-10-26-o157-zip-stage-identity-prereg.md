# O157 preregistration — ZIP staging pathname custody after exclusive creation

Status: **PREDICTION FROZEN BEFORE TEST CODE/RESULTS** (2026-10-26 UTC). Scientific negative experiment only; no product, format or release credit.

## Authority, scope and concurrency
- Canonical `FCMO-AI/.CMPCT`; published v0.30.0; on-disk revision 24 unchanged. Normative CMPCT AGENTS/discovery/quality and FCMO runtime apply.
- Parent exact O149 product candidate [#492](https://github.com/FCMO-AI/.CMPCT/pull/492) `ca01d885fedc8ffc343b9c3c624eddd134158452`, Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`.
- Independent sibling O150 candidate [#491](https://github.com/FCMO-AI/.CMPCT/pull/491) `48bbb41661f8b19d369c50b06bec1018cd4400e9`, Reader blob `f38662c8db4132895778951263d83d24022f9296`.
- O143 negative [#489] verifies prior-output corruption without staging; O149/O150 fix ordinary failures; O151 [#493] already prices mode/symlink destination semantics; O153 [#495] already prices source-exact normal export. **Neither owns a post-allocation private stage pathname pivot.** This O157 is a separate deterministic falsifier; do not modify #491/#492 product branches.
- No `docs/discovery/CONCURRENCY_PROTOCOL.md` exists at the verified canonical v0.31 head. Current staleable discovery STATE has no ownership claim over this exact output-stage manipulation.

## Primary falsifiable question
Does ZIP staging protect **unrelated regular filesystem content** against a deterministic change of the staging pathname after its `O_CREAT|O_EXCL` / `mkstemp` creation and before the inner ZIP writer reopens it? Existing-path publication atomicity is not sufficient if the supposedly private output handle is dropped and a pathname is followed again.

### Mechanism and prospective prediction
Both O149 and O150 create a private sibling, close the creation descriptor, and subsequently reopen by pathname for ZIP serialization. A process with actual write permission to the output directory can replace that sibling during this window. On POSIX, replacing the stage with a symlink to a *different ordinary file* should pass O149's inner source-inode/kind guard (the victim is regular and is not the CMPCT archive); the writer should follow the symlink and truncate or overwrite the unrelated victim. O150's inner writer similarly opens the pathname and should follow that symlink. Original target path starts as a distinct valid ZIP. A name replacement may then publish the symlink under the requested target name. This is a **path-custody failure under malicious concurrent directory mutation**, not evidence of a weakness in SHA-256, compression, or ZIP parser integrity.

### Cheapest controlled discriminator and strong controls
- Use unmodified **builder-independent** revision-24 RAW `raw.bin` fixture from `tests/conformance/v24-direct-codecs.json` (blob `d10b7dab9126d39e819a74279c186363a163f2ef`) and verify its exact archive/logical SHA.
- Run the installed O149 and O150 source-identical Readers in separate child-process test conditions, outside the checkout, on Ubuntu and macOS. Each test gets its own temporary output dir, target ZIP, external ordinary victim sentinel (not the CMPCT source), and a local source snapshot.
- **No-pivot control:** ordinary `export_zip` succeeds, emits a readable ZIP with exact `raw.bin`, leaves external victim untouched and source unchanged.
- **Pivot injection:** intercept the first close of the just-created stage descriptor *after* it has closed, or the immediate call to the inner writer before it starts, and replace only that private stage path with a symlink to the victim. No race timing or background attacker processes; this is a deterministic interleaving that a concurrent directory writer could realize. Do not tamper with the Reader's payload, hash, archive path, index or output target. Require stage was a freshly created regular sibling first and that target/victim were distinct.
- Record target and victim before/after bytes, SHA-256, size, file kind and symlink target; original archive fingerprint, exact source blob, operating system, actual exception if any, original cleanup residue.
- **Kill/falsify:** both implementations retain victim bytes and do not publish an unsafe symlink under the claimed interleaving; or the filesystem rejects the stage replacement before any write; or source/test identity is not exact. If one implementation differs, preserve split result, never promote a broad two-owner claim.
- **Control for alternative explanations:** proof must show a correct unpivotted export on same fixture, a real stage file prior to replacement, and preservation of CMPCT source. No simulated writer corruption or monkeypatch that writes victim bytes directly is admissible.

## Cost/semantics and promotion boundary
No full-product benchmark. Threat requires an adversary or competing actor able to mutate the output directory during creation; it is **not** a claim that every ordinary ZIP export is unsafe or that the random stage name can be guessed before creation. Explicit create-time `O_EXCL` is a useful control against pre-planted symlinks, but it cannot preserve identity across a close-then-reopen. A possible product response is keeping the exclusively opened descriptor as serialization authority, then authenticating the object at publication; this may need trusted-directory assumptions, portable fd-aware ZIP writers and further race tests. No in-place source edit, frozen test weakening, merge, numeric release, or success claim before hosted results.

## Counterfactual prospective discriminator
The critical inexpensive observable is whether the candidate retains the exclusive stage file descriptor through all writes. Both codepaths visibly close it before reopening, motivating this single deterministic interleaving; the experiment decides whether that static concern has an actual externally destructive manifestation.

Decision remains **UNMEASURED** until a source-bound hosted run returns raw evidence.