# O57 — source-side Win32 ADS fail-closed admission (preregistered product candidate)

Date: 2026-10-25 UTC. **Prediction before product edit.** Independent implementation candidate stacked on exact O50 [#405](https://github.com/FCMO-AI/.CMPCT/pull/405) `17c96603e33b02b3f2f9e0079eec2b128f293be8`, Builder Git blob `21a9ec696df13961c25301654feb607a7e161a4c`. This candidate does not modify O50's owner branch, #408 or O56's immutable original scientific code.

## Decisive inherited negative

Preregistered O56 [#411](https://github.com/FCMO-AI/.CMPCT/pull/411), hosted [Actions #40164441760](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164441760) on original O50: installed Windows 2025 NTFS 3/3 true tests. Physical source had named `:cmpct_o56:$DATA` 331 B and unnamed `::$DATA` 4096 B; original Builder returned success, r24 verified and extracted only unnamed stream. A physical hardlink preserved its relation but lost named stream. Ordinary no-ADS control passed. [Issue #412](https://github.com/FCMO-AI/.CMPCT/issues/412) owns the scoped loss category. This is not a checksum failure; source inventory omitted information.

## Hypothesis and minimal mechanism

A guarded Windows-only `FindFirstStreamW/FindNextStreamW` enumeration at source **regular-file admission** detects arbitrary nondefault named streams (not fixture-specific), then raises `OSError` **before any physical output archive is committed**. The pure enumeration gate does not change supported input archive bytes or decode format. On POSIX it performs no syscalls or policy change. The existing Builder scans real directories and files; Windows NTFS named streams are not separate `scandir` entries and cannot be reconstructed by r24. Prefer fail-closed refusal now over unsupported native format extension.

## Alternatives and economic risk

- Full named-stream serialization and reconstructing ADS would require format/reader/interop semantics, bytes and portability cost; inappropriate before bounded product need.
- A lexical check for `:` in pathnames is ineffective: the ordinary filename has no colon.
- Silently stripping ADS is the confirmed inherited failure.
- A per-file native stream enumeration has additional syscall cost. It requires actual timing measurements for large Windows small-file trees before release; no claim of free performance.
- Platform API call failures are treated as observable errors, not evidence of no streams. This may exclude filesystems/drives that previously could archive ordinary files but cannot enumerate streams; such compatibility debt must be measured, not hidden.

## Falsifiable product test

Build unchanged O50 control and candidate from their exact Git refs on the same installed Windows runner with the same stable synthetic trees.

1. Candidate on NTFS ordinary source + nonempty named stream must raise a clear unsupported-named-stream error, not return success. Verify absent new archive and preservation of preexisting output sentinel.
2. Candidate on hardlinked ordinary source with named stream must reject without losing/rewiring source.
3. Candidate on no-ADS ordinary hardlink/independent-copy tree must create a SHA-verifying r24 archive and restore correct physical alias topology and bytes; complete archive bytes must equal exact O50 parent for same source when reproducible.
4. On POSIX, original O47/O48/O50 specialized tests remain unchanged; candidate performs no Windows probe.
5. Source test must capture true Win32 `FindFirstStreamW` named-stream witness; no mocked enumeration or hidden test skips. JUnit/report custody must prove effective assertions ran.

**Kill / narrow:** a source ADS archive still succeeds; no-ADS stable source changes archive bytes; known ordinary Windows NTFS files spuriously fail; hardlinks regress; candidate cannot verify exact installed source; or Windows API results cannot be distinguished from infrastructure failure. Do not weaken the evaluator or special-file policy.

## Boundaries / honest self-critique

This is **not** a snapshot or source race fix: same-inode content/ADS could mutate after enumeration (#408/O52/O54). Directory-level named streams, reparse points, remote shares, ReFS/exFAT, ACLs and encrypted streams are not fully covered by the regular-file gate. Positive focused evidence may justify a draft candidate but cannot authorize merge/release without those gaps assessed and performance, installed packages, native/fuzz, Reader/Writer, and version/format/release law checked.

No edits to O50, O56, issue #408, Discovery Engine `STATE.json`, historical benchmarks, evaluator thresholds or source-fingerprint controls. Preserve negative and contradictory results. Product claim scope is narrowly **static NTFS regular-file named-stream refusal**.
