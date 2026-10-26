# J24W02 — Windows S_CHUNKS/S_CDC extraction with unavailable fd chmod (preregistered)

Date: 2026-10-26 UTC. **Prediction, before candidate product modification or hosted result.**

## Authority and competing owners
Canonical CMPCT v0.30.0 / r24 released; isolated child of O193/PR #521 at commit `392112ce859db5a7f85be593c82d1cabc1f5131f` (Reader Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`). O193 owns ZIP64 streaming, O201/#534 owns independent S_CDC malformed-descriptor research, and issue #535 proves the unrelated missing-`os.fchmod` Windows portability failure. This child is a small independently reviewable compatibility fix; no write to those owners' branches, no release claim, no format/ABI/algorithm change.

## Single falsifiable question
Can `_extract_chunked_verified` preserve exact valid S_CHUNKS/S_CDC reconstruction on Python hosts without `os.fchmod`, while keeping POSIX fd-bound chmod, unchanged authenticated length/SHA checks, and existing destination preservation on corruption?

- **Baseline:** Python on Windows 2022 raises `AttributeError: module 'os' has no attribute 'fchmod'` before chunk writing; O201 valid-wire control passed verify/full read/range but failed extraction. POSIX extraction succeeds.
- **Mechanism:** feature-detect the fd chmod primitive once; if missing, omit only optional fd-mode application and continue secure, exclusive `mkstemp` staging; do not fall back to `os.chmod(stage_path)`, which would reopen mutable namespace custody, or swallow unexpected exceptions.
- **Strong simpler control:** platform `hasattr(os,'fchmod')`; equivalently feature-detect via `getattr`, preserving `OSError` suppression only when the API exists. The general extractall(metadata=True) path independently handles best-effort `os.chmod` after materialization; this experiment does not claim full Windows POSIX-mode parity or fix symlink-stage substitution (#528).
- **Alternative explanation:** O201 failed due to its synthetically crafted wire or missing codec. Refute by independently frozen Builder-free valid S_CHUNKS & S_CDC vectors with actual RAW/Zstd/Deflate, plus Builder-produced large chunked file.
- **Kill:** any same-source Windows positive fixture fails; any POSIX mode/bytes/corruption regression; invalid archive accepted where inherited tests refused; any new file path opened for mode setting; test requires weakening historical court or synthetic benchmark claims.
- **Expected discriminators:** three-OS installed-package tests, direct feature-absence simulation with `monkeypatch.delattr(os,'fchmod')`, exact fixed chunk-map archives SHA/round-trip, already inherited chunk corruption preserves old destination, stage cleanup, source Git identities. This fixes #535 only, not #531 mutable-mmap hash/write, #528 stage publication, or malformed S_CDC lengths discovered by O201.
- **Evidence tier:** product candidate direct host tests on authentic unchanged conformance vectors and Builder; not release gate or performance benchmark.
- **Costs:** extra feature lookup per extracted file should be tiny but unmeasured; no changes to physical archive bytes. Host mode fidelity when API absent is best-effort, not falsely asserted.

If the three OS acceptance court succeeds, publish an owner handoff with exact head/checks and remaining debt. Never merge without owner's reconciliation and complete release gates.