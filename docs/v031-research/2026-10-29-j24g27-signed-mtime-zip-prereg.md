# J24G27 — preregistration: signed r24 timestamps through legacy ZIP export

Date: 2026-10-29 UTC. Evidence level: prospective, no measurement or shipping change at registration.

## Authority and ownership
Released CMPCT source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Current public revision 24 and release v0.30.0; no version, release lock, benchmark, source or threshold edits. GitHub issue/PR search at registration found no owner for `_zip_dos_time`, negative epoch, or ZIP-export time conversion. This is an independent cross-host compatibility falsifier, not a fix to owned ZIP CRC/atomic-output chain #284/#492/#707.

## Question and baseline
The r24 manifest can represent signed nanosecond mtimes (and the original reference Reader preserves them). The ZIP endpoint must map a valid pre-1980 file date into the conventional DOS date interval, without preventing export on a supported host. The released Reader calls `time.localtime(mtime_ns / 1e9)` before clamping to 1980. Whether this accepts a valid negative timestamp varies by platform C runtime.

## Prospective hypotheses
H1: On the same fixed first-party physical r24 archive with `mtime_ns=-1_000_000_000`, `CMPCT.read()` and `verify()` succeed on Ubuntu/macOS/Windows, demonstrating an ordinary valid member independent of conversion.
H2: `CMPCT.export_zip()` for that exact input fails with a time-conversion error on at least one host while the ordinary 2020 control exports correctly. This is a predicted portability gap, not presumed evidence.
H3: All successful exported ZIPs decode exact contents and their DOS dates remain within 1980–2107.
Disproof/retirement: if all three hosts export both inputs successfully with correct bytes/date, retire this hypothesis; do not produce a fix. If the archive is invalid or `read/verify` fails, the test is inconclusive and cannot blame timestamp conversion.

## Cheapest decisive instrument
Generate first-party archives on one Linux host, using `Builder(...,workers=1)` and two real files of identical content with `os.utime(ns=(-1_000_000_000,-1_000_000_000))` and ordinary 2020 respectively. Preserve fixed physical artifacts, SHA256, installed source SHA, metadata row and manifest. Cross-host jobs download those same bytes rather than regenerate them. Run the current installed Reader in a clean process; record platform, `time.localtime` behavior, read, verify, ZIP export, normalized traceback/exception, member bytes and zipfile timestamp. Repeat at least twice per host. No forced-cast/monkeypatch and no altered semantics.

## Stronger control and alternative explanations
- Ordinary 2020 timestamp control proves host package installation, ZIP encoder and file permissions.
- Fixed payload and SHA prove no separate host filesystem-specific Builder path.
- Each host reports `CMPCT.by[name][3]` exactly; failure to preserve the negative signed timestamp invalidates the claim.
- A failure outside `_zip_dos_time` is classified as infrastructure/other instead of the predicted mechanism.
- Successful export can legitimately differ in local DOS timestamp across time zones; **do not assert cross-timezone ZIP byte identity**, which is not current product law.

## Accounting and decision
This is correctness/portability research only: archive bytes held fixed; no asserted create/extract/CPU/RSS improvement or release credit. If positive, send exact result to an existing ZIP-chain owner rather than independently patching their branch. Preserve all negative controls. `docs/discovery/STATE.json` is not a lock and has separate ownership (#574).
