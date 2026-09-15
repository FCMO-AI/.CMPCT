# A15 initiation audit — universal reconstruction IR

Status: **candidate audit only; NOT an active thesis; no product/release credit**.

Authority: `docs/ASSUMPTION_LEDGER.md` A15 and `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`. This note exists so the next Foundry activation can test whether A15 deserves a charter without repeating the A01 archaeology mistake.

## Assumption under audit

Current CMPCT reading semantics are implemented through multiple explicit storage/codec families rather than one small typed reconstruction program. In `src/cmpct/reader.py`, current storage dispatch includes at least `S_BLOB`, `S_PACK`, `S_CHUNKS`, `S_CDC`, `S_SPARSE`, and `S_VZIP`; codec dispatch separately includes STORE, ZSTD, LZMA, DEFLATE and Brotli, while links, generation deltas and VZIP recipes add further reconstruction paths.

The A15 question is not “can these branches be renamed as opcodes?” It is:

> Can CMPCT express its existing exact semantics through a smaller universal typed reconstruction IR that reduces reader/mechanism carrying cost and makes new reversible relations composable **without increasing complete stored bytes, decode work, dependency depth, attack surface or portability burden enough to erase the benefit?**

## Why this may have headroom

A universal reconstruction IR could change the ownership boundary. Instead of adding a bespoke archive format branch for each new mechanism, creator-side search could emit a small decoder program composed from a stable primitive set. That could make future mechanisms cheaper to carry, simplify native/Python parity and allow representation search over programs rather than hard-coded storage kinds.

This is only valuable if the IR is genuinely smaller than today's semantics after charging program bytes, interpreter/runtime complexity and verification.

## Internal archaeology completed

No filename-level checked-in experiment/result named as a universal reconstruction IR was found in the current repository tree during this audit. Current reader code already behaves like a hand-written semantic interpreter, so A15 may be an architectural refactor of an implicit IR rather than a greenfield invention. That is a major alternative explanation and must be tested first.

Do not charter A15 until the cheap oracle below shows that explicit unification buys something measurable beyond vocabulary.

## External feasibility boundary

Two adjacent systems show that the broad design class is feasible but also raise the novelty bar:

1. **OpenZL** exposes a graph-based compression framework in which encoding is composed from nodes/transforms and the decoder executes the recorded graph. This is strong evidence that a stable generic decoding runtime can support creator-side composition; CMPCT cannot claim novelty merely for “compression as a program/graph.”
2. **Brevis** (arXiv:2601.20961, 2026) uses a small typed, bit-exact tensor DSL and synthesizes compression/decompression programs. It reports 2–5x compression on evaluated model families and a 14.5x geometric-mean compression ratio across a heterogeneous benchmark, demonstrating that typed reversible program search is an active frontier rather than a speculative metaphor.

A15's useful CMPCT-specific question is therefore exact arbitrary-filesystem reconstruction, complete byte/access/recovery accounting, and whether one IR can subsume current archive semantics with lower total carrying cost.

## Cheapest decisive oracle before charter

Build a **non-product semantic projection** over the current reader, not a new archive format.

1. Freeze a minimal candidate primitive set derived from current semantics, for example:
   - `READ_PHYSICAL(range)`;
   - `DECODE(codec, params)`;
   - `SLICE(offset,length)`;
   - `CONCAT(children)`;
   - `SPARSE_WRITE(offset,child)` / zero-fill;
   - `APPLY_DELTA(base,patch)`;
   - `LINK(target)`;
   - `VERIFY(hash/length)`.
2. Translate every current canonical storage mode and VZIP/generation reconstruction path into that IR **without changing archive bytes**.
3. On the existing benchmark/release corpus, measure:
   - IR program bytes if serialized canonically;
   - primitive count and maximum dependency depth;
   - dynamic decoded bytes / amplification implied by the program;
   - number of reader semantic branches replaced versus branches still requiring escape hatches;
   - Python/native implementation delta and interpreter dispatch cost in a microbenchmark;
   - malformed-program validation surface.
4. Compare against a strong simpler control: keep today's storage kinds but factor their shared decode helpers without introducing a serialized IR.

## Frozen initiation criterion proposal

A15 should become an active thesis only if the projection can represent **all currently canonical read semantics with no mechanism-specific escape opcode** and one of these is true before any format change:

- projected serialized program overhead is <=0.1% of current archive bytes on the release corpus while removing a material fraction of distinct reader semantic branches; or
- the IR exposes at least one exact composition currently impossible without a new bespoke storage kind, with a charged oracle showing material addressable bytes/access value.

At the same time, the interpreter/control microbenchmark must show no >5% decode-throughput regression for simple STORE/ZSTD leaf reads after excluding process startup noise. These are candidate thresholds only; they must be frozen in a formal preregistration before result-bearing execution.

## Kill / narrow conditions

Do not charter if:

- the “IR” is merely a one-to-one renaming of existing storage kinds;
- escape opcodes preserve most bespoke reader branches;
- descriptor/program bytes are material on small-file archives;
- native/Python implementations become harder to keep semantically identical;
- simple decode pays persistent interpreter overhead without enabling new exact relations;
- existing helper factoring captures most maintenance benefit without a serialized/program model.

## Next executable action

Before any A15 code lands in product paths, inventory the exact current reader semantic branches and define the smallest candidate primitive set plus the helper-factoring control. Then freeze the projection oracle. If that audit cannot produce a meaningful delta, leave A15 unchartered and return to the Assumption Ledger.