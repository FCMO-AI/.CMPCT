# O21/O21b — measured economics of an explicit strong-extraction policy

Date: 2026-10-24
Status: **SCOPED HOSTED RUNTIME DIAGNOSTIC — DECISION CHANGED / NO PRODUCT PROMOTION**
PR: #373
Base Reader: #258 exact `2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`; Reader Git blob `60f52328467ca509bb410abe6a34810c50917cb5`.
On-disk format: revision 24. Released checkpoint v0.30.0 unchanged.

## Question and controls

Following the O20 physical-integrity distinction (#370), price the simplest more-stringent same-open-Reader policy `verify(); extractall(metadata=False)` against ordinary `extractall(metadata=False)`. The policies **do not have the same integrity semantics**: figures represent cost of requesting a stronger internal SHA check on an immutable pristine input, **not an improved compressor, a legitimate strict same-semantics performance ratio, or a safe transactional extractor**.

Two independent regimes, both validated as exactly one physical owner: 256 Builder-created structured text members stored in one S_PACK Zstd physical owner (196,608 logical bytes; full 4,246-byte archive), and a Builder-independent fixed-r24 4-MiB RAW direct physical owner (4,194,304 logical bytes; full 4,194,760-byte archive). Each source archive is identical between the two policies on a runner. Independent SHA-256 manifests of every extracted file match original source for all **80 child reconstructions across two runs**, 5 ABBA/BAAB balanced blocks × 2 policies × 2 samples/policy/block × 2 corpora × 2 runs. The unchanged original physical-r24 integrity fixed-vector test also passed on both runs.

## Preregistration and evidence identity

Original hypothesis preregistered at `075ad27c595e8c9448b50be7330544f38213e7fd` before instrument and workflow source. The original result, including flawed audit-inclusive CPU naming, remains unchanged in GitHub:
- Run [40121322679](https://github.com/FCMO-AI/.CMPCT/actions/runs/40121322679), exact head `ff476bcce8ea94f9146248c7f017f92e85d5f276`, SUCCESS; artifact `12571680970`, ZIP SHA-256 `2ea7cb482b07961c8fbb6145a720362d5b1f557fd3920645e64c66a4c0e6219c`.
- A separately preregistered O21b precision correction at `a4c327c903077f37ed1630e72730f710aba3e008` fixes CPU timing to stop at exactly the same boundary as wall timing, preserving original audit-inclusive CPU separately. Corrected run [40121641073](https://github.com/FCMO-AI/.CMPCT/actions/runs/40121641073) on corrected head `010e3bfbf4ca71bce0a16e9512e733264d36ec9b`, SUCCESS; artifact `12571857236`, ZIP SHA-256 `84cfa2a645fb99749e48d795ebebc62cc39487ca8e38d401a186d876d0779fd7`.
- Both archive/file/fixture identities and SHA manifests passed, with original pinned independent fixture generator blob `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`.
- Each run retains **40 raw per-child wall/CPU/RSS records**, phase timings, order and paired block deltas. Product source bytes are untouched. The later commit adding this result note is documentation only and must not silently borrow exact-head CI without a new check.

## Measured economy: policy B versus policy A

| Corpus / hosted run | A operation wall median | B operation wall median | B − A | B / A | Paired block B−A signs |
|---|---:|---:|---:|---:|---|
| Structured S_PACK / O21 | 7.864 ms | 8.493 ms | +0.629 ms | 1.080× | 5/5 positive (0.513–0.684 ms) |
| Structured S_PACK / O21b | 12.573 ms | 13.599 ms | +1.026 ms | 1.082× | 5/5 positive (0.882–1.314 ms) |
| Direct RAW 4 MiB / O21 | 2.666 ms | 5.167 ms | +2.501 ms | 1.938× | 5/5 positive (1.999–2.777 ms) |
| Direct RAW 4 MiB / O21b | 4.098 ms | 8.356 ms | +4.257 ms | 2.039× | 5/5 positive (3.448–4.860 ms) |

On O21b the **corrected equal-boundary CPU medians** were PACK 12.607 vs 13.639 ms (1.08185×), RAW 4.132 vs 8.384 ms (2.02890×). The original O21 CPU timings included independent full-output SHA-256 audit and **must not** be used as same-boundary operation CPU. Opening and extracting were measured separately; O21b median verified-phase wall was PACK 1.440 ms and RAW 5.184 ms, partly offset by lower median following extract wall on the already-warmed same Reader (PACK 11.518 ms vs A 11.934 ms; RAW 2.542 ms vs A 3.415 ms).

The two hosted runners have materially different absolute baseline wall times (PACK 7.864 → 12.573 ms; RAW 2.666 → 4.098 ms). This variation is not edited away. The **relative penalty repeats at approximately +8% for PACK and +94–104% for RAW**, under these two structures only. Five/5 paired blocks per corpus on each run favor cheaper ordinary extraction. Relative CPU improvement/regression should be phrased as an integrity-policy cost, never as a same-semantics comparator win.

Median child-process high-water RSS: initial run **46,136 KiB** in both arms; corrected run **45,984 KiB** in both arms. These process peaks are dominated or masked by interpreter and imports; equal maxima **do not prove equal instantaneous decoded-buffer, heap, temporary I/O or RAM traffic**. The source maps remain live, and external memory accounting has not been instrumented.

## Causal interpretation and product decision

For a shared S_PACK the Python Reader keeps decoded blobs up to 2 MiB cached per open handle; explicit verify authenticates the shared physical SHA once, and extraction can reuse that decoded owner. There is therefore only a small additional observed policy cost relative to the 256 filesystem writes in the tested structure. For a 4-MiB direct RAW blob, which exceeds the 2-MiB Reader cache threshold, the two operations likely incur repeated physical materialization and SHA work; the observed roughly doubled operation cost is consistent with that source model. This is an **inference from inspected implementation**, not a direct byte/memory-traffic profile.

**Decision:** The economic evidence rejects a blanket claim that strong pre-extraction verification is prohibitively expensive. It is inexpensive in absolute time for the examined small-pack tree, yet it produces a material ~2× cost on 4-MiB incompressible direct RAW. More importantly, O19/O20 and a live-mmap writer counterexample (#286) show that `verify(); extractall()` **does not** protect publication against a source that changes after its verification pass; it is a useful existing control, **not** a sufficient general secure-extraction product fix. Do not implement an expensive parallel extractor only to save roughly 0.6–1.0 ms in this PACK case. First define source ownership, publication model and whether strongly verified extraction is intended to be an explicit opt-in or a default; then use mutation-safe one-pass physical-owner authentication if genuinely required. Absolute costs/generalization must be rechecked on larger held-out trees and other codecs.

## Strongest self-critique

The original CPU meter was inconsistent with wall time; it was corrected prospectively, preserving original wrong-label data. Both hosted measurements were only one Ubuntu/CPython environment class, share the same CPU architecture class but different runner load/cache states, and used synthetic source data; relative ratios may shift in real-world file systems. Neither source mutation, malicious index nor adversarial destination was introduced in the timing corpus, and unchanged SHA controls do not demonstrate concurrent-source safety. The 4-MiB RAW fixture is independent of Builder (strong conformance control, not a typical Builder-admission sample). Peak RSS equalities offer no memory proof. No release ABBA, creation size improvement, installed desktop package, recovery or portability evidence is obtained. Product result: **NONE**. Scoped installed-product runtime diagnostic: **PASS**.

## Concurrency / discovery / handoff

This was a deliberate new economic question, distinct from #258 (strong physical pack verification implementation), #370 (semantic integrity-tier falsifier), #319 (native PACK selective read amplification), #143/#146 (historical G04 verification folding), and #367 (temporal publication corruption). No existing owner or canonical discovery STATE was overwritten; no collision detected. Counterfactual: the simple same-Reader A/B should precede a new strong extractor because it removes speculative architecture work when SHA/cached decode costs are tolerable. No evidence of a repeatable discovery-*policy* failure beyond O21's local CPU boundary; **discovery policy unchanged**.

Next cheapest high-leverage action: independent source/destination mutation model and candidate product contract; only after that, compare a single-pass strong physical-owner extraction with the cheapest `verify(); extractall()` control, charging RSS/IO/CPU and tree safety. Promotion requires general, hostile, recovery, portability and strict current release evidence. **No merge, no format/release advance, no benchmark/promotion credit.**
