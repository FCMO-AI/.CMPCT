# O61-D — Actual O57 Builder silently omits stable NTFS *directory* named stream

Date: 2026-10-25 UTC. **Decision: DEFECT CONFIRMED in independent source-exact Windows research court. PRODUCT FIX NOT IMPLEMENTED; no release authority.**

## Authority, preregistration and frozen baseline

The original prospective [preregistration](2026-10-25-o61d-ntfs-directory-ads-prereg.md) committed first at `bbe17bc3f9a2026ad2b31912b1d897ce85c01766`. Independent branch derives from current O57 owner [PR #413](https://github.com/FCMO-AI/.CMPCT/pull/413), exact parent `d9f9fa724c139c6281f0e2a92c66601bee912618`, Builder blob `7a13545c7dc22ea973f90930fae6cf053f13f1f2`, Win32 regular-file guard blob `23207ac06797fb21322cf327e97928fdbb5241c2`. No product/format/comparator change. Windows documented directory named-stream support: [Microsoft MS-FSCC §5.1](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/c54dec26-1551-4d3a-a0ea-4fa40f848eb3).

## Executed actual scientific court

[GitHub Actions #40168116780](https://github.com/FCMO-AI/.CMPCT/actions/runs/40168116780), push HEAD `27339047a078d167776fb51ed752dd273b1d904f`; original artifact [#12589845383](https://github.com/FCMO-AI/.CMPCT/actions/runs/40168116780/artifacts/12589845383).

On Windows 2025 with CPython 3.11 installed into `site-packages` **outside repository checkout**, source-exact Git blob checks pinned unchanged O57 code and original O57 tests. The independent oracle calls genuine `FindFirstStreamW/FindNextStreamW` on a nested directory; verifies `:cmpct_o61d:$DATA` exists, reads its **676 actual bytes**, and confirms the stream is absent from ordinary `os.scandir()`.

Actual O57 `Builder.build()` returned **success** with a genuine revision-24 archive. Real `CMPCT.verify()` passed. A regular child file's **4,096 bytes** reconstructed exactly. The nested directory was reconstructed, but its 676-byte named data stream was **absent**. The original named stream remained intact in the source. Observed archive SHA-256: `aaa9aab1f43a3c6997d5ee57445b7f1cb5afb0f3f9d37562ae6d5c419c0d9fd1`. The evidence log explicitly printed `O61D_DEFECT_CONFIRMED=directory-stream-omitted source_bytes=676 restored_stream=missing`.

Original regular-file O57 checks were retained unchanged: named regular streams refuse; hardlinked named regular streams refuse without overwriting a preexisting output; supported regular hardlink tree reconstructs exactly/deterministically. Plain nested directory also reconstructs exactly.

**Actual JUnit: 5 PASS / 0 FAIL / 0 ERROR / 0 SKIP** (`O61D_REAL_TESTS=5`), 0.12 seconds after dependencies installed. All five test cases executed. This is a **green scientific falsifier of a red product behavior**; never reinterpret as the product passing losslessness.

## Scientific decision and strong counter-controls

- Primary claim confirmed for a stable named-stream nested directory on Windows 2025 NTFS, not a post-stat race.
- Simpler explanation that the runner cannot create or enumerate directory named streams is refuted by successful direct file read and independent native Win32 enumeration.
- Positive baseline plain directory and inherited O57 regular-file controls pass.
- A genuine cryptographic archive checks what was stored; it does not prove the selected physical source tree was completely inventoried. No hash collision or Reader corruption was observed.
- **No additional release/product/compression credit** and no performance measurements were made. All original O57 gate debt persists.

## Integration boundary / next cheapest executable target

The O57 `refuse_unsupported_named_streams` guard is called only after regular-file classification. A nested directory is appended to K_DIR and recursed without inventory of its ADS. A later product fix should check nested directories *before* publication, preserving ordinary directory recursion and existing file/hardlink behavior. Unlike files, NTFS directories have **no default unnamed `::$DATA` stream**, so directly applying the current regular-file guard to all directories may reject valid ones if empty stream enumeration returns end-of-file. Verify Win32 empty-directory enumeration before designing the helper. The separately important source-root directory has no explicit K_DIR row and requires an explicit source semantics decision, not an accidental scope expansion.

Coordinate any Builder/helper modification with O57 owner #413 and Builder O50 owner #405. Do not overwrite branches; do not weaken O47/O48/O50/O57 courts. Candidate eventual promotion requires installed Windows/Linux/macOS execution, exact stable archive identity, original benchmark gates, Windows directory-with/without-stream positives/negatives, and realistic per-directory Win32 enumeration CPU/wall resource cost.

**Counterfactual:** the cheapest transferable discriminator is independent physical stream inventory before/after archive creation; a mere successful checksum over captured bytes cannot establish source completeness. This episode does not by itself justify editing the general Discovery Engine or `STATE.json`.
