# O93 — descriptor-bound Builder output: genuine hosted result

Date: 2026-10-25 UTC. Scope: v0.31 **draft** investigation; not merged and not published. Released v0.30.0 / r24 intact.

## Source / prereg / causality

- O90 source parent `1beb733da61da8e1c562e7c3190b1f18f1cc45d1`, Builder blob `bfb37fcd06e6ff05742606ece365348150f477fc`.
- Immutable prereg `c62a27d89c2618691dd0354c55558032ce1cccc1`.
- Candidate Builder blob `7214a46b781bb10051e6782ba7731989ebf05edb`.
- Result-bearing exact head `53395e6c234dbb16d8e6d6924a73ebf3f6720298`; [hosted O93 source-bound Actions run 40212143956](https://github.com/FCMO-AI/.CMPCT/actions/runs/40212143956).
- Genuine inherited O91 negative: O90 postscan symlink to a one-link source overwrites original, FIFO pivots can block >7s, [run 40209092155](https://github.com/FCMO-AI/.CMPCT/actions/runs/40209092155). O93 prevents these in the controlled two-POSIX-host replays; an oracle asserting failure of the old product is not falsely treated as a candidate green.

## Direct installed product evidence

| Runner | PASS | justified SKIP | FAIL | genuine court |
| --- | ---: | ---: | ---: | --- |
| Ubuntu 24.04 | 58 | 7 | 0 | SUCCESS |
| macOS 14 | 58 | 8 | 0 | SUCCESS |
| Windows 2025 | 45 | 21 | 0 | SUCCESS |
| TOTAL | 161 | 36 | 0 | 3/3 SUCCESS |

The original upstream O80/O81/O84/O90 tests remain unchanged, along with source-exact O84 historical complete archive parity. New O93 tests cover: regular create/overwrite Reader full verify; after-scan symlink-to-single-link source refused without source mutation (Linux/macOS); after-scan FIFO refused without blocking (Linux/macOS); initially absent symlink path attack refused exclusively; pre-existing output inode/hardlink/symlink/xattr and POSIX permissions preserved; read-only path refusal (POSIX); after-scan regular inode replacement rejected on **all three** OS; initially absent regular path race rejected on **all three**. POSIX platform skips are not counted as validation of Windows FIFO or xattr APIs.

Historical O84 identical complete archive SHA from O90/O93: Linux and macOS `d31f77aad7bc94f6354dd4b9299020663c20be3d32b8c348cdd0c5c4c911c1e3`; Windows `490b1f6e6672bc173083d65037df5e11e92fb0f0558d24ab25d4b47eddc865ee`.

## Source-exact whole-Builder economics: micro product rung, not release credit

A new instrument runs the **authentic Git-blob verified O90 Builder source** against the O93 installed candidate in five alternating same-input warm-process A/B repetitions per fixture, preserving individual raw wall/CPU measurements and whole-archive equality in hosted `o93-evidence/economics.json`. Single-worker reproducible-mode small public synthetic fixtures only. Measured median wall milliseconds:

| Host | 25 tiny source files O90→O93 (delta) | 3 mixed files O90→O93 (delta) |
| --- | --- | --- |
| Ubuntu | 3.282886→3.290199 (+0.007313) | 2.498642→2.545330 (+0.046688) |
| macOS | 2.786250→2.574375 (-0.211875) | 3.283958→2.075917 (-1.208041) |
| Windows | 8.5460→7.1752 (-1.3708) | 5.7622→5.3754 (-0.3868) |

No speedup claim: timing noise and extremely small counts dominate; Windows `time.process_time_ns` yielded quantized ~15.625 ms/zero readings. Complete archive bytes identical on every pair, 1284 B (tiny25) and 132249 B (mixed) in Linux/macOS, 132251 B Windows for mixed same-host pairing. Independent earlier standalone `Path.write_bytes` vs extra descriptor calls micro observed extra syscall cost; lower-tier only.

No cold startup, official eight-corpi parity/full ABBA, sustained-workload CPU/RSS/temp-I/O, crash consistency or externally equivalent comparison has been established. A small warm A/B **does not** constitute release-performance acceptance.

## Negative truths / debt

O93 is **not** a transactional replacement or filesystem snapshot. For pre-existing output an I/O error after `ftruncate` can still destroy a valid prior archive (O75 debt). The final pathname `stat` is not an atomic namespace commit and cannot prevent all adversarial parent/root/source mutations or power-loss loss. An initially absent output that appears concurrently is now rejected even when its creator is benign. Reader xattrs and ACL completeness remain independent questions. On-disk format revision unchanged.

CI topology, Version Discipline, native, fuzz and historical source-fingerprint gates must be evaluated **on each exact head**. Older engineering-evidence runs initially failed on PR template headings, later on an explicit `quality-ratchet` marker; the PR description was amended, without evaluator modification. Do not mark that status SUCCESS until a fresh run confirms it. Official r24 performance workflow can end administratively green with substantive benchmark SKIPPED; do not award any release credit. Other inherited frozen checks may fail because they demand old source IDs.

## Decision & handoff

**NARROW PRODUCT CORRECTION VERIFIED** on the checked installed three-platform scenarios. Product publication requires review by owners of O90 #448, O91 #449, and contradictory O75/#432 / O78/#435 physical semantics, followed by full general CI and *substantive* official parity/growth gates. No merge or version advancement. Discovery `STATE.json` remains with existing dedicated reconciliation owner #440 and was not modified. No policy change earned.

Counterfactual discriminator: the cheapest decisive adversarial test was a real after-scan atomically swapped path on an authentic Builder, not a static `stat` primitive thought experiment; that O91 signal selected descriptor lifetime over more static filters. Evidence doesn't imply a generalizable magic file atomicity theorem.
