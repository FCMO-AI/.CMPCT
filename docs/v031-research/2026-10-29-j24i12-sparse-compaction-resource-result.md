# J24I12/J24I12b — installed sparse compaction resource scaling and measured phase owner

**UTC 2026-10-29. Status: DECISIVE NARROW SCIENTIFIC POSITIVE / NO PRODUCT PROMOTION.**

## Authority, sources, custody

- Released `FCMO-AI/.CMPCT` `main@80c358f8824ec1b20d349c92ed94c898090969b0`: v0.30.0, r24; no changes.
- Original experimental compaction implementation owner [PR #723](https://github.com/FCMO-AI/.CMPCT/pull/723), source `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`, Builder blob `387192edd783e02bf7a44a38945214bf9d6c183e`, transactions blob `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264`; all unchanged.
- First prospective scientific preregistration `ec5b538ac537417576a33944e2a3be340fcdf1fc` (before source instrument); second distinct **post-first-result** prospective phase attribution preregistration `1c8cb84e30ecd80e00779a53420dbfb6c70ceea8` (before second instrument). The first threshold was NOT changed after observing data.
- First exact installed scientific HEAD `4a975107080be87ba8e6a7c53d83426599859940`, [Actions #40821349596](https://github.com/FCMO-AI/.CMPCT/actions/runs/40821349596), original [artifact #12874389029](https://github.com/FCMO-AI/.CMPCT/actions/runs/40821349596/artifacts/12874389029), 12,336 B ZIP, SHA256 `e860b6d0bd593b2245cb6142175fa682454a2b6676a6b32aa48bab9bcbe69f27`.
- Second exact phase-attribution scientific HEAD `ed10f8c62225a432a05d683d803ac6936553b66f`, [Actions #40821941608](https://github.com/FCMO-AI/.CMPCT/actions/runs/40821941608), original [artifact #12875216264](https://github.com/FCMO-AI/.CMPCT/actions/runs/40821941608/artifacts/12875216264), 13,795 B ZIP, SHA256 `bb176e97c3af8b8fd11ad2f4eb066c1510ab04cb1f414cf1d8116511ab6e2fb6`.
- Both hosted courts installed the exact package and verified actual Builder, Reader and transactions site-package bytes against Git HEAD source. Second original phase-wrapper delegates to `CMPCT.read` unmodified, exactly once, records Linux `/proc/self/status` before and after; it does not affect product source. All instrument files additive to the child branch of #723.

## Measured product-candidate costs (direct observations)

Original hosted court #40821349596, three independent fresh child processes / 2, 32, 128 MiB logical sparse file; each genuine source file has two 4KiB physical extents and a real appended delta update, source SHA unchanged and authenticated output.

| Sparse logical bytes | Source CMPCT bytes | Compacted CMPCT bytes | Fresh child peak RSS KiB | Compaction wall ms | CPU ms |
|---:|---:|---:|---:|---:|---:|
| 2,097,152 | 1,984 | 1,805 | 27,644 | 16.075575 | 15.612961 |
| 33,554,432 | 1,986 | 1,811 | 89,044 | 209.812523 | 209.378692 |
| 134,217,728 | 1,990 | 1,813 | 285,620 | 778.054324 | 777.534636 |

**First prospective decision = SPARSE_LOGICAL_RSS_COST_SUPPORTED.** Fresh-own-process peak RSS difference 128MiB vs 2MiB is **251.9296875MiB**, substantially above frozen +64MiB criterion. Original tree had 8,192 B physical sparse block occupancy at all three sizes; child `/proc/self/io write_bytes` 20,480 B for each. This establishes *memory* inflation rather than equivalent physical disk-write inflation. The journal-preserving straight copy is only a weaker I/O control; do not compare its CPU/wall as equivalent compaction.

Second full source-identical court #40821941608 reproduced the same result independently with +**252.15234375MiB** RSS delta (128MiB run 285,772 KiB vs 2MiB run 27,568 KiB). Different wall times from the first run were preserved rather than selectively preferred.

## Direct causal-phase result — J24I12b

Within one separate fresh 128MiB compaction worker, the measurement-only original `CMPCT.read("sparse.bin")` wrapper observed **exactly two calls**, one on source and one on rebuilt staged archive. Both return 134,217,728 B and exact authenticated logical SHA `13e049ebd03fcf6baa5916d1be340e948e921280f99d85a4c38f86668397ae77`.

| Phase | Before own VmHWM KiB | After own VmHWM KiB | Increase KiB |
|---|---:|---:|---:|
| First source `read()` during verification | 25,072 | 285,640 | **260,568** |
| Second rebuilt-stage `read()` | 285,640 | 285,688 | 48 |

Final worker resident RSS after compaction was only **23,544 KiB**. This decisively attributes the *peak* memory to the first S_SPARSE logical-size `Reader.read` during whole-file verification, not to physical disk staging or Builder alone. The second read is still performed and can allocate logical buffers, but its peak does not exceed the already reached high-water mark materially. **Second prospective decision: FIRST_SPARSE_READ_MATERIALIZATION_CONFIRMED**, exceeding frozen +128MiB first-call discriminator. This is per-call provenance via installed source—not independent low-level allocation tracing or a stable speedup comparison.

## Third-root physical referee and audit limits

Downloaded both original Actions ZIP files off-host, verified archive SHA-256 plus ZIP CRC, then used an independent Python `struct`/MessagePack/`ctypes libzstd` parser that **does not import CMPCT**. For each of the six original source/output r24 archives per hosted run, verified dual authenticated index/footer structure, source's genuine appended delta and effective replacement entry, all physical blob header codecs/CRC32/SHA256, and streamed the complete signed S_SPARSE logical zero-hole SHA using a reusable 1MiB zero buffer. Exact source→compacted effective logical bytes, sparse extent geometry, metadata and SHA all matched. Four deliberate physical mutations (header, primary index, blob payload, footer SHA) were rejected by the referee. The phase receipt also matched the static logical sparse SHA and high-water arithmetic.

The physical parser's independence covers archived bytes and receipt logic; it does **not** independently run the Linux memory meter or guarantee unobserved compaction source/target races. Raw physical Actions artifacts and all receipts remain in the run links above. Separate downloadable local bundle includes the independent referee and audit JSON.

## Owner reuse, negatives and promotion gates

**Existing stronger simpler implementation identified before fixing product:** [#613 J24V01](https://github.com/FCMO-AI/.CMPCT/pull/613) already has streamed sparse verification without full hole materialization. Its [#617 J24V02](https://github.com/FCMO-AI/.CMPCT/pull/617) source-exact same-wire Ubuntu 256MiB evidence: `verify()` peak RSS **547,824→25,478 KiB** and wall **487.376→171.416ms**, both measured, but only for the Reader and **not this compact candidate**. [#620 J24V03](https://github.com/FCMO-AI/.CMPCT/pull/620) extends signed sparse hardlink alias handling; #569 owns composed Reader. **Do not fork or duplicate the existing streaming verifier.** Next useful owner experiment is compositional A/B using authentic #613/#620 source with #723 on identical compaction input, preserving source SHA and complete strong hash, and charging full performance/temporary I/O.

**Still blocked:** #726 staged-name rebind demonstrates a separate physically unsafe publication window. This scientific observation does not repair it. No 4GiB, hostile many-extents, macOS/Windows, crash/durability, race, official benchmark or release parity evidence. No source code, format, version, release thresholds, owner PRs, `docs/discovery/STATE.json` or frozen experiments modified.

**Discovery Engine:** This primary question changed the compaction resource-causality decision, without a collision/duplicate implementation claim. Counterfactual: a broad earlier historical PR lookup for `sparse Reader.verify` would have revealed #613/#617 before choosing a possible *fix*, saving search; the experiment remained useful because #723 compactor's own phase economics had not been demonstrated. One observed search narrowing does not earn a policy edit.

**Handoff:** Keep PR #731 Draft (scientific). Transfer phase result to #723 and #613/#620 owners; no merge, no release. `quality-ratchet`: retain all hard safety, exact fidelity, cross-host and complete product economics before any integration. `disproof`: a future authentic installed-source A/B that loses semantic equivalence, reproduces stage rebind or fails parity is a product veto regardless of this RSS result.
