# O9 physical PACK ownership and singleton-bypass counterexample — terminal research result

**Date:** 2026-10-24 UTC. **DECISION: RAW S_PACK OWNER CONFIRMED; SINGLETON BYPASS HAS REAL HELD-OUT BYTE LOSS; UNCONDITIONAL PRODUCT PATCH REJECTED.** This is a source-exact scientific result with complete Builder+Reader reconstruction, **not** a release promotion or an optimized encoder.

## Prospective experiment and exact-head proof

- Frozen **before O9 test code**: `docs/v031-research/NATIVE_PACK_PHYSICAL_SINGLETON_O9_PREREG.md` at commit `fe06639573903ea5211b79fbb05541db55029250`, on existing PR #330 (O8/O8b/O8c already immutable). Inherited Builder/Reader/native product source was unchanged from PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae`.
- Final source-exact O9 **GitHub Actions run [40070636652](https://github.com/FCMO-AI/.CMPCT/actions/runs/40070636652)**, HEAD **`95b90cfc535f39b41bfd6f7b310b500e018b0362`**, terminal **SUCCESS**. Artifact **12551007703**, ZIP SHA-256 **`be88d12b7391e16a6b44fd4e91924a0100df44f73ccc1f8d6e8d8bd214bc3c4e`**, internal `result.json` SHA-256 **`0b854bd5f685ec66b5668ff24d61ed702d05359c131a8d77238d1ab13fc609b4`**; original `result.sha256` independently matches. ZIP tested uncorrupted.
- Direct **13 cases × three policies × two reproducible builds = 78 complete real r24 builds and 78 full ordinary Python Reader reconstructions**; each verified exact source member SHA and names, stable archive SHA across identical builds, SHA/CRC for each physical blob, S_PACK slice content hashes, index/physical framing equation, and non-mutated sources. Wall/CPU raw repeats, compressed/uncompressed indexes, physical codec, payload/frame and full archive bytes are in the immutable artifact.
- **Evidence-instrument negative kept:** first source HEAD `29d52baf270f69eebc4e05178935927db05e1623` run [40070446535](https://github.com/FCMO-AI/.CMPCT/actions/runs/40070446535) SUCCESS **but** a reviewer found its `physical_payload_bytes` incorrectly summed tuple codec IDs rather than compressed sizes; **do not use that field in the first artifact**. Corrected and constrained by an independent frame accounting identity in commit `95b90cfc`, reran exact-head SUCCESS and independently verified the corrected artifact. The unchanged direct archive-size and other non-payload fields of the earlier run remain diagnostic only; all quantitative conclusions below use the corrected final run.

## Original same-path O8c four families — physical truth

| Same paths/content | Distinct source SHA | Default archive | One-distinct bypass archive | No-PACK archive | Default physical S_PACK codec | Bypass minus default |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Related 256 | 256 | 4,505 B | 4,505 B | 32,041 B | **ZSTD** | 0 B |
| Independent high-entropy 256 | 256 | 199,562 B | 199,562 B | 225,870 B | **RAW** | 0 B |
| Exactly duplicated 256 | 1 | 1,491 B | **1,422 B** | 1,422 B | **ZSTD** | **−69 B** |
| Mixed 256 + 70KB | 257 | 172,651 B | 172,651 B | 200,608 B | **ZSTD** | 0 B |

**The paradox is resolved.** O8b/O8c native group discovery only admits **Zstd-compressed PACKs**; the 256 independent high-entropy .txt members nevertheless share **one real RAW physical S_PACK** (196,608 B physical payload; 196,672 B including one record header), thus save 26,308 complete stored bytes over materializing independently, without being native Zstd-batch eligible. Never equate `batch_count=0` with `no physical PACK`.

The exact 256-duplicate result can be attributed:
- Default one Zstd S_PACK: raw index 9,610 B, compressed index 597 B, physical framed record 161 B, archive 1,491 B.
- Bypass one direct S_BLOB: raw index 8,586 B, compressed index 561 B, record 164 B, archive 1,422 B.
- Net: index compressed **−36 B duplicated in primary/tail** (−72 B) plus physical frame **+3 B** equals **−69 B**. Removing the pack hint changes the inherited codec effort slightly, not the member identity; the Builder selected 95 B vs 98 B compressed payload. This is whole-product same-input evidence, not an isolated payload oracle.

## Held-out singleton and mixed-bucket counterfalsifier

| Held-out structure | Default B | Bypass B | No-PACK B | Bypass minus default |
| --- | ---: | ---: | ---: | ---: |
| Identical compressible text ×64 | 1,181 | 1,180 | 1,180 | −1 |
| Identical independent-looking noise ×64 | 1,852 | 1,848 | 1,848 | −4 |
| Identical all-zero ×64 | 1,106 | 1,100 | 1,100 | −6 |
| Identical compressible text ×256 | 1,427 | 1,414 | 1,414 | −13 |
| One compressible text file | 981 | 976 | 976 | −5 |
| One high-entropy file | 1,652 | 1,648 | 1,648 | −4 |
| One all-zero file | 906 | 896 | 896 | −10 |
| Two genuinely distinct repeated content blocks ×64 | 2,031 | 2,031 | 2,038 | 0 |
| **Cross-extension bucket: 32 unique .txt + 32 duplicate .json** | **2,403** | **2,413** | 7,631 | **+10 B LOSS** |

**The crucial negative is the cross-bucket case.** Its singleton bypass changes no encoded physical blob at all: both default and bypass contain physical frames **1,167 B**, payload **1,037 B**. The raw MessagePack index gets **128 B smaller** (2,550→2,422), yet its compressed index gets **5 B larger** (550→555); two authenticated stored index copies make the complete archive **10 B larger**. Therefore neither “fewer S_PACK wrappers” nor “smaller uncompressed index” is a sound monotonic admission criterion. Actual compressed dual-index representation must be charged. Unconditional one-distinct PACK bypass is **FALSIFIED** against a held-out alternative, even though eight cases improve.

**Aggregate:** 13 complete source families; O9 bypass wins 8, ties 4, **loses 1** versus unchanged default. This is no justification to alter global Builder policy, frozen release thresholds or to turn off micro-PACK generally; the independent high-entropy RAW pack and mixed family have large default advantages. The simplest original no-PACK control remains a real alternative, not a pretend oracle.

## Decision, strongest counterfactual, and continuation

- **Research claim confirmed:** codec-level physical census answers the opaque native-admission contradiction with one real RAW PACK. **Hypothesis narrowed:** one-distinct groups are often redundant but not universally cheaper to represent differently because the **compressed full index**, encoded twice, is nonlinear to raw index length.
- **Counterfactual prospective discriminator:** if the first O8 admission-negative had logged **physical S_PACK codec IDs and referenced blob ownership**, it would have distinguished RAW packing from no packing *before* buying multiple native C benchmarks. This is transferable as a harness preflight: measure whether the mechanism being benchmarked actually triggers, and at what physical representation/codec layer.
- **Next cheapest unclaimed scientific action:** quantify whether a tiny exact-final-form index admission comparison, *after* candidate grouping and before output publication, has bounded costs and generality on many independent families; compare the stronger simpler alternative of leaving singleton PACK untouched. Do **not** promote a heuristic based on uncompressed index length or a few saved bytes; additional dual-index compression/trial-work and maintenance could cost more than their benefit. The high-value adjacent mission is safe native grouped extraction productization with current owners (#327/#326), not unlimited tuning of this narrow synthetic family.
- **No product code, on-disk revision-24 bytes, ABI, reader/writer safety, historical v0.30 release fingerprint, Bounded Drift or shared `docs/discovery/STATE.json` was modified.** No performance/release credit. Subsequent general/native/CI checks on documentation successors are independent; a green workflow with a SKIPPED benchmark gives no ABBA proof.

**State transfer:** O9 data is decision-complete at exact `95b90cfc`; subsequent document commit is NOT itself an executed O9 result, so do not mislabel the proof's source SHA. Source identity for any future mutation must be reconfirmed against live PR #330. No discovery-policy change earned from this single experiment.
