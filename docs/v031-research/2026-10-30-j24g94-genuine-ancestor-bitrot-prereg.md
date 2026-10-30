# J24G94 — Prospective authentic ancestor digest-damage Writer continuation

**Preregistered before implementing J24G94 code or CI.** 2026-10-30 UTC. Research-only; no product, format, version, comparator, CI gating, release, test-weakening, or Discovery STATE mutation.

## Current authority and existing evidence
- Release main v0.30.0/revision 24 `80c358f8824ec1b20d349c92ed94c898090969b0`.
- Owned J24G92 #856 `f29561c5e2d36a8f47aa35f61191911c0611be6b` established unbound footer predecessor history can resurrect a committed DELETE on Ubuntu/Windows.
- Adjacent J24I67 #859 owns independent two-field *hostile parent rewrite* camouflage. Do not duplicate.
- J24G93 #860 `5f765553a62a57ecd1ca4ac2b15bf713b8496867` hosted three-host actual public Writer correctly skips manually injected unrooted SHA-valid orphan; that test does **not** model genuine Writer-produced generation bitrot or a real crash.
- An explicitly preregistered adjacent detached O0 on original J24G92 16/128 hosted archives physically flipped one authentic F2 SHA digest byte while preserving F3 valid, and *simulated*, not executed, a successor linked to F1. The prior O0 showed Ubuntu/Windows 13→15→14 and 125→127→126 member counts with synthetic successor. This prospective experiment requires real installed Writer.

## Primary scientific question
Will the **unchanged installed public Writer** correctly append a fresh DELETE when the real latest F3 footer is individually SHA-valid, but its F2 predecessor is now SHA-invalid due to a *single-byte stored digest corruption*, causing Reader/preflight to recover F1?

Predict all hosts:
1. Build N=16/128 real files with released Builder; emit genuine public DELETE f0, DELETE f1, DELETE f2 (F0→F1→F2→F3) and verify original surviving N-3.
2. Flip exactly one stored **F2 payload SHA** byte, leaving F3 footer payload and stored SHA unchanged. F3 cannot reach checkpoint; F1 is now latest recoverable. Reader and preflight must select F1, showing N-1 live files.
3. Run actual unchanged public `append_delete(f00003.dat)`; new F4 must link to F1, **not** the physically newer individually SHA-valid F3, and present N-2 members (remove only f0 and f3).
4. Compare to same exact physical F0+F1 valid prefix with public fourth DELETE (no corrupt orphan tail). Compare logical paths and all full reconstructed member digests.
5. Corrupt newly appended final SHA and require Reader/preflight to recover F1 and N-1 files; differently rooted binary parse rejects invalid F2, independently authenticates F3 payload, F4 predecessor, complete payload content and error controls.

## Baselines, alternative explanation, kill conditions
- Simpler control: J24G93 injection with `prev=0`; if result only survives that artificial orphan but not real Writer chain corruption, the result is narrower.
- Alternative: Reader may fall back to F1 but Writer may refuse new commits because invalid F2 remains physically present; or preflight and Reader may disagree. Record all failures as scientific negative.
- Falsify H1 if actual installed Writer `prev` is not F1, or append fails unexpectedly. Falsify H2 if per-member bytes, strict preflight, digest-damage recovery or clean-control state differ.
- Keep previously successful J24G93 source head and hosted evidence intact; no retroactive threshold edits, no silent release promotion.
- Physical costs: count 1-byte F2 modification and exact appended F4 bytes separately; no size, runtime, RSS or codec performance claim. No disk failure/power loss was reproduced; source mutation represents *manual checksum damage*.

## Decision unlocked
If genuine public Writer continuation succeeds on Ubuntu, Windows and macOS, retire the unconditional **nearest physically SHA-valid predecessor** validator as incompatible with documented r24 recovery. This does not prove all historical authenticity guards impossible. Owner #857 must still resolve bound-versus-unbound ancestry in future format with legitimate crash/recovery, native, hardlinks/xattrs, multiwriter, bounded CPU/RSS, external attestation and semantic identity checks. Preserve output as research-only, not product credit.
