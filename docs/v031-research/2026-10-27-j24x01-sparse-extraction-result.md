# J24X01 — Authenticated sparse extraction contract falsified on shipping r24

Date: 2026-10-27 UTC. **Science-only. No product source, format, version, benchmark, comparator or release change.** Preregistered first at `29d6a0b220d6ac4ff1b8b26d6dca71463fb749cd`, then authored the instrument `644a2a7f4c992be766be1615b9953e086d125929`. Executed against unchanged `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, validation blob `51c2849061f99a4afeddb7666956b24566ce7de0`.

## Decisive hosted evidence

- Exact instrument/workflow [GitHub Actions run #40453070210](https://github.com/FCMO-AI/.CMPCT/actions/runs/40453070210) on source HEAD **`787820cca5df6769d76cb4cedbf4c36b287d46ef`**: **SUCCESS** Ubuntu 24.04 / macOS 14 / Windows 2022 (3/3).
- Independently installed package on each host, installed module content byte-identical to pinned shipping Reader. `src/`, `native/`, `benchmarks/`, `tests/` unchanged vs release. Mainline r24 product remains v0.30.0.
- Original artifacts: [Ubuntu #12710819501](https://github.com/FCMO-AI/.CMPCT/actions/runs/40453070210/artifacts/12710819501), [macOS #12711920494](https://github.com/FCMO-AI/.CMPCT/actions/runs/40453070210/artifacts/12711920494), [Windows #12711017336](https://github.com/FCMO-AI/.CMPCT/actions/runs/40453070210/artifacts/12711017336). ZIP SHA-256: Ubuntu `64e25897bd850e27dd79c1718b680f29e4a58f68b5a7fa643d9255b54344dd2f`, macOS `f316eb6b646374cf15eae8b5a6e488f81f2428ded5df92b19f965e9817ab2cc6`, Windows `14f11e182e8ab4b8a005e91a7ce2214258b2b378c4ed2e478ff9128f9c5cc4c4`.
- Downloaded original ZIP evidence was independently replayed with a separate stdlib auditor. It recomputed expected hashes from newly constructed independent `ABCD`/zero/canary bytes, checked source Git blobs and installed hashes, preflight/read/verify/extract outcomes, archive-source conservation, destinations, stdout and cross-host archive byte identities. **273 assertion checks PASS, 0 discrepancies**. Six deliberate receipt corruptions (digest, output, exception, positive control, case count, installed source hash) were independently rejected **6/6**.
- Negative discovery captured as [issue #572](https://github.com/FCMO-AI/.CMPCT/issues/572). These facts do not assert external signature forgery, concurrent race or deployed exploitation.

## Prospective predictions vs actual outcomes

All archived root and tail indexes have correctly computed index SHA, actual physical records have correct lengths and intact data unless the *declared* mutation is applied; the strict header-only preflight admits the structurally valid index and physical header.

| Synthetic file | `read()` | `verify()` | `extractall()` | Destination postcondition | Hosted OS |
|---|---|---|---|---|---|
| Valid S_SPARSE with leading/trailing holes | accept | accept | accept | 12 exact bytes, correct logical SHA | 3/3 |
| Unrelated valid S_BLOB | accept | accept | accept | 4 exact bytes, correct SHA | 3/3 |
| S_SPARSE with wrong, *authenticated* logical SHA in index | **reject** `file integrity failure` | **reject** | **success** | 12 correct assembled bytes but **not the declared logical SHA** | **3/3 reproduced** |
| S_SPARSE with one corrupt physical RAW byte, existing canary | **reject** `blob integrity failure` | **reject** | **reject** | preexisting canary was **destroyed**, replaced with 12 zeros | **3/3 reproduced** |

Exact deterministic data hashes:

- Genuine 12-byte sparse logical payload `000000004142434400000000`: `abe3586bf6a5079fa6b16e37c225f7ebbb8d2cacfc56e53223bb7df0846883a6`.
- Wrong index logical SHA: `d91f759e74ed...` (full digest in original JSON).
- Failed corruption extraction output: SHA of 12 zero bytes `15ec7bf0b507...` (full digest in original JSON).
- Preexisting canary is not preserved in either case because extraction writes into/truncates target directly; the test only requires failure preservation in the *corrupt* case.

## Root cause and distinction from other active work

Source `extractall` S_SPARSE branch uses `os.open(full, O_TRUNC)`, `os.ftruncate(fd,size)`, direct physical writes. It does not calculate and compare the full file's SHA-256 from row `h`; read/verify do. S_CHUNKS/S_CDC already have separate temporary verified publication; O212/O214 fix **structural extent geometry admission** but do not retrofit sparse extraction verification. J24P03/P04 concern attacker-mutable namespace identity after publication and do not explain this static corruption scenario. No concurrency, permissions race or malicious syscall interposition is needed.

## Charged prospective product route — avoid a false cheap fix

An apparently simple fix, stream the logical SHA-256 while reconstructing sparse holes into a private temporary inode, exports CPU work proportional to the full **logical size**, not only stored extents. A separate, **local micro-only** Python 3 / OpenSSL SHA-256 lower-rung probe (three repetitions; 1 MiB reusable zero window) measured:

| Hole logical bytes | Median SHA CPU/wall | Median `ftruncate + pwrite(4 B)` wall |
|---:|---:|---:|
| 8 MiB | 4.94 ms | 0.0169 ms |
| 64 MiB | 42.90 ms | 0.0266 ms |
| 256 MiB | 175.94 ms | 0.0267 ms |
| 1 GiB | 674.00 ms | 0.0279 ms |

The comparison illustrates an asymptotic materialization cost and is **not** a fair full CMPCT product comparison: it does not include stage publication, blob decoding, filesystem flushes, read/write amplification, metadata or actual workload. It warns against calling SHA-over-holes "free". The strongest simple control is existing low-CPU sparse extraction, which is unsafe in failure/corruption scenarios. All genuine repair candidates must account for unchanged exact bytes, O(logical bytes) hashing CPU for current SHA commitment, RSS, temporary physical I/O, keep-holes-sparse behavior, destination commit semantics, supported OS/filesystems, resource limits and full-size 4GiB cases.

A more radical authenticated **physical proof of logical zero-runs** might avoid that CPU, but cannot be silently substituted for the existing SHA-256 full-file commitment without new wire/proof semantics and compatibility law. No new format mechanism was built or proven here.

## Decision and next executable target

**New product defect confirmed, no fix promoted.** Issue #572 is the owner of this newly isolated correctness seam; owners of O212/O214 geometry and J24F11/Issue #528 inode publication remain independent. Highest-leverage next lane: implement a bounded-memory sparse verified staging candidate in its own branch, preregistered against the unchanged above *negative* tests, then measure exact r24 geometry/corruption/overwrite guarantees and large-file performance before any merge. If SHA zero-run CPU is prohibitively costly on very large sparse objects, preserve the negative and reopen the proof/reconstruction-model design rather than weakening integrity or shrinking hostile fixtures.

Discovery Engine: primary question decided (both predictions confirmed); no concurrency collision detected with same narrow sparse-extraction SHA/failure boundary; cheaper discriminator was source-level observation followed by two tiny archived cases; policy-level amendment **not** earned. `docs/discovery/STATE.json` is a staleable, already dated cache and was not used as a lock or overwritten. **Credit:** science + exact-source evidence; **product/release credit:** zero.
