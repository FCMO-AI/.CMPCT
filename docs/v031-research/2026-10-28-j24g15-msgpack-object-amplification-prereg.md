# J24G15 — prerequisite decision: signed MessagePack object amplification defeats raw-byte retention budgets

Status: **PREREGISTERED BEFORE INSTRUMENT OR RESULTS**. This is an independent falsification of the research subclass in #675, not an implementation claim or replacement for its owner. Exact parent: #675 `e5dc38006a49d38b4f68071c9afeed9db7366952`; Reader Git blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. Only this isolated branch is writable.

## Primary question and causal hypothesis
When authentic revision-24 Builder output receives a SHA-authenticated, syntactically valid delta footer whose MessagePack payload is below J24G14's 1,048,576-byte raw-retention budget but represents a large tree of tiny Python objects, can eager, guarded, or adaptive retention prevent the **peak object construction memory**? A raw budget is an input-size limit and does not bound Python materialization. The existing J24G14 admits this as unproven; this experiment attempts to quantify the **actual full Reader RSS and CPU economics** and to discriminate a whole class of ownership-only fixes.

A payload containing a top-level ignored `extension` of ~200k one-key maps should be ~800KiB encoded and allocate much more Python memory than a similarly sized opaque bytes extension. The Reader currently parses even ignored map fields. No fiction about a malicious Writer or natural workload: this is an adversarial *signed, SHA-valid* archive generated expressly to test resource bounds.

## Frozen experiment and strong controls
- Build one genuine r24 archive with first-party Builder; append an authenticated delta footer with `FTR/FM​AGIC/sha` and a `prev=0` orphan reference. The existing valid checkpoint must remain fully recoverable. No product/writer code edit.
- Construct two same-order/similar-size authenticated payloads: `opaque` (large bytes extension) and `nested` (~200,000 one-key map objects). Include a no-extension small negative control.
- Run source-exact installed #675 arm classes **eager, guarded, adaptive** on identical physical archive per case, fresh subprocesses, alternating ABBA order, three repetitions per normal arm/case. Measure process CPU and wall only around opening, read, range and verify; OS Linux `ru_maxrss` in fresh process; optional separate traced allocation diagnostic outside the timing court.
- Confirm same output SHA, old footer, zero depth, full read/range/verify, archive SHA. Preserve raw individual measurements and independently recompute medians and raw/physical metadata controls.
- Independent cheaper oracle before costly source-bound CI: MessagePack `unpackb` in a fresh local subprocess, same exact bytes, with `tracemalloc`, peak RSS and a random-structure negative control. It earns **no Reader/product evidence**.

## Prospectively declared discriminator
- **H1 observed if:** nested-adaptive total peak RSS exceeds opaque-adaptive by at least 12 MiB while both stay below 1 MiB raw payload and both correctly recover prior valid checkpoint; and nested eager/guarded show similar in-decoder peak, proving discard-after-parse cannot prevent construction peak. If nested is rejected by authentic Reader, first classify exact error; that falsifies the proposed admitted-resource failure.
- **H1 falsified if:** the nested authenticated delta is rejected by existing parser/format or adaptive/guarded keep max RSS within ~4 MiB of opaque despite independent Python object amplification.
- CPU and memory comparisons must not replace one another. If nested only increases host RSS due to unrelated startup/native cache, preserve the independent raw-only control and label **ambiguous**.
- Do not claim overall resource bounds from a positive result or propose a fixed arbitrary admission threshold without proving compatibility.

## Cheapest evidence rung, BONK and opportunity cost
This is a low-cost hostile falsifier on an existing candidate; it should **not** start a new cache/threshold family or claim new compression. If H1 is confirmed, the next structural question is pre-materialization bounded admission or schema/projection-aware MessagePack validation—not a different post-parse lifetime budget. If H1 is falsified, retire this specific extension-shape concern and prioritize the measured mixed valid/invalid Reader opportunity elsewhere.

## Invariants and public boundary
Preserve r24 physical archive semantics, source hashes, existing signed-malformed rejection, fallback to newest prior valid footer, exact bytes, version v0.30.0, all frozen gates, threshold semantics and current #675 owner branch. No merge, release, benchmark/headline, product modification or discovery STATE write. If the experiment is inconclusive, report that without promotion. Read CI artifacts from actual exact HEAD, not a prior source or scheduled result.
