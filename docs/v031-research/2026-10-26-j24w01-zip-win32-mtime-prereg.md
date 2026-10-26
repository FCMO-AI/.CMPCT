# J24W01 — preregistered ZIP namespace × Win32 timestamp composition

Date: 2026-10-26
Status: PROSPECTIVE — committed before source/test/workflow composition.

## Authority and baseline
- Published floor: CMPCT v0.30.0; on-disk revision 24. No promotion or version bump.
- O160 ZIP namespace parent PR #499 at `03a82b5c1227ed37733d45c8ebe661dd871f5236`; Reader Git blob `f29885574c892a2c2dd819f13b7595d1af59a903`. Its independent fixed-r24 ZIP oracle is `research/o160_zip_name_parity_court.py`; Linux/macOS positive; original Windows direct extraction with metadata failed at unsupported no-follow `os.utime`, before ZIP export (Actions 40280705125).
- Independent O167 owner PR #504 at `841c32d435494f6e4d83c44cd00a1a2f8f7ab148`; its Win32 handle implementation `src/cmpct/_win32_times.py` is exact Git blob `70308f454c74fad7b247db6ee36aa8cc7d38c99c`. Its separate 3-host court 40293736155 measured correct file+directory physical mtime and non-following final reparse checks.
- The two owner branches are independent. This branch composes existing mechanisms without changing either owner branch or historical source-identity validators. It does not claim that O149 staging defeats O157's concurrently replaced temporary-file name (PR #497).

## Primary falsifiable question
Does transplanting O167's unchanged handle-based Win32 regular-file/directory mtime fallback into O160's unchanged canonical ZIP member-name Reader allow the original *independent O160* archive/ZIP filesystem parity test to finish successfully on Windows, while preserving O149 export-failure atomicity, O167 physical mtime fidelity and POSIX behavior?

**Prediction:** fixed independent r24 RAW/Zstd/Deflate inputs have correct names and bytes under both ZIP serializers on Windows, Ubuntu and macOS; 18 positive ZIP cases plus 3 duplicate canonical-name refusals per host; original O167 test preserves physical mtimes within its 3 s predeclared tolerance and rejects final reparse pivots; O149 inherited tests continue to pass. All test source files remain unchanged except for their presence in this composed branch.

**Disproof/kill:** any authentic golden reconstructs to a different tree, archive SHA drift, a Win32 timestamp is not restored or an external reparse target is changed, O149 previously passing failure-preservation control regresses, source custody does not match the two original owners, or generic CI discovers a novel product failure. Historical workflow SHA guards rejecting a *different* Reader source are not product evidence; keep those guards unchanged and report them separately.

## Alternatives and Pareto comparison
1. Modify original O160 frozen workflow to accept any Reader: rejected as weakening a source-history identity guard.
2. Work around failing extraction by setting `metadata=False`: rejected; masks a real filesystem-fidelity defect.
3. Duplicate O167's native Windows implementation: rejected; reuse the original exact helper blob and transplant only its scoped integration method.
4. Modify O160's ZIP writer or r24 index to fix the Windows failure: wrong causal subsystem.
5. Selected: isolated composition branch with byte-identical O167 native helper, original O160/O167 independent courts, newly source-bound hosted acceptance and unchanged O149 negative controls.

## Evidence ladder and resource/accounting
- O0 source analysis: confirm the original failed Windows call site is precisely regular/directory `os.utime(... follow_symlinks=False)` and the O167 Win32 leaf handle is the minimal adopted correction. Treat symlink timestamps as best effort and never follow a symlink to fake success.
- O1 source-exact hosted tests: run installed candidate outside checkout on Windows/Linux/macOS, independently authenticate original O160 and O167 test blobs, source/fixture identities, and physical timestamps; retain per-host raw logs and JSON/JUnit.
- O2 full product parity and ZIP publish safety still separately required. Neither reduced export size nor faster operations are predicted. Additional Win32 file-handle opens per restored item are unmeasured cost. Archive bytes, metadata, O149 staging/inode changes, O157 race, O151 permissions, timing, RSS, temp-I/O and crash durability remain outstanding.
- The dedicated composition workflow must retain results on failure and distinguish test functional failure from source/CI/custody failure. Exact hosted test success is not a release gate.

## Concurrent ownership and continuity
Read active PRs before implementation: #499 (ZIP names), #504 (Win32 mtime), #492 (ZIP staging), #497 (stage-name identity negative), #502 (ZIP-only Windows acceptance). This work is a deliberately bounded cross-PR integration, not a replacement owner or a new competing timestamp mechanism. Do not force-push, alter PR owners, rewrite frozen benchmarks, change format/version, or merge.
