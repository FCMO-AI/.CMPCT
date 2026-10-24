# O0/O1: APFS normalized-namespace alias falsifier and bounded extraction admission

Date: 2026-10-24
Status: prospective preregistration; product/format claim unearned
Baseline: `FCMO-AI/.CMPCT@agent/v031-development`, exact source `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, released v0.30.0, format revision 24.
Separate active owner: PR #332 handles Win32 device/stream/drive/case names; do not overwrite that branch.

## Exact question and prediction
Can two distinct authenticated CMPCT member names address a single physical inode on a normalization-insensitive macOS filesystem while the extractor accepts the tree without a collision warning? Apple's APFS guide states APFS is normalization-insensitive on macOS even for case-sensitive variants. Predict the unchanged baseline accepts `café` (U+00E9) and `cafe\u0301` (U+0065 U+0301) as two logical keys, then both map to one physical filesystem entry. This would violate one-to-one tree reconstruction, without proving arbitrary code execution.

## Falsifier / controls
1. Host independent stdlib `unicodedata.normalize("NFD", x)` gives identical canonical equivalence; preserve a byte-distinct source spelling witness.
2. On actual macOS hosted filesystem, test physical NFC/NFD alias with `os.path.samefile`; on Linux show source spelling separation.
3. Baseline product court: run actual `CMPCT.extractall` on two synthetic already-preflighted directory rows, require it to reject ambiguous Mac spellings **before member writes**. First run against exact original development branch and preserve red if observed. Also test implicit parent alias and plain case alias.
4. Valid single-directory and Linux two-name positive controls must still pass.
5. Only if baseline falsifies, add a destination-only macOS check using NFD+casefold prefix keys and strict UTF-8 encodability, with no wire/parser/format mutations. A case-sensitive APFS or Mac volume may allow more names; conservative rejection must be documented as carrying cost.
6. Re-run the **same** test source on the candidate, with actual macOS + Ubuntu workers; isolated pytest avoids the inherited global Linux-only research conftest.

## Bounded product path and costs
Any new check costs O(total lexical path components) normalizations and memory per distinct prefix. Host filesystem behavior can differ by volume; Unicode Python normalization is not a formal complete model of Apple's Unicode-9.0 comparator. Accept limited safety claim, never universal APFS namespace security. Do not use the candidate as release evidence without general tests, native/platform parity and benchmark. Existing destination symlinks/TOCTOU (#265), preexisting names, and directory inode mobility are separate unclosed risks.

## Stronger controls and kill condition
Full filesystem-sensitive reference without prediction would cost more and risks writes before the oracle. The stronger simpler control is the existing unchanged portable logical parser: if macOS physically preserves both NFC/NFD names as distinct on the tested host, the predicted bug is not reproduced there and product promotion should stop pending a representative host. An unconditional global NFC normalization would alter accepted POSIX archive names and is rejected.

## External provenance
Apple APFS FAQ: https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/FAQ/FAQ.html
