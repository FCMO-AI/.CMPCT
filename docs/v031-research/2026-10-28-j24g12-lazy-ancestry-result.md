# J24G12 — authenticated ancestry materialization: **guarded memory seed, not product-ready**

Date 2026-10-28 UTC. Preregistered at commit `991ddfa2a42bddaa8d76efdd3524a71c9de52b27` **before instrument implementation**. Research-only independent child of draft #668: `698f576a13ae1d14f248271185de3503ed839ee7`, real Reader Git blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. Original source/Reader untouched. Source-bound hosted GitHub Actions [#40679438911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40679438911) established first real result; later source-locked **referee-hosted HEAD `25ba03db0441081fcc9ce97443169bef35c8fdf1`**, [Actions #40679842728](https://github.com/FCMO-AI/.CMPCT/actions/runs/40679842728), **SUCCESS**. The latter makes all definitive measured statements below.

## Scientific fork / baseline / admissibility

Three consecutive footer-negative-proof families (#661 AP, #664 SQLite, #667 packed-u64, #668 staged) improved repeated footer ancestry CPU yet left a memory-producing chain of decoded MessagePack delta objects. Frame review changed **execution lifetime** rather than tuning proof-store thresholds: first authenticate a predecessor chain and retain at most offset/digest pairs for deferred replay. Compared three classes against identical first-party Builder/Writer r24 bytes: eager inherited `CMPCT`, naive skip of invalid delta MessagePack, and guarded parse-and-discard plus revalidation/redecode on valid checkpoint. Real installed source checked against git, fresh child processes, same source/physical archive SHA per cell, ABBA ordering, library CPU/wall (not process startup), `tracemalloc` and Linux `ru_maxrss`, exact footer/depth/read/read_range/verify. Values are **host-specific research evidence**, not shipping semantics.

### Final exact-HEAD raw hosted medians (Ubuntu 24.04, Python 3.11)

| Same physical case | Inherited eager | Guarded parse/discard | Naive skip (unsafe) |
|---|---:|---:|---:|
| 4,096 linked SHA-authentic orphan footers, CPU | **541.691 ms** | **363.070 ms** (-33.0%) | 162.455 ms |
| 4,096 linked, Python traced peak | **30,993,742 B** | **3,650,490 B** (-88.22%) | 3,644,594 B |
| 4,096 linked, peak process RSS (maxrss) | **126,496 KiB** | **43,088 KiB** | 43,088 KiB |
| 512 legitimate signed deltas, CPU | **110.299 ms** | **148.212 ms** (+34.37%) | 122.521 ms |
| 512 legitimate, Python traced peak | **4,460,551 B** | **868,505 B** (-80.53%) | 868,265 B |
| 512 legitimate, peak RSS | **41,824 KiB** | **32,232 KiB** | 32,232 KiB |
| 4,096 independent orphan footers, CPU | **337.687 ms** | **356.256 ms** (+5.5%) | 142.648 ms |
| First-party Writer rename, CPU | **0.8256 ms** | **0.8920 ms** | 0.8631 ms |

On the linked hostile tail, all three ran **4,097 real footer decodes**, and eager/guarded each made **4,097 MessagePack unpack calls**; lazy skip made 1 unpack. On valid 512, eager ran **513** footer decodes and guarded/skip **1,025**: the second pass is real CPU work, not concealed outside timing. The consistent peak RSS evidence does not imply a total bounded-memory product since decoded payloads, proof offsets, scan buffers and compilers may still grow for different inputs. All supported valid objects, digest, selected footer, depths and full/range/verify matched.

**Fatal negative/adversary:** signed footer carrying malformed MessagePack with a valid payload SHA triggered the inherited error in eager and guarded, but the naive skip silently recovered an older valid checkpoint instead. Returning correct bytes here does not make it equivalent to the historical error contract. **Naive always-skip is retired as a drop-in product mechanism** without a separately authorized semantic change. Repeating every valid delta gives guarded +34.37% CPU on a deep valid chain, with no demonstrated simple universal admission decision. The guarded approach is a valuable *memory-efficient seed with timing debt*, **not** a promotable Reader fix.

### Independent second-root receipt referee

The dedicated `research/j24g12_independent_receipt_audit.py` imports **only standard library**, not CMPCT. On exact instrument/result HEAD `25ba03db0441081fcc9ce97443169bef35c8fdf1`, hosted run #40679842728: **641 independently recomputed raw/source/case checks**, **6 malicious receipt mutations rejected** (`false-decode`, `fabricated-median`, `erase-malformed-negative`, `false-release`, `false-source`, `duplicate-key`), independently recalculated medians, source Git blob/digests and read/control counts. It is **not** a separately implemented CMPCT archive reconstruction and does not carry physical `.cmpct` bytes outside the ephemeral CI workspace. This limitation must remain visible. `court.json`, `source.json`, `audit.json` and logs survive as workflow artifacts.

### Initial source-exact replication preserved separately

Earlier source/execution-only HEAD `5d9e692f1673b20edffb7a1633884f2bbe80ddc3` ran [#40679438911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40679438911), **SUCCESS**, same Reader blob but before independent audit addition: linked orphan 506.572 ms eager vs 359.244 ms guarded CPU; valid-512 112.056 ms vs 146.111 ms (+30.39%); traced peak ratio 0.1177815. Repetition supports direction; cross-run subtraction is not a valid paired effect measurement. The definitive final audited run above showed valid CPU +34.37%. Preserve both, do not cherry-pick a more flattering result.

## Disproof / strongest self-critique

- Valid depth-512 slows materially (+34.37% CPU), so unconditional guarded two-pass is **not a Pareto dominator**.
- Naive unparsed delta changes error semantics on a signed malformed footer; it is **not source-equivalent** and cannot be silently shipped.
- The research subclasses duplicate protected original logic to isolate a single causal mechanism. They are **not** a validated combined production Reader.
- The representation retains one Python `seen` set and one `(offset,sha)` tuple per ancestor (O(depth)); both can be very large. Global bounded resources/CPU and arbitrary malicious input acceptance remain unproven.
- SHA recheck on the successful second pass only compares decoded payload digest; it neither atomically pins file metadata nor prevents an adversary replacing on-disk bytes between scans. Original #654 mutation-semantics question remains.
- Synthetic orphan delta payloads contain 32 deliberately unmatchable delete ops each, stressing object materialization; prevalence, false-admission and benefit on naturally occurring archives is unknown.
- Python traced allocations are not total process RSS, and `ru_maxrss` is process peak not necessarily attributable solely to delta objects. Archive size, create/extract performance, native ABI, other hosts, temporary I/O, complete standard parity and packaging were not evaluated.

## Scientific decision / counterfactual

**Decision:** J24G12 proves per-chain *object lifetime* is a separate controllable RAM/CPU owner from negative-proof storage. Guarded discard reduces Python traced peak 88.22% on the chosen linked malformed tail and 80.53% on a deep valid chain, but pays a genuine 34.37% valid CPU debt; early naive skip is semantically divergent. Preserve the former as a bounded **research seed**, not a shipping mechanism. This changed the next decision away from always-lazy productization.

**Counterfactual prospective discriminator:** alongside any future ancestry memory-saving scheme, run (a) a deep valid journal chain, (b) a long deeply linked invalid tail, (c) flat invalid tails, and (d) malformed signed MessagePack before trusting memory savings. Valid replay and error semantics would have killed an unguarded architecture earlier. This is a transferable *local* lesson, but no Discovery Engine policy update is earned from one frame-review episode.

## Highest-leverage next action

Define a fixed-memory/CPU recovery contract and test an **adaptive ownership boundary** that avoids double replay for proven valid short chains, uses bounded storage for long unknown ancestry, and preserves signed malformed-delta error decisions and fallback semantics. Before production, prove stable source identity / in-place mutation behavior and full three-host Reader/Native/physical performance. Because the 512-valid-chain CPU red is material, an always-guarded merge is unjustified. Else shift to distinct product debt: #569 Reader cold-open 27–28x and recovery hardlink/path issues, without duplicating active owners.

**Release truth:** Published v0.30.0/r24, unchanged; branch #671 research only. No code in `src/`, no format/version or frozen evaluator change; no merge, no promotion, no release credit. Exact-head CI status is separately tied to each commit and cannot be inferred from this document alone.
