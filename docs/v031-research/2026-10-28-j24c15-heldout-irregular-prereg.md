# J24C15 — Held-out irregular/codec, Q1, and global checkpoint budget (PREREGISTRATION)

Date: 2026-10-28 UTC. Status: **prospectively locked before J24C15 instrument or workflow**.
Parent = J24C14 #665 HEAD `3b29aacc5a575d3f2a6de54e85c2032ea3ff81ed` (science-only; the product Reader remains byte-identical to J24C13 #662).
Owners: #641 ABI3, #662 fused implementation, #665 first published-floor comparator. **This child owns only new J24C15 research, tests and CI.**
No release, merge, product change, format change, benchmark mutation, threshold gardening or shared Discovery STATE edit.

## Question and falsifiable mechanism

J24C14's 4.08–5.26x released-floor advantage used only 4-byte fixed RAW physical owners, six reads and one large logical member per archive. Are fused stride-256 offsets genuinely safe and economic for held-out **heterogeneous physical blob sizes (including zero)**, **mixed RAW/Zstd physical owner codecs**, **one-off Q1 early and tail queries**, and **multiple signed members competing for a bounded global index budget**?

Mechanism prediction: native admission computes exact logical prefix once while it already validates the signed descriptor list; subsequent bisect and bounded decoding return exactly the same slice as independent logical-byte reconstruction. This should transfer to heterogeneous lengths without workload identity dependence, but Zstd decoding and short-session costs may reduce or reverse the gain. The global budget must affect only optimization eligibility, never safety or exact bytes.

## Exact historical controls

Three independent installed Python 3.11 wheels, one hosted Ubuntu runner and one independently serialized signed r24 byte stream per case, shared by all arms:
- released v0.30.0 `80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`;
- native strict ABI3 #641 `a639570c1e9f9b36decae3893265be74a6d185b0`, Reader blob `9bca5d1047f9c78984b945d7ca90e3149fe429ab`;
- fused protected #662 (inherited on this branch), Reader blob `c4d1dee0a31527b814d6e1f41b77abe1cc987996`.

Reference fixture families: irregular RAW 65,536 and 262,144 references with nonuniform sizes including zeros; mixed RAW/Zstd 65,536 references with nonuniform sizes. Generated from fixed payload/codec descriptors and signed r24 framing **independent of all three Builders**. Each input has fresh SHA-256 and distinct deterministic bytes. Q1 early, Q1 late, Q6 nonmonotone and Q64 nonmonotone queries, all with independent exact slices; phase wall/CPU and high-water RSS (when actually observable), process startup separate. No reference to J24C14 result as a substitute for this experiment.

The multi-member budget test must create an authenticated archive with at least three members, then *test* (not ship) a deliberately reduced in-memory checkpoint budget to exercise first-member admission and later-member fallback. It must compare every member's full bytes, strong verify and early/tail ranges with independent source payloads, record exact retained marks, and restore original budget afterward. This is only a branch-correctness test, **not proof of natural 65,536-mark exhaustion nor a performance number**.

## Preregistered outcomes

**Kill/scope-narrowing:** any wrong byte, false acceptance, missing expected native execution, bad signed-wire hash, incorrect budget fallback or missed source fingerprint => FAIL, do not productize. No safety equivalence is claimed against the weaker released Reader on hostile inputs.

**Economic decision:** For a given held-out cell, a material regression against released is both >=5% AND >=3.0ms in median full-session wall, with the same separately reported for CPU. A Q1 regression is particularly material and prevents generalized Q1 performance credit. A positive transferred advantage is >=1.20x published/fused complete-session wall **and** CPU in a Q6/Q64 cell, with no >8MiB observed high-water RSS delta. Record all cells, not only positives. If the major hetero families do not generalize, narrow/retire the claimed broad throughput advantage rather than modify post-hoc thresholds or fixtures.

Evidence tier: installed same-input *research* court. A CI success validates the instrument and records even negative results; it is not a declaration of release readiness. Complete frozen publication/parity, Windows/macOS, live mutable-source and external compressor/equivalent-security comparisons remain outside scope.

## BONK and ownership

Cheapest decisive next step is a held-out source-exact installed court plus independently audited raw evidence, not another ABI3-only synthetic speed score or nearby stride tuning. Stronger simpler control is the actual published Reader; #641 is the secured alternative. #583 and #652 negatives remain binding. No overlap with #667 footer proof or #666 VZIP work. Evidence is archived with source SHA, workflow/run/artifact identity, negative cases and next discriminator; do not update stale main `docs/discovery/STATE.json`, owned by #574.

Counterfactual discriminator: including Q1/heterogeneous codecs/multiple members with the original released-floor test could have exposed the generality boundary one experiment earlier. Only record this as a transferable process lesson if evidence actually shows a material omitted-coverage cost.
