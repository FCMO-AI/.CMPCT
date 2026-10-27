# O223 — Bound full-member chunk-read futures before blaming MessagePack

Date: 2026-10-27 UTC. **Prospective source-exact CMPCT experiment; no product credit.**

## Causal trigger, ownership, and evidence tier

Published CMPCT stays v0.30.0 / on-disk r24. Base **J24C02 PR #569**, exact commit `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, current `src/cmpct/reader.py` blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. No Reader code mutation; #569 owns its implementation. O221 #583 reported 461–485 MiB process HWM on tiny archives with 262,144 repeated refs, and did not attribute the cost. Source review reveals `read()` for both `S_CHUNKS` and `S_CDC` calls `ThreadPoolExecutor.map(self._blob, ids)` with **all** refs as one iterable; under CPython 3.11/3.12, this may eagerly allocate one Future per ref. Separately, Builder already ships `src/cmpct/_ordered_pull.py`, an ordered bounded-futures implementation, but it must not silently be imported into the Reader without semantics/benchmark evidence.

**Already observed non-product screen, prior to this preregistration:** a synthetic stdlib callable on 65,536 input items increased fresh-child peak RSS from about 95–103 MiB for bounded/serial to 203 MiB for eager; at 262,144 eager observed about 531 MiB. This is exploratory diagnosis, *not* a prospectively tested product result, and cannot satisfy the decision below.

## Locked question

On identical authenticated, Builder-independent r24 fixed/CDC input, how much full-member `read()` RSS and wall/CPU does eager `executor.map` cost? Can the strongest **simple serial** control or a bounded 512-item window preserve exact read output and whole-file SHA while keeping peak RSS substantially lower, without moving unacceptable CPU cost into the full Reader session?

**Hypothesis:** high reference-count RSS is dominated by eager futures rather than primary MessagePack index expansion. A bounded ordered map should remove >128 MiB median HWM at 262,144 refs; serial may dominate for small/repeated already-cached one-byte RAW blobs. Confront both instead of proving only a favored parallel mechanism.

## Fixed controls and execution contract

- Use the unmodified installed J24C02 Reader and the preexisting O215/O214 Builder-independent r24 fixture constructors; signed primary/footer, hashes, exact version and blob records. Verify with the original strict `preflight_archive` outside timing.
- Cases: `S_CHUNKS` and `S_CDC`; 4,096, 65,536, 262,144 references; repeat vs cyclic **8 distinct RAW one-byte payloads** as two layouts. Small separate length-varied byte-sensitive checks prevent fixed-offset aliasing. Same file/hash per arm.
- Four arms in independent fresh child processes: ordinary `reader.read` eager; `serial` local `b''.join(reader._blob(...))`; `bounded512` local `b''.join` of ordered map windows of <=512; `bounded64` as locality/overhead sensitivity. Candidate construction still uses ordinary `CMPCT(path)` admission and inherits the **same index**, not a second pathname. Candidate local function is **research-only**, not a Reader patch.
- Measure read session **open+admission+read**, and separately `read()` wall/CPU in every arm; child ru_maxrss; process wall outside read separately. Archive bytes and logical SHA/size immutable; 3 repeated independent processes per arm, randomized interleaving. `read()` byte-exact results and SHA must equal baseline; strong independent `verify()` check on a separate control to avoid 262,144 futures in all candidate timing arms.
- Errors, mismatched authentic input, bad SHA, missing receipts or wrong source identity invalidate science rather than becoming gains. No archive/format/publication or benchmark evaluator changes. Baseline may win.

## Frozen decision criteria

**`BOUND_FUTURE_HWM_MATERIAL`** only if on **both** modes at N=262,144:
1. bounded512 versus eager median child HWM falls at least **128 MiB**;
2. complete **open+read** median wall is no slower than eager by more than 10% (bounded512/eager <=1.10);
3. every arm's output bytes, exact logical SHA and full logical size agree with authenticated expected data, with no control loss.

Otherwise classify `BOUND_FUTURE_PRODUCT_HEADROOM_NOT_PROVEN` and retain individual measured wins/losses. If serial dominates bounded512 on the same cases, prefer serial as the simpler candidate and **do not** claim bounded parallel ownership earned. If high-diversity or compressed/heterogeneous real-product cases are unmeasured, do not extrapolate.

## Alternative explanations and residual costs

- **Alternative:** MessagePack unpack alone costs most memory, or actual large file bytes dominate; capture a child `open_only` control on the identical wire and compare pre/post read HWM. Distinguish high-water RSS from allocations via a local heap probe if feasible.
- **Alternatives:** ThreadPool speeds actual Zstd/Deflate decoding, so repeated cached-byte controls artificially favor serial; this trial cannot authorize dropping concurrency for heterogeneous expensive blobs.
- **Exported costs:** full logical output, Python futures, reference array, per-item Python objects, thread pool cache, CRC/SHA, additional window overhead, stream work, wall/CPU, process RSS. Windows/macOS, journal/recovery, same-inode truncation and official release gates remain untested.
- **Counterfactual:** source inspection of the already-shipped bounded Builder worker pull and the actual `read` eager-map call would have been a cheap, prospective discriminator before interpreting O221's high HWM as index inflation.

## Outcome routing

No product code in this PR and no `STATE.json` edits unless this trial truly changes decisions. Publish raw exact-head receipts and negative cases on this branch/PR, notify #569 and #583 with measured scope, and request owner-integrated full Reader + hostile tests before any shipping change. The Discovery Engine's normative rules, frozen experiments and release law are unchanged.
