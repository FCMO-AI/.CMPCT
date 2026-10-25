# O102 — Win32 metadata=True archive timestamp reconstruction (preregistration)
Date: 2026-10-25
Status: prospective, frozen before constructing/executing test
Source: `FCMO-AI/.CMPCT` O69 #425 exact head `8fe424ac8575da10bf5ecfdb9660d4b5831f638b`, inherited Reader `extractall(metadata=True)`.
Owner boundary: independent **science-only** evidence for timestamp portability; O69 owns Reader xattr code and must not be overwritten. No implementation or release changes authorized by this experiment.

## Measured baseline and question
O86 #444's first installed Windows court encountered `NotImplementedError` from `os.utime(..., follow_symlinks=False)` during `Reader.extractall(metadata=True)` after byte-exact verification. O69 #425 catches that error as a portable fallback; the consequence for *actual Windows file/directory mtime fidelity* is not directly authenticated by those tests.

Can a valid r24 archive containing a regular file and nested directory with a distinct known nanosecond mtime return extraction success with `metadata=True`, perfect logical bytes, and silently wrong physical mtimes on the source-exact O69 Reader on Windows, while genuinely restoring timestamps on POSIX?

## Hypothesis and discriminators
Construct one real source tree with a regular file and nested directory; normalize both mtimes to 2020-02-02T12:34:56Z using `os.utime`; create an actual archive with installed `Builder`; confirm serialized r24 row timestamps and `Reader.verify/read`; extract using ordinary public `CMPCT.extractall(metadata=True)` (never `metadata=False`). Independently `os.stat` extracted regular file/directory mtimes. Predicted: Windows Reader finishes successfully but physical mtimes differ by years; Ubuntu/macOS finishes and mtimes agree within 3 seconds. The logical archive fingerprint and reconstructed bytes remain exact everywhere.

A cross-platform hosted court compares *real* filenames, row timestamps, physical stat, byte hashes and JUnit: a research test **passes when the predicted non-fidelity is observed on Windows**, not when the product is correct. No test contract or evaluator will be weakened for a favorable narrative.

## Strong simpler controls and alternative explanations
- Validate `os.utime(path, ns=...)` for the source independently (test must fail/skip distinctly if unsupported); otherwise a Windows filesystem unable to store the date could be misread as Reader fault.
- Separate `Reader.verify/read` exact content from filesystem metadata restoration; unchanged bytes do not prove mtime.
- Distinguish expected subsecond rounding from an mtime left near current date using generous ±3 s bound.
- Source-exact old O69 installed wheel outside repository; no mock `Reader`, `os.utime` or `os.stat`.
- If Windows *does* restore physical mtimes, hypothesis falsified; if it raises, the new catch-path is not exercised and question narrowed; if POSIX fails, no universal POSIX positive claim.

## BONK / decision
This is a different question from O69's xattr strict opt-in, O72's closed loop, and O86's VZIP budget. Cheap one-tree three-host installed court can confirm or falsify a consequential end-user metadata contract regression; no full performance matrix required. Do not add any Windows path-following fallback without a separate security review: `os.utime(path)` may follow symlink/reparse points and weaken the existing no-follow intent. Potential remedies are native handle-bound timestamp application, explicit strict-metadata API, or explicit documented platform limitation; none selected before observing result.

## Costs, release and stopping rule
One tiny archive, bounded file/dir count, no expensive benchmarks, no format/native/Reader/Product edits. Preserve negative and direct evidence if confirmed. One initial installed CI attempt; if green and decisive, notify O69 owner. If already answered by stronger source-exact evidence, retire this experiment with references and do not rerun. No merge/release/performance credit from this scientific court. Released v0.30.0/r24 and v0.31 canonical branch unchanged.
