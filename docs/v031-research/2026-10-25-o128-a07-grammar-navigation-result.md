# O128 A07 — Binary grammar-navigation oracle: stronger grouped control wins bytes

**Evidence state:** lower-rung research only; *not* a CMPCT archive, release gate, format change, general-purpose workload result, or a Reader/Builder capability claim. Prospectively frozen [hypothesis](2026-10-25-o128-a07-self-index-grammar-prereg.md) at commit `8dc24288fc1631f0e705fb57a22eea6ab2c324d3`. Primary independent source-bound hosted [Actions run 40242242796](https://github.com/FCMO-AI/.CMPCT/actions/runs/40242242796) at `f931e0456af800dcea9017ed801389e6ab6d9e83` **SUCCESS**, 16/16 generated cases with exact member reconstruction, Zstd-19 metadata frame readback, and per-range grammar traversal. Original artifact **12617034730** contains `oracle.json` and `custody.txt`; ZIP SHA-256 `52fa6e001ac64aff5afe516e71d88f481670c58e2f3dfd74da8d25ece07f8389`, JSON SHA-256 `daedb6a88607a026aa54e925343d322f253367042162d75ba401788605007e2c`.

## Primary question and change of decision

Can a global binary RePair-style grammar over **exact deduplicated physical block IDs** save **complete stored bytes** while supplying its own bounded navigation index (child IDs and logical subtree lengths), compared with compressed, separately seekable control streams?

**Original preregistered control**: each of 16 independently indexed member-block-ID lists, min(raw varints, Zstd-19), with exact identical physical independently compressed block dictionary, paths, offsets, hashes and codec/framing charge. The gifted grammar oracle achieved a **positive against this weaker control** in two families:

| Deterministic family (four seeds each) | Mean grammar whole-archive saving vs per-member flat-ID control | Mean grammar *loss* vs stronger grouped-ID control | Grammar max cold decoded-work ratio | Chosen grouped frame max decoded-work ratio |
|---|---:|---:|---:|---:|
| Repeated 8-block motifs, sparse mutations | **3.409%** | **280 B / 1.747%** | 1.535× | 5.062× |
| Rotated shared sequences, sparse mutations | **2.975%** | **341.5 B / 1.759%** | 1.887× | 5.062× |
| Independent references to shared blocks | -0.038% | **319 B / 1.217%** | 1.254× | 5.062× |
| Opaque independent 256-byte blocks | -0.003% | **243 B / 0.077%** | 1.504× | 5.031× |

All 16 members per case were exactly rebuilt; 64 blocks per member, 256 bytes per block, four fixed content-only seeds 31/101/2026/4096. Full original rows, input SHA-256 and individual grouped-frame outcomes remain in the ZIP, not just this aggregated table.

**Counterfactual/PARETOBONK:** the stronger simple control should have been the *first* rung, not an implementation follow-up. Independently Zstd-19-compressing groups of 1/2/4/8/16 member ID lists (with independently charged frame offsets, raw+compressed lengths, codec, group count, physical dictionary, member catalog and SHA) gives all the cross-member sequence gain without a recursive grammar decoder. Frame size is chosen on complete charged bytes **only among frames satisfying <=8× selected 256-byte logical decoded-work amplification**. On every hosted case, that grouped baseline is **smaller** in complete bytes than the grammar. Selection was not based on seed/fixture identity.

A second stronger size-only control, one **solid Zstd-19 stream of full file names/content**, is 10–20% smaller than grammar on these synthetic families, though it does **not** prove equivalent selective-file/range access. Plain per-member Zstd-19 is much larger on shared-block families, showing why exact shared physical blocks are not a vacuous baseline.

## Interpretation and negative knowledge

**Decision: REJECT this 96-rule binary block-reference grammar as a *storage-byte winner* in the tested regimes.** Its first ~3% apparent full-byte improvement was a control-choice artifact: cheaper ordinary grouped compressed references capture more. The >=1% materiality criterion was *not* relaxed to rescue the hypothesis.

**Not Pareto-dominated across all dimensions:** grammar cold decoded control work can be 1.3–1.9× for the block-seek versus ~5× under the smallest grouped-byte owner. Those extra grouped decoded bytes are typically hundreds, not an archive-sized payload, and actual cold-open latency/cache/RSS/read traffic were not measured. This does not justify reader/format complexity yet but also does **not** prove grammar/self-index concepts impossible. A future independent hypothesis must demonstrate a meaningful whole-product *locality or cost* advantage beyond cheap grouped controls, including actual metadata physical I/O, source/reader memory, maintenance and decoder costs, and a generic admission path.

## Honest charged model and caveats

- Source `tools/research/o128_grammar_navigation_oracle.py` uses **real libzstd level-19 frames**; exact inputs generated without filename-extension or workload-identity admission; no CMPCT product imported.
- Both mechanisms use the same independently compressed exact 256-byte terminal blocks, 4B length + 32B SHA + 4B physical locator each; both charge fixed header, per-member path/32B digest/locator, metadata frame offsets, codecs and lengths. Every rule charges both child IDs and logical subtree span for range navigation. Creator search of up to 96 substitution rules is **gifted** and produces **zero product create-speed credit**.
- Full member bytes are rebuilt and hashed from terminal IDs, and selected-block range navigation independently checks 4 positions/member. Metadata Zstd frames are decompressed after encoding. A later code-only audit improvement ensures **each terminal Zstd frame** also independently decompresses to the exact original bytes; see subsequent exact-head run.
- A cold decompressed-work ratio counts **all grammar table + selected root block-ID control + selected 256-byte terminal**, not just terminal bytes. Grouped-control ratio counts complete selected group control frame + terminal. In neither path is actual filesystem/open/seek latency or RSS attributed to a real CMPCT Reader. Storage bytes are an oracle modeling separate physical frames, **not r24 wire bytes**.
- Synthetic 256-byte boundaries are gifted; true generic boundary discovery, charged encoder search, update/index mutation, authenticated physical recording, recovery, portability, owner races and hostile inputs remain untested. No real independent solid benchmark workload or formal ZIP/Deflate-9 comparator was run.

## Correctness / self-review / next action

The initial lower-rung code had reconstructed terminal bytes from the retained raw dictionary, without independently **decompressing each terminal frame**. This is an evidence gap, not proof of a false ratio. Patch `8cc80570cd77b0d2d2f8257e2dcf178f3e7682c9` adds exact terminal frame round-trip, preserves all fixed inputs/controls and leaves any negative alive. Its hosted exact-head run and final documentation HEAD must be reported separately: initial run success alone cannot certify the patched frame verifier.

**Highest-value unclaimed next route:** after final exact-head status, retire *this precise binary reference-index grammar storage-size proposal* and prioritize product integration/economics already owned in #336/#442/#468/#472 and source-history custodians #431/#473. Only reopen A07 as a materially different *self-index + access/recovery* design after a cheap grouped-frame control already demonstrates enough unexploited whole-system locality/storage headroom. Do not touch the central Discovery cache currently owned by #440. All numeric releases, r24 law and historical benchmarks remain unchanged.
