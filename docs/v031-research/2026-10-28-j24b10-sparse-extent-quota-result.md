# J24B10 — Signed sparse physical extent overrun of logical extraction quota

**Decision:** `CONFIRMED_SPARSE_SIGNED_EXTENT_QUOTA_OVERRUN` — published CMPCT v0.30.0/r24 extraction defect, not a product fix. **Measured 2026-10-28 UTC.** Research PR [#700](https://github.com/FCMO-AI/.CMPCT/pull/700), product issue [#701](https://github.com/FCMO-AI/.CMPCT/issues/701).

## Source, frozen prediction and scientific scope

The exact published main source is `80c358f8824ec1b20d349c92ed94c898090969b0`, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. First preregistered prediction was committed at `36efdecc174aeff094e132804e7a7fdf8a7ac7d7` **before** any scientific instrument. Exact result-bearing science code HEAD: `ed6376252e943cb4a9535d5b9cdde65e273834f8`.

The [first exact-head scientific GitHub Actions court](https://github.com/FCMO-AI/.CMPCT/actions/runs/40760729066) completed **SUCCESS** in 3/3 actual installed-wheel jobs: Ubuntu 24.04, macOS 14 and Windows 2022, Python 3.11. Each job proves source HEAD and imports installed CMPCT from the installed package, not an oracle-proxy Reader.

**Interpretation:** hosted success is the observation of a **released-product failure** under deliberately SHA-consistent hostile metadata. It is not evidence that the published Reader is safe; no production change, merge or release was performed.

## Exact physical mechanism and controls

A deterministic builder-independent revision-24 positive archive stores one logical `sparse.bin` of **16,384 bytes**, a single ordinary RAW physical blob of **8,192 bytes** and a sparse extent `[4096,8192,[0]]`. All index/physical SHA-256 and CRC32 values are authentic; file digest is the SHA-256 of the correct logical content.

The mutant changes **only** the index extent from `[4096,8192,[0]]` to `[16383,1,[0]]`, recompresses and rehashes both primary/tail index copies, and retains **identical** original physical blob bytes and member `row[4]=16384` + original full-file SHA-256. SHA-256 is unkeyed archive self-integrity, **not** an external digital signature.

| Operation | Original | Signed malformed extent |
|---|---|---|
| Strict `preflight_archive` | Accept | **Reject**: sparse extent 0 length mismatch |
| Ordinary `CMPCT.read` | 16,384 correct bytes | Reject logical SHA/length |
| Ordinary `CMPCT.verify` | Pass | Reject logical SHA/length |
| `extractall(max_bytes=16383)` | Refuse before member output | Refuse before member output |
| `extractall(max_bytes=16384)` | 16,384 correct bytes | **Success, 24,575 output bytes** |
| Overrun of declared max_bytes | 0 | **8,191 bytes** |

The released `S_SPARSE` extraction code first `ftruncate(fd, size)`, then writes each complete physical `_blob(idx)` at `off` with `os.pwrite` (or seek/write fallback). It does **not** check that the total actual decoded physical bytes equal the authenticated extent length `ln`, that writes remain inside file-row declared size, or that the full-file SHA matches before publishing. A late write at offset `16383` of an `8192`-byte blob extends the file to exactly `16383+8192=24575` bytes. This is not a timing/measurement or index-validator defect; the standalone stricter validator already correctly refuses it.

The stronger simpler control is the existing strict preflight's exact extent-physical size binding, but invoking a separate pathname preflight before ordinary Reader extraction is **not** an automatically sound fix because of source identity/TOCTOU differences. An integrated same-open authenticated effective index and safe staged publication are the relevant ownership boundaries.

## Hosted evidence and independent verification

The original hosted [run #40760729066](https://github.com/FCMO-AI/.CMPCT/actions/runs/40760729066) retained original archives, mutants, actual output files, exact source HEAD and two independent JSON reports.

| Host | Original artifact | ZIP SHA-256 |
|---|---|---|
| Ubuntu 24.04 | [#12847113499](https://github.com/FCMO-AI/.CMPCT/actions/runs/40760729066/artifacts/12847113499) | `3df8a1a9da9380a326b05d7ccc5ec3b27a4ca3c66db0f0ae7b99c4872875a831` |
| macOS 14 | [#12847368125](https://github.com/FCMO-AI/.CMPCT/actions/runs/40760729066/artifacts/12847368125) | `7dd83bed99337676598baa770f0f3e273a32d80db99a755be8c3f2e2ded26672` |
| Windows 2022 | [#12847992594](https://github.com/FCMO-AI/.CMPCT/actions/runs/40760729066/artifacts/12847992594) | `8bc59165f2bffea596f6e40414d4c893a3999c70db49a648e52c17e65ce8ba7f` |

- Hosted detached `research/j24b10_sparse_quota_referee.py` uses independent raw frame/index parsing, Zstd package, CRC/SHA, member-output reconstruction and **4/4 deliberately corrupted evidence rejection per host**.
- A **third separately implemented local audit** independently downloaded all three ZIPs and parsed raw frames using `ctypes/libzstd`, stdlib struct/hashlib/binascii and MessagePack (not either hosted candidate/referee). All three original archives are **byte-identical** across systems; all three mutated archives are byte-identical, as are the actual extracted original and hostile outputs.
- The physical record SHA-256 is `3327af305bc2f7a6397c98ccbd2213da46145e0691a11d7c26c26054bae9becd`. Whole original archive SHA-256 `d36da9b74217904e7e957ca03672bce857350b3b26faaacc0a376c89ed21ce61`; mutant `50277518ace719f00dcd085ef274fd2df3c1b80eac19989cd31aa3b158d608d5`. The cross-host output physical byte comparison had **zero discrepancies**.
- Third-root auditor rejected **12/12** distinct corrupted host copies (one receipt scalar, one physical source record, one index byte and one output byte per OS). Independently persisted third-root receipt JSON SHA-256 `75f774e5c04244e0346c25d2e7f1582c549053250eb5d5549a7829bbe3feb14c`. The receipt and original host artifacts are retained outside Git; the original exact-host archive references above make the result reproducible.

### Epistemic qualification

This experiment proves **one exact failure geometry** across three operating systems; it does not claim arbitrary amplification, general prevalence, remote exploitability, privileged code execution, actual allocated disk-block amplification, or safety of any remediation. All three runs used the same deterministic input bytes; they establish cross-platform replication, not an independently sampled natural corpus.

## Discovery, counterfactual and integration

The current `docs/discovery/STATE.json` on main is a stale v0.30 allocator; PR #574 owns its prospective reconciliation, so this PR deliberately does **not** overwrite it. The local concurrency protocol file was not present on checked branches, and the named #255/#270/#573 sparse + #569 composite Reader and #609 physical owner codeowners were left untouched.

**Decision-changing discriminator:** before developing another quota-accumulation fix, compare every physically materialized S_SPARSE extent's declared length against the authenticated referenced blob lengths, and ensure staged verified output can never extend beyond logical bounds. A direct source/length derivation would have predicted this overrun before the full three-host court, but only an actual installed Reader and independent SHA-consistent archive prove the concrete published behavior. This is a reusable test ordering lesson, **not** evidence to modify discovery policy itself.

Existing [#572](https://github.com/FCMO-AI/.CMPCT/issues/572) proves sparse full SHA/early truncation; [#689](https://github.com/FCMO-AI/.CMPCT/issues/689) proves negative symlink size; [#693](https://github.com/FCMO-AI/.CMPCT/pull/693) and [#697](https://github.com/FCMO-AI/.CMPCT/pull/697) prove nonnegative alias/symlink length undercount even after #690. This case is separate: **declared member size itself is nonnegative, correct and unchanged**, while the signed sparse-extent geometry lies. Therefore #690 alone and composition #699 cannot be considered full logical quota repairs.

## Product acceptance and work still owed

Scientific court: **PASS/defect confirmed**. Product promotion: **BLOCKED**. Candidate fix: **NOT IMPLEMENTED**. CI generic, version, frozen benchmarks, recovery, release, performance, hostile destination concurrency and actual large sparse RSS/temp-I/O are independently governed. A real fix should maintain exact zero/holes, full SHA, format r24, source/destination inode ownership and no-clobber semantics, account all logical bytes and validate before output can be published. Only cross-kind source-locked three-host behavioral tests and full incumbent performance gates could earn product credit.

No `README`, product implementation, `STATE.json`, parser policy, release identity, benchmark comparator or threshold was modified by this scientific result.
