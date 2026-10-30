# J24G73 — physical installed Reader-open factoring result

Date: 2026-10-30 UTC. **Science outcome: `FULL_READER_SPEED_SEED`**, not a shipping product/release claim.

## Authority and exact source

- Released CMPCT remains `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/revision 24.
- Immutable prediction was committed first `47098cb201bf2424a436d197d7bd09162d872b78`. Fixed research parent: #808 `41cd7f88d9fede55a495f36e78126b26eff85880`. Reader Git blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`, journal `03743ca2a06c022c2ec64243a90fe373cf91e899`, #808 `factored` oracle `7657a41d11f2b3c8136c0b69cfe62401f9b19ccb`.
- Measured HEAD: `5c76b50cfa95a8ada9552ff41b3c424d0839cd7d` (source-exact installed A/B, detached arithmetic controls). Expanded independent wire parser/checks HEAD: `6fe4126cc05aba37cac07c50e53bd358ddbb233d`. Neither modifies any shipping `src/` bytes, formats or release/version.
- Owned isolated draft [#818](https://github.com/FCMO-AI/.CMPCT/pull/818), stacked on #808; product integration remains with #795.

## Prospective prediction and result

Prediction: at least 2× full installed Reader-open speedup on an authentic 2,048-live-member/63-DELETE signed journal on >=2/3 OS, no exact-index/content/xattr/recovery changes, <=+2 MiB Python traced peak increase. Original [exact-head run 41026604105](https://github.com/FCMO-AI/.CMPCT/actions/runs/41026604105) completed 3/3 PASS; independent SHA/MessagePack audit of all original ZIP bytes repeated the arithmetic and reconstructed every physical journal footer. New independent no-CMPCT hosted raw-wire interpreter under [run 41027333346](https://github.com/FCMO-AI/.CMPCT/actions/runs/41027333346) also completed **3/3 PASS**, including corrupted-footer SHA mutation rejection and three independent platform packages. Stronger statement is limited to the source/test shapes below.

| OS | Real DELETE baseline Reader-open median | Research subclass median | Full Reader gain | Python traced peak exported | Mixed 63-op full Reader gain |
|---|---:|---:|---:|---:|---:|
| Ubuntu 24.04 | 30.3297705 ms | 9.187048 ms | **3.30136×** | +1,083,552 B | **1.77281×** |
| macOS 14 | 39.938271 ms | 10.917167 ms | **3.65830×** | +1,083,816 B | **1.87391×** |
| Windows 2022 | 70.34975 ms | 18.58935 ms | **3.78441×** | +1,083,552 B | **1.64327×** |

The larger independent-wire-instrumented exact-head repeat retained the result with DELETE speedups **Ubuntu 3.53403×, macOS 3.71899×, Windows 3.87938×**, not extra product acceleration. Original direct raw measurements: 8 balanced ABBA and BAAB blocks × 4 opens/block = 32 opens per variant per OS/case, 384 wall/CPU observation pairs across both cases. Each platform's original six content/receipt alterations (6/6) were rejected by detached no-CMPCT arithmetic, and additional physical SHA corruption was rejected by the no-CMPCT MessagePack footer parser. No evaluator/protocol thresholds changed after observation.

## Actual physical and semantic scope

Every host built **two** genuine Builder/public Writer archives: 2,111→2,048 members after 63 DELETEs and 128→118 members after 21 renames, 21 deletes, 21 puts. Each archive has exactly 64 SHA-authenticated physical footers (63 one-op deltas plus original checkpoint). Source attestation and same-input index/MessagePack equality were required for every A/B. All expected member bytes, `verify`, signed preflight, latest-footer recovery after bad hash and truncated tail were tested. Strict `require_xattrs=True` extraction on Linux/macOS proved three surviving signed sparse xattr identities, including rename transfer and non-resurrection of deleted/recreated `f0042.dat`; Windows xattrs were explicitly unmeasured.

Complete physical archive bytes on original run, DELETE/mixed respectively: Ubuntu **314,840 / 29,054 B**, macOS **316,208 / 29,142 B**, Windows **300,878 / 28,166 B**. Candidate Reader emitted **no extra on-disk bytes** because it was a read-only subclass over identical input archives; this is not a new compressor-size comparison. An independent *no-CMPCT parser* independently read and authenticated footer Zstd/MessagePack/SHA for all six original artifacts, reconstructed final path-keyed sparse xattrs, and reproduced their complete index SHA-256. Original artifacts:
- [Ubuntu #12963183888](https://github.com/FCMO-AI/.CMPCT/actions/runs/41026604105/artifacts/12963183888);
- [macOS #12963284307](https://github.com/FCMO-AI/.CMPCT/actions/runs/41026604105/artifacts/12963284307);
- [Windows #12964017589](https://github.com/FCMO-AI/.CMPCT/actions/runs/41026604105/artifacts/12964017589).

## Negative evidence and limits

- Mixed archives transferred **only 1.64–1.87×**; #808 helper-only 7.64–9.31× does **not** transfer to a full Reader headline. The 3.3–3.8× DELETE benefit is real but with +~1.08 MiB traced Python memory. This is not an unqualified domination.
- Fresh-process **post-import** RSS medians for DELETE increased around +0.67–0.96 MiB across platforms, confounded by Python allocator/import baselines. OS peak RSS is *not* a release measurement; Windows small-case CPU median is timer-resolution zero. Warm process/open timing is *not* disk-cold latency or process startup.
- Scientific subclass overrides a Reader private method; **no shipping Reader/source code changed**. It is not certified against arbitrary hostile journal grammar, hardlink reparenting, privileged owner overrides, full checkpoint64, concurrent mutations, native Rust semantics or official size/create/extract parity. No release or merge authority, no safety bypass.
- The performance hypothesis was decided by same-input full Reader evidence, not by comparing the old in-memory helper vs a different corpus. All sample ratios and platform contradictions are retained. No Discovery policy update was earned.

## Decision / counterfactual / next exact target

**Decision:** carry #808's general factored cross-generation replay as a promising integration seed for #795, not as a shipped 3–4× Reader. #814's simpler DELETE remains a comparison control if the general candidate's fallback/memory economics disappoint. The cheapest prospective discriminator was whole Reader open on actual Writer output before implementing another production architecture; it retired the missing transfer uncertainty and revealed a roughly +1 MiB Python allocation debt. The next owner-controlled step should isolate whether `factored` can **reuse already-owned decoded index/deltas safely without deep-copy** under immutable caller/identity guarantees, then measure full Reader with large held-out trees, signed fsmeta/hardlinks, strict corrupted-tail recovery and actual OS RSS. Release only after all official exact-source, same-input performance and safety gates. No action on #574-owned Discovery STATE.
