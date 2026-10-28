# J24B06-R1 — fail-closed logical-size admission before extraction writes

Date: 2026-10-28 UTC
Status: FROZEN PROSPECTIVE ENGINEERING HYPOTHESIS. No release, merge, or format/version authority.

## Base and independent scientific cause
Published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Independent source-pinned J24B06 #688, run 40732802978 (Ubuntu 24.04; second OS run pending at the time this hypothesis was frozen), established that signed negative symlink row size -8192 cancels an ordinary +8192 regular file, bypasses `extractall(max_bytes=4096)` and writes 8192 B. Full signed primary and tail index, physical SHA equality, actual first-party Builder, verify=2, independent wire audit; issue #689.

## Minimal causal repair
The inherited `extractall` already scans all file rows once to sum logical sizes. Combine type-exact nonnegative size admission into that same pass, counting only non-directory sizes for `max_bytes`. Validate BEFORE `dest.mkdir` so malformed signed input cannot even create an output directory. Reject `bool` (Python int subclass), floats/strings and negative values as malformed. Do not create any global memory/cache or change Blob/Reader/Builder/Format/native ABI, journal or release gates.

## Frozen acceptance/kill controls
- Original Builder archive with 8192-byte regular payload + symlink to it, legitimate symlink length 11 and cap 4096: reject unchanged, no output path.
- Signed symlink metadata -8192 and cap 4096: reject before destination creation. Confirm actual `verify()` still demonstrates the scientific issue (source signed but not valid semantics; the repair is scoped to extractall).
- Signed negative size and no `max_bytes`: reject (malformed index may not be extracted without a budget).
- Signed zero or bool length: zero is nonnegative but fails cap due regular 8192; bool must reject as malformed, preventing `True` arithmetic in lengths.
- Legitimate archive with cap >=8203: successfully extract original file and safe symlink exactly.
- Zero-size legitimate regular member: extract successfully under cap=0.
- Nontrivial bytes and metadata shall be byte-identical to original archive; not a reserialization or schema mutation.
- Record memory/cold-open/cpu acceptance cost. The patch must perform O(number of rows) size accounting with no extra pass or new retained O(N) index. No invented performance win.
- Windows/macOS source-exact installed courts, indexed signed journal generations, hardlinks/sparse/CDC/VZIP and complete historical release tests remain separate promotion gates. No merge until satisfied.

## Strongest alternative
A global constructor admission of all row sizes is conceptually stronger, but it changes open/verify/list behavior and can strand descriptors on failure in the current `__init__`, requiring a broader lifetime and recovery review. Extractall-only admission is the smallest immediate reduction of confirmed caller-visible limit violation. If correctness needs ordinary open to reject malformed sizes, preserve that as follow-up debt, not a stealth claim.

## Stop and self-critique
If any existing valid archive is rejected solely due to newly tightened type semantics, investigate a real format counterexample and do not weaken evaluator. If the signed invalid size is still written or a positive original is blocked under generous cap, this candidate is not promotable. Do not reinterpret success as complete signed-index safety or sparse publication correctness.
