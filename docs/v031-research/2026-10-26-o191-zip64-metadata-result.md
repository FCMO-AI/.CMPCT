# O191 — ZIP64 fallback calendar parity: result-bearing synthetic dispatch court

Date: 2026-10-26
Status: **SCOPED POSITIVE; unmerged draft product patch; no genuine >4GiB product acceptance**.
Source branch: `agent/phased3-v031-o191-zip64-dos-metadata-20261026`.
Preregistration commit: `8bd95904191b2b43d351adcf13aa243799f5f118` **before** source patch `9873883087616d78fda4992addff12400ae66c50`.
Parent owner O190: PR #518, at source `00896f9aeded487e44f92dfae3de4aba59a9dcbf` (Reader blob `4af0223af96eb725ea164d9d47812bfa4898045e`).
Result-bearing implementation HEAD: `8d2bc3f5be466a62a09385e9f288067f1a50cc1b` (installed Reader normalized SHA-256 `72e0a1f4d5510e5bcdb7339d24df830d20018f1f6982ac2ad3be9db559371ab8`).
GitHub Action: https://github.com/FCMO-AI/.CMPCT/actions/runs/40339431574, **four of four jobs SUCCESS**.

## Question, baseline and simplest control

The ordinary fast ZIP writer already uses O190's full signed DOS calendar. The distinct fallback activated when any declared file size >= `0xffffffff` directly constructs `ZipInfo(name)` and never assigns a member datetime. Python 3.12's `ZipInfo(name).date_time` is fixed at `(1980,1,1,0,0,0)`, **even when an authenticated CMPCT file has an ordinary year-2000 mtime**. This is a real source-level defect prediction, not a demonstrated genuine 4GiB ZIP artifact.

O191 adds a constant-time conversion of the *existing* O190 `_zip_dos_time(mt)` packed bits to `ZipInfo.date_time` immediately in that fallback path. No second date algorithm, no change to O190 fast writer, no new on-disk format.

## Instrument and actual three-host evidence

Linux Ubuntu 24.04 built three authentic source CMPCT revision-24 files using the unchanged O190 producer; source archives and SHA-256 were transferred intact to installed CMPCT Readers on **Ubuntu 24.04, macOS 14 and Windows Server 2022**. Each receiving job verified its Git HEAD and installed Reader bytes against the Git object. Each then changed only `reader.files[0][4]` **in memory** to `4294967295`, selecting the fallback despite a true 38–40 byte payload. The name lookup still used the original authenticated row. This is deliberate **synthetic dispatch, not a genuine 4GiB payload**.

| Source case | CMPCT original SHA-256 | Expected / observed ZIP date (all 3 hosts) | ZIP bytes | ZIP SHA-256 (all 3 hosts) |
|---|---|---|---:|---|
| signed 1960 | `93fecf0d240a59619a612d1139ca0207be4a41f1b42f35ade453317d18cb0e7c` | `1980-01-01 00:00:00` | 152 | `b06b04d4301ac1960f7a3d2f95c890fb584a35d018279bb523a0ef3afd679fca` |
| ordinary 2000 | `dc0c8c34cb05bc3da84be36c92f1406daf5355dffb0870c8da2e39e03dfe22d3` | `2000-02-02 00:00:00` | 154 | `1d25f9b2e9f094893f06d6cb7422b41271bc2a6dfd18ed183c070264aadbb95f` |
| signed 2110 | `9df86c0d0141cb16eaff8dd198c5c67d3889f4bfa0999e641ccc847895e05834` | `2107-12-31 23:59:58` | 154 | `b54ae76141178850b986315c8a964f6dae1911c5c20c7eb34e6d4441533fcafa` |

All nine independent host×date cases passed byte-exact payload reconstruction, member list, independent stdlib ZIP CRC and calendar comparison, and original CMPCT SHA preservation. Cross-host emitted ZIP SHA was identical for each case. The ordinary-2000 case is the **decisive discriminator**: baseline `ZipInfo` would output 1980; candidate emitted 2000.

Source-run artifacts (raw structured JSON): 
- Ubuntu: https://github.com/FCMO-AI/.CMPCT/actions/runs/40339431574/artifacts/12658452326
- macOS: https://github.com/FCMO-AI/.CMPCT/actions/runs/40339431574/artifacts/12658108347
- Windows: https://github.com/FCMO-AI/.CMPCT/actions/runs/40339431574/artifacts/12657763907
- Linux producer CMPCT bytes/receipts: https://github.com/FCMO-AI/.CMPCT/actions/runs/40339431574/artifacts/12657437590

Independent algebraic local control (separate from installed product): 12,000 seeded in-range DOS date bit pack/unpack identities checked, 0 mismatches; three examples also round-tripped through Python's ZIP reader. This is supportive derivation only.

## Adversarial review and bounded interpretation

- The method **does not allocate or test real >4GiB data**; the archive emitted by the forced path is a small ordinary ZIP. It does **not** establish genuine ZIP64 huge-member correctness, ZIP64 central-directory interoperability, streaming or memory requirements.
- Source-exact `CMPCT.read(name)` builds a complete `bytes` payload; the fallback calls it and then `z.writestr`. Thus actual >=4,294,967,295-byte regular members can demand at least one such full logical member materialization, before accounting for temporary copies. A genuine giant-member stress test is a **separate charged resource decision** and was not attempted.
- ZIP name canonicalization, symlink metadata, output publication atomicity, hostile ancestor changes, Win32 extraction metadata, ACL/xattr and sparse layout are separate product contracts. O191 does not change them.
- No measured delta for CPU, RSS, creation/extraction wall, temp I/O, compression ratio, cold opens, selective reads or dependency depth; no claim of performance advantage.
- The original O184 negative and O190 source/prereg remain intact. Parent O190 tests and normal generic CI must be reconciled before merge; SUCCESS in this narrow court never authorizes release.

## Decision, counterfactual and next action

**SCOPED RESULT:** `ZIP64_FALLBACK_CALENDAR_FIDELITY_FORCED_BRANCH_PASS` on three installed hosts, with exact source identity and authentic small revision-24 archives. The simplest earlier discriminator was the source-level absence of `ZipInfo.date_time` assignment: a one-line inspection predicts unconditional 1980 and a tiny synthetic dispatch makes that prediction falsifiable without unsafe multi-gigabyte materialization.

**Next:** owner O190 can reconcile/cherry-pick this constant-time fallback amendment after reviewing exact-head CI. For a claim of genuine ZIP64 export, build a streamed, resource-bounded, same-input product court rather than multiplying fake-size fixtures. No discovery policy/STATE change, merge, release or version bump.
