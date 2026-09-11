# ONE-G0.2 — Selectively authenticated graph-descriptor transfer — 2026-09-05

## Mission lock / Referee freeze

The preceding frozen multi-version transfer established a specific blocker: one shared Law + Surprise basis graph improved density as related roots accumulated, but the simple reader authenticated and read the complete graph manifest for every 4 KiB request. At eight derived versions that manifest was 632 bytes, and complete-manifest traffic broke the frozen `<= 1.20x` median authenticated-touch gate.

The frozen Builder tested whether this debt belongs to control addressability rather than to the ONE Law graph itself. It kept the same corpus, edited-version families, mutation counts, basis AuthTree geometry, request size, alignment sweep, Law semantics, Surprise bytes, and `<=1.20x` gate. It introduced no temporal/version opcode and no fallback codec.

The tested representation authenticates generic graph descriptors with a domain-separated binary Merkle tree. A descriptor control is 40 bytes (`32 B Law + 8 B Surprise length`). The already-required SHA-256 digest of that descriptor's Surprise becomes an input to its Merkle leaf commitment rather than being persisted a second time inside the descriptor. A selective reader fetches only the fixed graph header, target descriptor control, complete target Surprise, descriptor proof, basis proof, and basis bytes touched by the request.

All persisted and selective costs are charged. The graph commitment replaces the already-required root digest rather than being double-counted.

Frozen advancement required, for every family-prefix/target row:

1. complete persisted bytes strictly below the same unauthenticated independent-literal family used by the prior transfer;
2. median authenticated 4 KiB touch amplification `<= 1.20x`;
3. exact reconstruction at every alignment;
4. deterministic corruption rejection for graph header, descriptor control, Surprise, and descriptor proof.

If no frozen basis leaf passed all four conditions, standard selective descriptor authentication was to be retired as insufficient; the access threshold was not eligible for relaxation.

## Exact execution identity

- experimental version: `ONE-G0.2`
- result-bearing source: `9cf00d4d64323b554f98b5dbee5072b2d3fb7fbf`
- workflow run: `33953127629`
- result-bearing job: `101271471717`
- artifact: `9965480503`
- artifact ZIP SHA-256: `0f7d70916479506b0320adfec6a104851eddf6344f7406dc516746e02744f00a`
- result JSON SHA-256: `6086a54f64b6ba62fbb3b96cb4ccccc49eb5c32580c2de334083075f17112792`
- result rows: `1080`
- exact failures: `0`
- corruption failures: `0`

## Result

Frozen decision: **`selective_descriptor_auth_restores_multiversion_transfer`**.

Three preregistered basis leaf sizes pass both the complete-byte and median authenticated-access gates across every tested family prefix and target: **80, 96, and 192 bytes**.

| basis leaf | worst candidate / independent-literal family | worst row median authenticated 4 KiB touch | worst single touch | v8 descriptor-tree stored hashes | v8 descriptor proof |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 80 B | 0.901833x | 1.178223x | 1.244629x | 448 B | 96 B |
| 96 B | 0.835182x | 1.193848x | 1.193848x | 448 B | 96 B |
| 192 B | **0.668434x** | 1.193848x | 1.240723x | 448 B | 96 B |

The rejected frozen leaves remain useful negative evidence:

- 32 B: density loses (`1.500465x`) and access loses (`1.240723x` median worst row).
- 48 B: access passes (`1.178223x`) but density loses (`1.168678x`).
- 64 B: almost density-neutral but still loses (`1.000465x`) and access loses (`1.240723x`).
- 112 B: density wins (`0.788063x`) but access narrowly loses (`1.209473x`).
- 128 B: density wins (`0.750465x`) but access loses (`1.248535x`).
- 160 B: density wins (`0.701637x`) but access loses (`1.256348x`).

At eight versions the descriptor proof is 96 bytes (three SHA-256 sibling hashes). The selective metadata before target Surprise and basis proof/data is therefore `80 B header + 40 B target control + 96 B descriptor proof = 216 B`, versus the prior 632-byte complete manifest. The Builder removes **416 bytes of unrelated control traffic per selective request** at that family width while preserving authenticated exactness.

## Causal interpretation

This result falsifies the idea that the eight-version locality loss is an unavoidable consequence of sharing one Law + Surprise graph. The dominant exported debt was **reader-side authentication/addressability of unrelated graph control**. Making generic descriptors selectively authenticated restores the frozen transfer without adding a reader-visible mechanism or weakening integrity.

The result also demonstrates concept compression: the target Surprise digest is not duplicated as both descriptor payload and integrity input. One digest serves the integrity relation directly through the descriptor leaf commitment.

## Hostile-review boundary and remaining debt

This is not yet a general CMPCT1 victory. The descriptor Merkle tree introduces new costs that the successful access experiment does not erase:

- up to 448 bytes of stored descriptor-tree hashes at eight versions;
- descriptor-tree construction/hash work during creation;
- `O(log V)` proof verification on selective reads;
- update work when one descriptor/Surprise changes;
- a physical-layout/failure-blast-radius question for stored descriptor-tree nodes;
- no native-speed, peak-memory, canonical-wire, full 15-workload, v0.29/v0.30, portability, or release authority.

The next decisive experiment is therefore not another leaf-size sweep. It is a causal compute/update/blast-radius profile of whole-manifest authentication versus selective descriptor authentication on the same frozen version families, charging bytes hashed, hash operations, persisted metadata, proof work, and changed authentication nodes. If the descriptor tree merely moves an excessive bill from read traffic into creation/update complexity, the representation needs further concept compression before promotion.

## Claim boundary

**Generic graph-control addressability structural transfer only.** No claim is made here about superiority to frozen v0.29 or deferred v0.30, canonical CMPCT wire format, native throughput, or release readiness. The explicit same-input 15-workload decision gate remains reserved for the first activation on or after 2026-09-11.
