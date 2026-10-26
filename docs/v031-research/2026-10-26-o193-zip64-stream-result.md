# O193 — Authentic small-r24 ZIP fallback streaming court

Date: 2026-10-26 UTC. Result: **SCOPED POSITIVE ON THREE PLATFORMS; NOT GENUINE >=4 GiB ZIP64 ACCEPTANCE**.
Research-only stacked draft PR #521 (base O191 #519). No merge, release, format revision, published performance claim or independent 4GiB validation.

## Prospective question and provenance

Hypothesis frozen before implementation in `docs/v031-research/2026-10-26-o193-zip64-stream-prereg.md`, preregistration commit `529757d25158bec8f0d96417d76f8d7bf631c6ab` (before first patch `16fb4f67b87058b8dca7e8beb0efdae1f5b616b4`). Baseline O191 HEAD `9ce2b55d9b4ab8bcac2bb4618ac809557468c724`, Reader blob `74aa7b286dec9700b070b948f5975b22028e41fe`, owned by #519. Its fallback uses `ZipFile.writestr(zi,self.read(rel))`, which owns a complete logical payload. ZIP64 wire-only sparse proof #275 does not prove this product path.

Candidate switched the fallback to `ZipFile.open(zi,"w")` and bounded `read_range` chunks with incremental logical SHA verification. O190/O191 signed calendar, POSIX mode/type and ordinary direct-Deflate branch are inherited unchanged. This *only* runs from `export_zip` when at least one file declares >= 0xffffffff bytes; smaller authentic r24 corpus calls its **same helper** directly to measure mechanism without forging a giant file.

## Real hosted results

- **Actual successful three-host source-bound court:** [GitHub Actions run 40345153310](https://github.com/FCMO-AI/.CMPCT/actions/runs/40345153310), **Ubuntu 24.04, macOS 14, Windows Server 2022 all SUCCESS (3/3)**. All three installed the exact candidate; normalized Reader SHA-256 `c65c4a3d02e943479fee89efbb3b5808289c1cd5f821a30141549a50173ebcea`. Checkout provenance SHA `0f972930cdf2d98a547660179f549f0dafcaae21`.
- Hosted raw JSON artifacts: Ubuntu [#12661500250](https://github.com/FCMO-AI/.CMPCT/actions/runs/40345153310/artifacts/12661500250), macOS [#12661176916](https://github.com/FCMO-AI/.CMPCT/actions/runs/40345153310/artifacts/12661176916), Windows [run jobs](https://github.com/FCMO-AI/.CMPCT/actions/runs/40345153310) (artifact ID not yet reconciled at this record).
- Real Builder-produced revision-24 inputs; ZIP independently read via Python zipfile. Exact logical payload SHA, CRC, member ordering, DOS dates, type/mode, directories, symlinks/hardlinks on POSIX, untouched original CMPCT archive SHA all PASS. A deliberate flipped source byte is rejected by incremental SHA. Compression-level control: compressed test text **3,327 B (level 1)** versus **1,839 B (level 9)** consistently.
- **Linux:** authentic sparse 67,108,881-byte logical member supported; ZIP stored bytes 12,655,212; original CMPCT 6,295,572 B, SHA `0946934bf7530ffec0ea6328b47c54db7bbc2e5efe7dbc2a47363f1247ff3131`; ZIP SHA `3d4bef6fb144eb82b74f7117fd935eef153b779f184d084d1c8db7eccc087460`. Observed max requested logical range **1,048,576 B**, whole-source Read() forbidden. One main streamed export wall **0.4043 s**, *hosted diagnostic, not controlled benchmark*.
- **macOS:** sparse 67,108,881 B supported; ZIP bytes 12,655,212; CMPCT bytes 6,295,827, SHA `90ed1471552440e57c42c8b5f12c4cc01866f70154323c59090fb5487dfa86a7`; ZIP SHA `5876b1baff1e70ea264aaf96ad5cb3d044589afbc1612ec38cbc16448af88c9f`. Max range **1,048,576 B**, streamed diagnostic wall **0.6516 s**.
- **Windows:** filesystem sparse backing not demonstrated, so skipped the 64MiB sparse source rather than pretend support; regular 6.29MiB multi-chunk source passed. ZIP bytes **6,295,938**, CMPCT bytes **6,295,034**, CMPCT SHA `086a74007ca43fd7574f6360d003f737bd0869e1aed4d312e014bcc12f7f34bf`; ZIP SHA `295e590c6fc4c07628c5b2a871f3b596e9647543a37c884c98583728b5baf22b`. Max range **1,048,576 B**, diagnostic wall **0.22325 s**.
- Range-request counters in raw JSON include main stream **plus two 256KiB compression-level exports**, and not merely the first main output; Ubuntu/macOS **763 total requests / 259,788,597 logical bytes requested**, Windows **67 / 20,711,316**. These are not physical decode bytes or RSS.

## Two negative feedback iterations (preserved)

1. [First hosted O193 run 40344299626](https://github.com/FCMO-AI/.CMPCT/actions/runs/40344299626) had Ubuntu/macOS failure from `file_sha256` unexpectedly invoking `read()` on Builder-produced `S_PACK` empty member. The instrument correctly rejected the whole-read. Product patch now resolves canonical hardlink target and derives PACK member's bounded digest from independently authenticated physical PACK range; it does not suppress the instrument.
2. [Second hosted run 40344882936](https://github.com/FCMO-AI/.CMPCT/actions/runs/40344882936) exposed the **test oracle's** own use of `file_sha256` to obtain a PACK digest, which again called whole `read()` under deliberately strict instrumentation. Fixed the oracle to hash the original on-disk source file (or original symlink target) using a separately streamed input, **strengthening independence** rather than bypassing the assertion.
3. The third source-bound court #40345153310 then passed all three hosts.

## Scoped scientific decision

The mechanism of avoiding complete **logical-member ownership in the compatibility writer** survives on genuine small/medium Builder archives, including an authenticated sparse logical 64MiB source, with <=1MiB requested logical slices and independent ZIP-member SHA/CRC. This is **not** a proof of bounded *process RSS*, because `read_range` can internally decode a whole underlying S_BLOB, reconstruct VZIP work, or retain cache state. No actual >=4GiB CMPCT source or ZIP64 parser/Info-ZIP giant-member experiment occurred. An output that is fully byte-identical to O191's ZIP file is not required; semantic ZIP bytes/CRC/date/type/mode are the contract.

Remaining debt: genuine >=4GiB inputs, true RSS/CPU/temp I/O and decode-unit accounting, independent ZIP64 wire readers, run-to-run same-input performance parity, hostile frame bounds, failure-atomic staged publication (#512), canonical ZIP member names (#499), inherited general CI and release gates. The current product experimental patch is **DRAFT ONLY**. Do not promote or merge on this rung alone.

## Counterfactual decision and handoff

Earlier inspection of `file_sha256(S_PACK)` and explicit K_HARDLINK source row relationships would have anticipated the first trap cheaply. This is a local engineering lesson, not sufficient evidence to mutate the global Discovery Engine policy. No `STATE.json` mutation because #440 owns stale-cache reconciliation.

Next decisive action: bound the largest underlying physical decoder allocation and exercise an **authentic** >4GiB sparse r24 source under explicit runner/disk/RSS budgets, checking ZIP64 bytes and external readers, only after securing destination publication. The existing O275 wire oracle can remain the independent control; do not develop a competing writer without evidence that stdlib streaming fails.
