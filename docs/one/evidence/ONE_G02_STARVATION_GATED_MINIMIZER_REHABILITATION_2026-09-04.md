# ONE-G0.2 — starvation-gated minimizer rehabilitation

**Date:** 2026-09-04 America/Mexico_City  
**Experimental version:** `ONE-G0.2`  
**Scope:** encoder-discovery compute rehabilitation only

## Mission lock

The rightmost 4,096-position Gear minimizer recovers shift-invariant exact-reuse opportunity that cheap fixed/sparse observers can miss, but always-on minimizer maintenance is expensive. The tested family keeps the frozen sparse-anchor starvation condition at exactly `MINIMIZER_SPAN == 4096` positions and asks how much expensive state can be deferred without losing the marginal relationship.

No result below changes ONE reader semantics. Survivors still compile into generic exact-reuse Law after byte proof. No threshold is retuned after seeing results.

## 1. Cold late activation: opportunity and compute headroom

Exact source `4498568e21908cf337d4625048743772566e52c5`, workflow `33943844440`, job `101246239490`, artifact `9962688489`, digest `sha256:6ca856e27054b5da34ac17646e01f2bc68e4b19d1256854c394fc7112e414519` showed that the original 8 KiB sparse-starved shifted adversary kept its full **8,192 B** marginal opportunity while random and zlib-random controls kept minimizer rescue active for only **2.4141%** and **2.1696%** of positions.

Exact source `ff06f9e908e5f9dd57b6c2813a879e42a5d01a24`, workflow `33943929056`, job `101246460961`, artifact `9962721689`, digest `sha256:a759d2336b83d7a928cbc01ffc37bd17b321c4577e3f9d7caadff8f132b523d5` then charged nine alternating paired hosted rounds. Median gated/full elapsed ratios were **0.445905x** random 1 MiB, **0.455258x** zlib-random, **0.525665x** repeated 64 KiB basis, **0.448534x** ordinary shifted 512 KiB pair and **0.869520x** on the original hard 8 KiB starvation row.

These were headroom results, not promotion.

## 2. Generator-distinct transfer rejects the cold-start shape

Exact source `66f512216452edbddd46da8f3b45f55748b6b45b`, workflow `33944085404`, job `101246889451`, artifact `9962759274`, digest `sha256:b8b003c3cc3d685cdbb4b3113a0ee861a476700722e72451419a38c572fc7ce0` selected the first 12 deterministic 4,096-byte pseudorandom bases with zero qualifying sparse Gear anchors, without consulting minimizer outcomes. Each basis was duplicated with 1-, 8- and 31-byte insertions.

Of 36 rows, **35** genuinely required full-minimizer opportunity beyond both cheap observers. The cold late-rescue implementation lost **35/35**. Typical hard rows had full-minimizer opportunity **4,096 B** and cold late-rescue opportunity **0 B**.

**Causal interpretation:** the frozen gate spends one 4,096-position span proving sparse-anchor starvation, then the cold implementation spends another full span warming an empty minimizer. The original 8 KiB-basis adversary was long enough to hide this second warm-up. The 4 KiB generator-distinct transfer rows were not.

**Scoped negative:** do not reopen `detect starvation -> empty minimizer -> second full-span warm-up` by moving the threshold or changing seeds. Reopening requires eliminating the second warm-up.

## 3. Deferred materialization repairs all transfer losses

The causal rehabilitation retains the already-computed prior span so minimizer state can be materialized immediately when starvation is proven, without rescanning source bytes.

Exact source `749107dd71f7df1e8d3a02fa047534074508bb71`, workflow `33944172060`, job `101247129611`, artifact `9962789618`, digest `sha256:8e0bee334c57c8a66b70ca0f116e6e1559c51c8a61c6995241392a50355f91f7` preserved **35/35** hard transfer rows with no losses. The first model retained a `(u64 Gear state, u64 absolute position)` tuple per span position, or **65,536 B** modeled history.

On exact source `c433388aa20cc424c17400162923fee889c2fa78`, workflow `33944274108`, job `101247304655`, artifact `9962851114`, digest `sha256:c2ec76460df6628baa5f35c27cdf1c125352fd6f205db371b9a11c9d681da834`, the same 64 KiB-history form also survived direct hosted carrying-cost A/B. Negative-control median elapsed was **0.528039x** full minimizer. Representative ratios were **0.519396x** random, **0.536682x** zlib-random, **0.590256x** repeated 64 KiB basis, **0.512345x** ordinary shifted 512 KiB and **0.870689x** on a generator-distinct hard 8,193-byte row. Opportunity was preserved on every charged relation.

