# O190 preregistration — signed CMPCT mtimes into bounded complete ZIP DOS dates

Date: 2026-10-26 (UTC). Status: **PREDICTION / NOT YET MEASURED**.

## Authority / inherited negative

Base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`, released CMPCT v0.30.0 and format revision 24. Original O184 (#515) runs 40325877075 and 40326480091 provide authentic signed-1960 r24 archive evidence: Ubuntu exported ZIP, Windows verified CMPCT then failed in `time.localtime(negative_seconds)` with `OSError: [Errno 22]`; ordinary 2000 control exported successfully. That negative remains immutable; this candidate changes *only its own product code*. The original O184 PR remains a negative experiment, not retroactively relabeled.

## Primary falsifiable question

Can the exact `CMPCT._zip_dos_time` fast export helper map every signed-i64 r24 timestamp to a legal *complete* DOS-local datetime without calling incompatible host `localtime` for intrinsically out-of-range times, while retaining byte-for-byte historical ZIP DOS metadata for all ordinary representable local times?

Prediction: negative/pre-1970 dates too early to enter DOS range become **1980-01-01 00:00:00** on Ubuntu/macOS/Windows; times too late become **2107-12-31 23:59:58**; local times inside range retain existing encoding, including two-second truncation. Immediately outside either boundary, clamp the *entire* date/time rather than changing only the year. `mtime_ns=0` remains the old unspecified/default sentinel but becomes deterministic legal DOS epoch in every timezone.

## Controls / alternatives / risks

1. **Do nothing:** Windows O184 failure persists; reject.
2. **Catch OSError from localtime:** avoids crash but can return an invented nonlocal date and does not repair incomplete-year clipping; reject.
3. **Convert all timestamps using UTC Gregorian arithmetic:** portable, but silently changes existing ZIP local-time semantics for ordinary files; reject.
4. **Chosen:** DOS-range safe-gating outside a conservatively wide UTC transition band, exact integer-floor seconds inside, host `time.localtime` for representable neighborhood, then lexicographically clip *all six calendar fields*.
5. **Stronger simpler comparator:** Python `zipfile` DOS clipping lower bound; independent `ZipInfo` decode and calendar validity checks.
6. **Potential negative:** platform-specific timezones near 1980/2108, ancient leap offsets, Windows CRT limitations within the safe band, ZIP64 stdlib fallback which currently assigns default 1980 timestamps rather than calling this helper; the fallback is existing separate debt and not falsely claimed fixed.

## Instrument and promotion / kill conditions

Before shipping claim require genuine installed CMPCT wheel, Linux-built authenticated r24 signed-1960 and ordinary-2000 files, same archive SHA received by Ubuntu/macOS/Windows, `cmpct verify`, actual `export_zip`, independent stdlib ZIP member/CRC/content check, positive ZIP DOS date, and candidate source identity. Add negative/positive boundary tests for 1979-12-31, 1980-01-01, 2107-12-31, 2108-01-01 and signed-i64 extremes; use at least two timezones on POSIX. Include an ordinary 2000 source-level frozen old-function comparison and any exact output ZIP bytes if available. Preserve negative contradictions.

**Disproof:** Windows still raises on signed-1960, wrong ZIP content, malformed date, in-range old/new difference without justified precision correction, inherited Reader security/ZIP staging regression, platform job skipped, or deterministic changed r24 archive bytes. Research success does *not* authorize merge/release. Full parity, RSS/create/extract, alternate ZIP64 path, concurrent ZIP publication and exact-head general CI are separate gates.

## Concurrency and ownership

Recent open ZIP stage owners #492/#512 and post-rename falsifier #514 own publication; canonical ZIP naming #499 and J24W01 #507 own different Reader surfaces. O184 #515 owns source-exact negative evidence, and this O190 is a **separate, narrow, reversible correction** of `_zip_dos_time`. No changes to those branches, shared discovery STATE.json, frozen historical tests, thresholds, or release metadata. Notify active ZIP owners with exact-head evidence rather than overwrite their implementations.

## Scientific status

This record is a prediction written before any O190 Reader mutation. No host outcome is claimed yet.
