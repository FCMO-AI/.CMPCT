# J24I47 preregistration — integrity-observation bound before new FLAC locality format

Date: 2026-10-30 UTC. **RESEARCH ONLY.** Parent #796 at `6d8fe62c9fecdd5c75cb1fc38387d9e20c6d894d`; public release remains v0.30.0/r24. No product/format/ABI/release changes authorized here.

## Primary fork (different proof frame)
After J24I46 demonstrated fast FLAC seek but falsified seek-only *full-member integrity equivalence*, ask whether extra *in-archive* chunk hashes, a Merkle tree, a seektable, or more clever codec indexing can yield **exactly the inherited fail-on-any-physical-corruption-in-target-member** guarantee with sublinear per-request observation from an **untrusted, mutable, not-previously-fully-validated** archive.

This is distinct from the weaker and potentially useful guarantee “the returned requested bytes match an authenticated per-range digest.” The question is about an *unchanged contract*, not compression or nominal speed alone.

## Baseline, controls, assumptions
- Native candidate #788's `read_range` uses complete target-member decode/strong digest before returning a region (#796 source inspection); #788's optimized `verify_complete` is separate and already owned. Do not compete.
- A trusted immutable external digest/identity, persistent validated cache, tamper-evident external watcher, signature rooted outside the archive, or preflight full-member scan are **not given for free**. The previously committed index/footer is not an oracle for whether unseen payload bytes changed after creation.
- Strongest simple control: SHA-256 over all member bytes on the same opened source.
- Candidate control: partition logical member into fixed 4KiB/64KiB/1MiB regions; commit 32-byte digests and charge 16 bytes per-region descriptor. Permit seek and validate *only* the touched region.
- Alternative explanations to rule out: corruption happens inside touched region; per-chunk commitment was updated to match it; the indexing oracle silently read full source; a full scan occurred at open; trust or immutability was gifted.

## Predictions, disproof and cheapest evidence
1. **Indistinguishability prediction:** if a purported exact-global-integrity range verifier observes a proper subset S of a member, changing one byte at an unobserved offset j leaves every observation unchanged; the verifier must accept the corrupted member whenever it accepts the clean one. This applies to deterministic adaptive algorithms, regardless of extra immutable in-archive metadata. A finite executable witness will compare local-digest verification against a true complete SHA. The actual proof is the indistinguishability argument, not the toy program.
2. **Quantified carrying-cost prediction:** on the *already frozen* J24I46 32MiB PCM originals, 48 bytes per logical segment at 64KiB will cost **below 1%** of existing encoded FLAC size, while 4KiB segmentation is materially more expensive. This is an optimistic **metadata lower bound**, excluding codec seek checkpoints, compressed frame dependency, source custody, hash-tree proof bytes, index compression, CPU, cold-open and recovery costs. No product win is earned.
3. **Decision:** retire strict-equivalence sublinear member verification from a mutable untrusted source **unless** a previously authenticated immutable/pinned trust boundary is made explicit and its costs charged; retain segment authentication as a possible *different semantic API* question only, not a drop-in. Do not start a new format implementation merely because its local-seek wall time is impressive.

**Kill/narrow condition:** find a legitimate exact-global same-source protocol with a proper unobserved member byte, no trusted precommit/monitor/previous scan, that nevertheless detects its change; or show our presumed contract is in fact only local-range integrity, in which case the impossibility theorem is not relevant to that weaker API. Any observed split between clean and mutant must be attributable to an observed changed byte or explicitly charged trusted side information.

## Controls and evidence plan
Research-only Python script using bytearray and hashlib (no CMPCT import), two structurally distinct patterns, mutation outside the requested region, three segment granularities, local digest and full digest on clean/corrupt sources. Independently recompute all numeric cost rows from hard-coded **source-stamped** J24I46 generation manifest; test corrupted *selected* region as positive detection control. Preserve JSON source fingerprint, fixed offsets, actual read coverage, byte counts and negative. Run locally and persist the exact executable, results and report in this isolated branch; request hosted CI only if it changes the scientific decision.

## PARETOBONK / ownership
Productize #788 is a higher-value ready owner than creating a redundant Claxon fork; J24I46's seek-only equivalence is already falsified, no reason to rerun the full 288 samples. Adjacent different-worldview action here is a bounded proof/contract filter that can kill a whole false class of frame-island Merkle proposals. #574 owns shared discovery state; do not modify it. No merges/releases/benchmark evaluator mutations.