This established that eliminating the second warm-up is a real compute rehabilitation, not only a semantic repair.

## 4. Remove redundant position state: 32 KiB Gear-signal history

Absolute positions in the retained history are derivable from ring order and current position. Exact source `c433388aa20cc424c17400162923fee889c2fa78`, workflow `33944273931`, job `101247300755`, artifact `9962845690`, digest `sha256:7a3756acd899dbbb2c80e8b3a9bb64cc39e0a97d8ac0ef4c652bcee67275cd51` retained only one `u64` Gear signal per position.

Modeled history fell from **65,536 B to 32,768 B** while preserving **35/35** hard transfer rows. This form established semantic/state compression only; no separate timing promotion is claimed.

## 5. Byte-history replay: 4,112 B state, exact transfer, performance near-miss

Gear states themselves are deterministic from one previous Gear state plus the intervening source bytes. The next rehabilitation therefore retains only:

- a 4,096-byte circular source-history cache;
- one 64-bit Gear seed state immediately before its oldest byte;
- two 32-bit ring counters.

Modeled incremental history is **4,112 B**, an **87.45%** reduction from the 32 KiB signal ring and **93.73%** from the original 64 KiB tuple ring. The cache is filled during the fused observation pass and replayed only after the unchanged starvation trigger; it is not a rescan of the original source stream.

Exact source `699782ed60d56fa45673b2f14ae9691a28bfdee3`, workflow `33944451028`, job `101247902286`, artifact `9962928324`, digest `sha256:41bd729bd230c59fe86fcd03f1cb8163cc3cdb16c5d5f7a041397be463039c3f` passed the complete ONE semantic boundary and the combined transfer/timing instrument.

Transfer remained exact:

- hard transfer rows: **35**;
- preserved: **35/35**;
- loss cases: none;
- replay state asserted identical to the fused Gear state.

But the preregistered hosted performance gate was **not** met:

- random 1 MiB: **0.909675x** full-minimizer elapsed;
- zlib-random: **0.890525x**;
- repeated 64 KiB basis: **0.953397x**;
- shifted 512 KiB pair: **0.893749x**;
- generator-distinct hard 8,193 B row: **1.262077x**;
- negative-control median: **0.900100x**, versus frozen requirement `< 0.90`.

**Decision:** `reject_or_rehabilitate_byte_history_rescue` for the current Python execution shape. The 0.90 gate is not rounded, weakened or moved to manufacture a pass.

## Hostile review and next reopening predicate

The 4,112-byte design is semantically strong but its Python loop pays per-byte ring writes, modulo/index bookkeeping and seed advancement, then replay cost on activation. The tiny hard case is slower despite preserving its 4,096-byte relation. Hosted Python therefore cannot promote it.

The next allowed Builder is a **compiled/native research microkernel using the same 4,096-position gate and the same generator-distinct transfer corpus**, with no threshold change. The relevant comparison is the current promoted tail-return 8 KiB discovery baseline, not an obsolete Python deque. Every generator-distinct hard transfer row is already at or above the current 8,192-byte dispatcher boundary, so the small-file counter path need not pay this candidate's carrying cost.

A further state hypothesis is promising but unproven: inactive byte history and active minimizer scratch may be mutually exclusive and therefore unionable. On trigger the history can be replayed into the same scratch region; after a later sparse anchor resets rescue, that region can return to history use. Do not claim this peak-state saving until a compiled implementation measures it.

Also unresolved: the repeated-64-KiB row activates rescue for about **15.06%** of positions despite cheap observers already owning the full relation. Starvation is a useful causal gate, not yet a complete opportunity-value predictor.

## Claim boundary

This evidence advances ONE encoder-discovery compute architecture. It creates **no new stored-byte win, product/native throughput claim, reader-format change, selective-read result, release authority, or v0.29/v0.30 superiority claim**. The full 15-workload Genesis comparator gate remains due on/after the first activation of 2026-09-11 America/Mexico_City.
