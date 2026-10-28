# J24K08 — equal-total VZIP literal partition: final scoped scientific result

Date: 2026-10-28 UTC. **Proof-scope / representation discovery, not a product vulnerability, fix, release or benchmark.** Preregistered in first child commit `1499792cdb84c44a9a1edca300332e6044c7d6ab` before instrument `22abd24ae557a5b16a3206cec5c750e904bfad12`, source-exact scientific HEAD `9ff7a2263436f6b03843640f19d1b1d98413a7ad` (base #642 `78bc1f552fee24970228f89ac25dbf23307b0406`).

## Primary question: does exact physical projection authenticate literal boundaries?

**NO, confirmed** for the one preregistered genuine Builder-independent revision-24 golden. Keep current `S_VZIP` physical blob table and stream compressed size identical, keep original file/recipe SHA and CRC, but change two literal lengths `[39,77]` → `[40,76]` while preserving total 116 skeleton bytes and logical file size 130. Both physical index copies have newly recomputed identical SHA-256; these are self-consistent *unkeyed index digests*, not external signatures.

| Observation | Original archive | Reauthenticated literal-boundary mutant |
|---|---|---|
| Physical data bytes | identical | identical |
| Skeleton literal sum | 116 | 116 |
| Deflate csize | 14 | 14 |
| Logical claimed bytes | 130 | 130 |
| `preflight_archive()` | ACCEPT | **ACCEPT** |
| Full `CMPCT.read()` | PASS and original SHA/ZIP | **REJECT**, retained original content checksum fails |
| `CMPCT.verify()` | PASS | **REJECT** |
| `read_range(name,39,1)` | `cb`, first stream byte | **`50`**, first byte from different skeleton position, length exactly 1 |

The original source golden archive SHA-256 was `9fa44e064af01a2fdc7402881bb89d9449cbc5de6a26563d05f71b812af0c224`, mutated archive SHA-256 `4cc8dd314b98a8849e2b660ee266a4101b535a1fc8711a228233397d15145c59`, and unchanged physical body SHA-256 `c8516eb24a9be58c0e978ee1dc5ffa3aebae71047abfc4afdf5ce2db3786afb2`.

This is **a proof boundary**: exact size projection and physical ownership do not imply that original full-content SHA / CRC remains valid under a different logical interleaving. Whole-file checksum correctly identifies the contradiction; range-only requests do not compute whole-file content hashes, and the current API should not be described as fully authenticated per-range access without an explicit additional guarantee.

## Primary hosted evidence and independent referee

[Actions #40636176349](https://github.com/FCMO-AI/.CMPCT/actions/runs/40636176349) completed **SUCCESS on all three Ubuntu 24.04 / macOS 14 / Windows Server 2022 jobs**, one exact preregistered test passed on each (3/3). Exact source Reader Git blob `b37b786966ac1506a0439567d4a58eea472d85f8`, codec `a5e5fd0cdaff9001d4d00e131c163c8768adc2b0`, validation `0614723549403f398a43552a7c5ad3f00fbec688` and golden fixture `663b9fdb4df560fb9572fa14bf003928a2379e5e` were unchanged and checked before each hosted installed run. The 8 requested one-byte offsets all matched across OS; at offsets 39,40,41,52,53 the candidate yielded correct-length bytes different from original, and at 37,38,54 it matched. Original full ZIP/SHA/verify was positive in each run.

Hosted artifact IDs: [Ubuntu 12793742397](https://github.com/FCMO-AI/.CMPCT/actions/runs/40636176349/artifacts/12793742397), [macOS 12794080120](https://github.com/FCMO-AI/.CMPCT/actions/runs/40636176349/artifacts/12794080120), [Windows 12793492061](https://github.com/FCMO-AI/.CMPCT/actions/runs/40636176349/artifacts/12793492061). Independent stdlib-only audit downloaded the actual ZIP artifacts, verified head identity, exact single receipt per OS, pytest PASS and byte-for-byte JSON equality across hosts. Audit output SHA-256: `2431f2ae675065edbed444d1cc2371ff2dafc94916b02186809a2b1bab8d6bc0` (separate local receipt). No alternate Reader or decoder is claimed.

## Structural derivation — why the result is expected

Let physical skeleton `S=A || B` with `|A|=39`, `|B|=77`, and physical Deflate stream `C` with `|C|=14`. Original interpretation: `A || C || B`. With one-byte literal repartition `B=b || B'`, candidate interpretation `A || b || C || B'`. Both output 130 bytes, both consume exactly the same `S` and `C` bytes, and both satisfy all size/projection equations. At offset `|A|=39`, original byte `C[0]=0xcb`; mutated byte `b=0x50`. This is a counterexample to *size projection ⇒ semantic byte identity*. The original whole-content hash disambiguates them only by full verification or a separate authenticated range-proof mechanism.

With a single payload and fixed skeleton length `S`, purely length-consistent interleavings permit `S+1` placements of a stream, not all semantically equivalent; this explains why geometry alone cannot decide which interleaving matches an external expected original hash.

## Relevant negative and self-critique

- **Do not call structural preflight defective for accepting this** without showing its advertised contract includes whole-file CRC/SHA verification. It currently enforces structure, not content.
- **Do not call the queried range cryptographically authenticated**: an unkeyed index digest and an unchanged full-content hash do not provide independently verifiable per-range integrity. The current byte-returning API may intentionally allow unverified partial data. The experiment characterizes the guarantee boundary, not an externally proven exploit.
- Only one 130-byte deterministic canonical-mode0 archive, one byte reallocation and eight offsets were exercised. Not a general fuzz, product performance or cross-format benchmark.
- No guarantee of data exfiltration, file escape or external signature forgery; original `verify()` correctly rejects.
- CPU/wall/RSS, cold open, selective physical I/O, extracted output and release gates remain unmeasured. Product code, wire format and published version unchanged.

## Architectural decision and next action

The direct J24K07 physical-coordinate issue and this semantic-authentication issue must not be conflated. For **physical bounds of unverified selective ranges**, the strongest safe smaller repair remains one-time metadata `_validate_recipe` geometry on the same effective index (at VZIP first-use or admission), addressing STORED/mode0/mode1 silently shifted csize with no payload decompression; mode2 retains separate regeneration proof and measured amplification debt (#642).

For **cryptographically verifiable selective content**, neither size equality nor cached metadata admission suffices. A separate proposed API/format design would need exact authenticated segment/extent commitments, proof depth and decoder work, and new format/version/interop contract if required, or explicit whole-file read/verify. Do not silently impose full-file recomputation on ordinary `read_range` absent a deliberate semantics/cost decision. This distinction itself is decision-changing L1 scientific evidence; no Discovery Engine policy amendment is earned.

**Disposition:** structural-projection-as-semantic-proof hypothesis falsified; preserve targeted physical-offset candidate without overstating its authentication claim. No merge or release.
