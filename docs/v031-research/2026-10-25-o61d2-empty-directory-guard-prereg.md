# O61-D2 preregistration — can the existing O57 file-stream guard safely be called on an ordinary directory?

Date: 2026-10-25 UTC. Parent decisive O61-D source-loss court: Windows Actions #40168116780 and independently [O61-D result](2026-10-25-o61d-ntfs-directory-ads-result.md). **This is a separate cheap false-remedy falsifier; no product changes.**

## Primary question and prospective prediction

Microsoft MS-FSCC 5.1 says directories have no default unnamed $DATA stream (their default stream is $I30:$INDEX_ALLOCATION), although named $DATA streams can exist. The existing O57 `refuse_unsupported_named_streams()` allows only `::$DATA` and assumes a regular file. **Prediction:** calling that existing guard on a plain, stable NTFS directory with no named stream will incorrectly raise (likely Win32 ERROR_HANDLE_EOF on `FindFirstStreamW`), so merely inserting the helper call in the Builder's `K_DIR` branch is unsafe.

Strong simpler control: create one new NTFS directory containing no files or streams and confirm its existence; call the Win32 `FindFirstStreamW` API independently of the CMPCT helper, record its raw outcome and last error; then call the genuine **installed O57 helper**. A regular file with no ADS passes the existing guard as the inherited reference. All tests are Windows-2025/CPython 3.11 and source-locked to unchanged O57 code. No skipping or manufactured success if Windows cannot run the actual test.

## Disproof and decision

If the real helper accepts the no-ADS directory, or the raw API lists an allowed default stream, **reject the prediction**, explicitly record the alternate observed semantics, and do not claim that the naïve helper call rejects valid directories. If the guard rejects, the reusable implementation lesson is *not* to blindly apply file-only `::$DATA` semantics to directories: add a distinct safe directory policy/handling of empty enumeration when product owner integrates O61-D. Do not call an observed helper refusal a product regression because the current helper contract explicitly targets regular files.

This micro test is a guard-design negative only, not proof of a complete NTFS Builder fix; preserve original O61-D and O57 tests. No changed archive bytes, benchmark timing, safety/release policy or `docs/discovery/STATE.json`; no product promotion or release authority.
