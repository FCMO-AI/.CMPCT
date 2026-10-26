# O171 result — exact Linux r24 archive authentic on Win32; inherited Reader extraction fails

Date: 2026-10-26 UTC. **RESULT BEARING / NEGATIVE**. Preregistration: `44801290dc9f67b4346880a30c277a66c2914024`; no prediction rewritten. Exact tested source head: `7d38af7b9670c2cd3bba837368d519b3c08fb1d0` (O168 parent + O171 evidence instrumentation, no shipped source mutation).

## Direct raw evidence

- GitHub Actions workflow: https://github.com/FCMO-AI/.CMPCT/actions/runs/40302748225
- Source-origin Ubuntu job `121504664439`: **SUCCESS**. Original archive artifact `12641201967`.
- Independent Windows Server 2022 job `121504911636`: **FAIL** at installed Reader extraction. Original Windows JSON artifact `12640424784`. The workflow was intentionally not turned green after the failure.
- Binary source revision-24 archive: **1,941 bytes**, SHA-256 `17d3560cb175bf4593974059c01d03f2706fd3c4f8743813162772e6682ad742`. Producer receipt and Windows downloaded binary **matched byte count and SHA**. No Windows Builder ran.
- Source hash reconciliation: Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, transactions `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`, O155 independent witness `0bef46e8d1944ff327063c66edc9bbc29fa58481`. All Windows checkout blobs matched producer; package installed outside worktree.
- Windows `cmpct verify`: **PASS**, "verified 8 logical files", 111.72 ms measured whole subcommand.
- Windows `cmpct extract`: **FAIL**, return code 1 after 114.803 ms, genuine traceback:
  `reader.py:474 os.utime(full, ns=(mt, mt), follow_symlinks=False)` raised **`NotImplementedError: utime: follow_symlinks unavailable on this platform`**. Original Reader catches only `OSError` at this site, so it propagates.
- Native Windows host capability micro-oracles: successful regular-file hardlink, file symlink, explicit directory symlink, **and default directory symlink with existing target**. Thus **lack of symlink privileges and missing `target_is_directory` are not demonstrated causes of this run's failure**. Python's published docs support auto-inference when the target exists. These controls were recorded before evaluating the product outcome.

## Disposition and causal bounds

P1 (source/transport identity): **PASS**. P2 (installed Reader verify): **PASS**. P3 (complete 10-entry physical Windows extraction): **FAIL before semantic tree comparison**. P4 (archive unchanged after successful extraction): **NOT MEASURED**, since extraction returned an exception before the post-extraction check; do not project a positive from pre-read SHA.

This is a real cross-host interoperability failure in the **specific inherited O168 Reader**. It does **not** establish corruption, a bug in all newer Readers, unsupported NTFS symlink capability, bad r24 source bytes, or universal Windows archive rejection. The test did not and must not mask `NotImplementedError`, change source assertions or loosen physical fidelity requirements.

**Important recovered stronger prior work:** Current independent O69 PR #425 and O167 PR #504 `src/cmpct/reader.py` already catch `(OSError, NotImplementedError)` for the symlink metadata `utime(..., follow_symlinks=False)` call. Their exact Reader blobs are `1122b1d80f2cf76faab8ed2d4e8cb2e346d85e27` (O69) and `c50522443b88e78ee2cc8361c4ec2bddbb4f0bbb` (O167). Consequently **do not create another parallel catch/mtime implementation**. Reuse the existing owner patch and execute a cross-branch same-archive interoperability court with explicit separate producer/reader source fingerprints. The existing O171 same-source negative should remain frozen.

## Counterfactual / decision

A cheap source inspection of the Reader `os.utime` exception handler and the already-open O69/O167 branch would have identified this probable host gap before a two-host run. But only the real installed Windows run established that this exact archive/host reaches the handler and aborts. The discriminator generalizes to Python cross-host APIs: documented `NotImplementedError` is distinct from `OSError`, and a handler may need both. No Discovery Engine policy rewrite earned from this single episode.

## Outstanding debt

The stronger existing O69/O167 Reader has not yet been verified against **this exact Linux-produced archive** in Windows. That retest must preserve full 10-entry kinds, file bytes, symlink targets/usability and physical hardlink grouping; a green verification alone is insufficient. No ZIP/Deflate compression speed, stored-byte improvement, portability beyond one Windows host, crash/TOCTOU safety or v0.31 promotion is claimed. Independent generic CI and release/economics gates still apply.
