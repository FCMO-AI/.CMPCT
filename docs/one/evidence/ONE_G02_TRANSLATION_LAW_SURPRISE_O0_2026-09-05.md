# ONE-G0.2 — translation Law persistence across Surprise, O0 headroom

**Status:** O0 headroom passes; continuation/extent search still gifted  
**Exact result-bearing source:** `d4fc5c951d417ec4e5593973773d07fbb684b6cf`  
**Workflow:** `33948213506`  
**Job:** `101258019767`  
**Artifact:** `9964006419`  
**Artifact digest:** `sha256:7d55112c128945c35a91f68b3e6230b07663b5609e7275fd7c8050447dbfbbbc`  
**Experiment:** `ONE-G0.2`

## Referee question

The internally edited-version transfer exposed one mature-minimizer-only relationship. Causal attribution showed that relationship used the same source→target translation delta already byte-proven by surrounding candidate relations; the mature selector merely re-nominated the existing Law after a substituted byte. The O0 question was therefore whether ONE can keep the already-proven translation Law alive and encode prediction failures as explicit Surprise instead of rediscovering every unchanged island.

## Oracle honesty and charged model

O0 gifts only:

- the decision to continue an already byte-proven candidate Law;
- the frozen target-version extent from the synthetic generator.

It does **not** gift the Law seed/delta, Law/control bytes, Surprise positions, Surprise literals, or reconstruction. Every row must first obtain the correct translation delta from an exact successful sparse/epoch candidate nomination.

Charged second-version representation per row:

- 32 B conservative generic Law/control payload;
- ULEB128 Surprise count;
- for each Surprise: ULEB128 position delta + one literal byte.

The base version is already present and is not charged a second time. Reconstruction is mandatory and byte exact.

## Exact-head result

All **50 ONE semantic tests** passed. Frozen decision:

`advance_translation_law_surprise_from_o0_headroom`

Gate failures: **none**.

Across the identical 64-row internally edited-version corpus:

- seeded rows: **64 / 64**;
- literal second-version bytes: **10,485,760 B**;
- charged Law+Surprise second-version representation: **6,222 B**;
- charged fraction of literal: **0.0005933762 = 0.05934%**;
- Law-predicted exact bytes: **10,484,400 B**;
- mature rolling-minimizer exact reuse opportunity: **10,036,655 B**;
- exact reconstructions: **64 / 64**.

The previously failing 262,144-byte base #1 / 16-substitution row is fully subsumed:

- candidate seed delta: **262,144 B**, obtained from a sparse exact relation (`source=311`, `target=262455`);
- explicit Surprises: **16 B**;
- Law-predicted exact bytes: **262,128 B**;
- mature exact reuse opportunity: **262,128 B**;
- fully charged Law+Surprise representation: **87 B** versus **262,144 B** literal;
- exact reconstruction: yes.

Depending on size/edit count, individual rows cost only roughly **36–227 B** under the frozen charged model while preserving exact reconstruction.

## Interpretation

This is stronger than repairing the missing 1,008-byte marginal opportunity. It suggests the mature minimizer is repeatedly paying discovery cost for a relationship that ONE can represent more directly: a persistent translation Law plus sparse Surprise.

That is concept compression in the intended ONE ontology: the same Law explains all unchanged islands, while edits are explicit residual information. No reader discovery and no legacy minimizer opcode are required in the proposed representation.

## Hostile review / debt

The result is **not automatic yet**. The target extent and continuation decision are gifted at O0. Product claims would be invalid until the encoder can bound the continuation cone from the proven Law itself, reject false-pattern cases cheaply, and choose Law+Surprise only when fully charged representation and compute beat crystallized/literal alternatives.

No native creation-time, decode-throughput, peak-memory, selective-read, hostile-input, wire-format, v0.29/v0.30 superiority or release authority is created here.

## Terminal decision

**Advance to automatic bounded translation-cone + MDL admission.**

The next falsifier should infer a non-self-referential continuation cone from the already-proven translation delta, charge every Surprise/control byte, require exact reconstruction, and include hostile partial-copy/random controls where a real seed exists but continuing the Law over the full cone should be rejected by its own representation cost. Do not tune the epoch selector to repair this family unless the Law-persistence route is causally falsified.
