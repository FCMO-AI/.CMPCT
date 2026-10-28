# J24K07 — signed STORED/retained VZIP suffix-coordinate court: result

Date: 2026-10-28 UTC. **Scientific correctness evidence, NOT product fix or release evidence.** Source parent [#642](https://github.com/FCMO-AI/.CMPCT/pull/642) frozen at `78bc1f552fee24970228f89ac25dbf23307b0406`. Preregistration first child commit `43143cee44c064eb6f886181a64d5a97e34fc926`; experiment source commit `8b61002505c6567ecae5d2b02bac6af178a88379`. No code in `src/`, original goldens, Reader, codec, validation, native engines, format, version, or frozen evaluators was changed.

## Primary question and decision

**CONFIRMED in the two preregistered Builder-independent revision-24 goldens:** a fully reauthenticated index can contain a STORED or retained-mode1 `csize` lie of +1/-1 and cause ordinary `CMPCT.read_range` to return **an incorrect byte of the requested exact length** at a later suffix coordinate. Strict `preflight_archive`, complete `read()` and `verify()` reject every mutant. Thus `len(result)==requested_length` prevents short reads but **does not establish correct coordinate ownership**.

This extends #623/#640 and is distinct from #642's regenerated Deflate mode2 proof. Prior to this activation the STORED/retained adjacency was explicitly a falsifier pending hosted execution.

## Source-exact hosted evidence

[GitHub Actions scientific court #40635350564](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635350564) finished **SUCCESS** on Ubuntu 24.04, macOS 14 and Windows Server 2022. All three jobs installed CMPCT noneditable and checked:
- source HEAD `8b61002505c6567ecae5d2b02bac6af178a88379`;
- unchanged Reader blob `b37b786966ac1506a0439567d4a58eea472d85f8`, codec `a5e5fd0cdaff9001d4d00e131c163c8768adc2b0`, validator `0614723549403f398a43552a7c5ad3f00fbec688`;
- unchanged STORED golden blob `1f199cafb40ca487263ed421e0d0908402ae6c3f`, retained mode1 golden blob `06381fab57609252bfb9b887e33c2bdd480de681`;
- physical bytes identical between legitimate and mutant archives; identical newly SHA-256-authenticated primary and tail index copies;
- positive original read/ZIP/SHA/verify and inherited J24K06 mode2 tests;
- **15/15 pytest PASS per OS, 45/45 total**, with the 4 mutation cells per host all confirmed and raw artifacts persisted.

| Authenticated hostile mutation | Original length | Declared length | Wrong-byte one-byte queries / queried suffix offsets per host | First erroneous coordinate | Mutated archive SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| STORED, csize -1 | 128 | 127 | **39/75** | 52; `01` instead of `4b` | `f0c06237fc0ef5572b7f79f831201d59e74d83d092495026aab6804274abfb66` |
| STORED, csize +1 | 128 | 129 | **40/76** | 52; `50` instead of `4b` | `01ffa1a7acb9b2ee46cef607ac843ea1061c870552fbe22dbe92c159194857a4` |
| Retained Deflate mode1, csize -1 | 130 | 129 | **41/75** | 54; `01` instead of `4b` | `294b1c902156b09ce78779a30ae8bf328cd486bb8046c3d5d1ce6e997bb64a0b` |
| Retained Deflate mode1, csize +1 | 130 | 131 | **42/76** | 54; `50` instead of `4b` | `d9b89ac99344a4b6c27fea54d72bb6e3cafe188f811effcf99dfd508a7b5ebc2` |

Each host observed the same four mutated archive hashes, same first wrong bytes, same 162 wrong-byte probes out of 302 attempted suffix offsets. There are 12 hosted mutation observations across platforms, but **only four distinct signed mutants**: do not treat 486 duplicated wrong-byte probes as 486 independent cases. There were zero rejected suffix probes and zero truncated one-byte results in the scoped grid.

Hosted artifact IDs: Ubuntu [12793536383](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635350564/artifacts/12793536383), macOS [12793880376](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635350564/artifacts/12793880376), Windows [12793655990](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635350564/artifacts/12793655990). Original fixture/source SHA and test stdout are present in each artifact.


## Held-out third mode0 source: J24K07b (independently preregistered after initial observation)

Prospective held-out experiment was frozen at commit `76e61ed9d52df20d5a1e8c0afa4201ba36c850d3` **before** the new independent canonical-mode0 test. It used the already immutable `v24-virtual-zip-deflate-mode0.json` SHA `9fa44e064af01a2fdc7402881bb89d9449cbc5de6a26563d05f71b812af0c224`, and a source-exact canonical `CODEC_DEFLATE` owner instead of STORED or retained mode1. No original outcome/corpus/test was rewritten.

[Second 3-host scientific run #40635939312](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635939312) finished **SUCCESS on Ubuntu, macOS, Windows**, each with **17/17 pytest PASS** (51/51 total), exact source head `7a14cd023543c4dbf1587e6b4465afde36d43cf3`. The canonical-mode0 signed mutations were:

| Canonical Deflate mode0 mutant | Original length | Claimed length | Wrong-byte suffix queries | First incorrect coordinate | SHA-256 signed archive |
|---|---:|---:|---:|---:|---|
| `csize -1` | 130 | 129 | **41/75** | offset 54; `01` instead of `4b` | `2ae514672fbb3a11090067b043e4e5ae61f7f7677344612881a5b5c2865b3557` |
| `csize +1` | 130 | 131 | **42/76** | offset 54; `50` instead of `4b` | `7e6338f53362546e805d816207fe4ffc4d1233579165e0221a9f2d25c1bd4d10` |

Existing strict preflight rejected each *specifically* with `recipe 0 canonical Deflate stream 0 size/codec mismatch`. Whole read and verify rejected, but each queried suffix produced exactly one byte with 41–42 mismatches. The two source-original J24K07 modes also passed with **precisely named** `stored payload` or `retained stream` physical disagreement rather than an unrelated parse failure. On all three hosts, **six distinct mutants** had identical hashes and same errors: **245/453** one-byte suffix positions returned wrong bytes with no rejection or truncation **per host**. Across platforms those are 18 observations, not 18 independent mutations.

Independent artifact-level Python-standard-library audit downloaded the three original ZIP artifacts and recomputed all six receipts, checked source SHA and actual pytest output, found exactly the six preregistered case×delta combinations, and confirmed identical normalized JSON across all hosts. Audit receipt SHA-256 `9c9cd038ff1f2ebc5a49e23231aaa651fcc8cd457ec226ff554c9dc4731c3a01` (available as supporting run artifact in conversation; raw hosted source artifacts are under run #40635939312). This audit corroborates raw receipts, not an alternate Reader or decoder.

**Updated conclusion:** All three non-mode2 VZIP payload classes (STORED/mode0 method, canonical Deflate stream mode0, retained Deflate mode1) have the same skipped-`csize` coordinate-owner gap in ordinary `read_range()`. The strongest bounded product solution remains to reuse the existing `_validate_recipe` geometry against the same effective authenticated index **once per recipe** at Reader admission or first VZIP range, with explicit lazy/eager CPU/RSS/cold-open comparison. Do not conflate this with regenerated mode2 compression proof (#642) or whole-content SHA authentication.

## Causal diagnosis and strongest simpler control

`range_vzip()` checks physical lengths of **overlapping** streams and of **skipped mode2 regenerated** streams, but trusts the signed `csize` of skipped STORED/mode0 and retained Deflate/mode1 streams to advance the logical position. That can choose the wrong suffix byte even when the result length is exactly one and the index checksum is valid.

The existing `validation._validate_recipe` already has a bounded authenticated **metadata** proof for all non-mode2 cases:
- STORED: `csize == blobs[raw_ref][1]`;
- retained mode1: `csize == blobs[stream_ref][1]`;
- canonical mode0: `codec == CODEC_DEFLATE` and `csize == blobs[stream_ref][2]`;
- skeleton sum and total projection equal their authenticated physical/recipe sizes.

The ordinary Reader constructor only invokes `_validate_storage` on sparse/CDC/chunked files, **not** on S_VZIP, so the stronger preflight evidence does not automatically protect read_range. A generic, bounded first-use or pre-open authenticated recipe geometry proof is the leading follow-up; repeating full stream decompression is not necessary for the three non-mode2 branches. For mode2, a purely metadata-level compressed length proof does not exist under current revision 24, so #642's measured recompression debt remains a separate design problem.

## Negative evidence and alternative explanations

- The same hostile files are rejected by strict preflight, full read and whole-file SHA/verify. This is *not* a successful SHA-256 collision, forged external signature, reader escape, data exfiltration, or out-of-bounds memory access.
- The test set contains only two original structural goldens and one-byte `csize` perturbations with positive suffix queries; no general worst-case claim. Other recipe modes, multi-stream interplay, resource exhaustions, repaired Reader branches and the native Rust ABI remain unmeasured.
- A source-independent mathematical 2,500-case/5,000-mutation oracle found displacement under variable nonuniform suffixes, but also shows that **uniform suffixes can hide shift without proving correctness**. This oracle is separate L1 mechanism illustration and receives no product or full-Reader proof credit.
- Full cold-open/wall/CPU/RSS, selective physical I/O, large-VZIP workloads, and official release parity were not measured. J24K07 itself changes no product behavior.
- Engineering Evidence initially failed on a required PR heading, since corrected in PR metadata; the failed first run is preserved rather than relabeled.

## Next decision and transfer

The next material intervention should **compare** metadata-only proof at ordinary Reader admission or first VZIP use against per-range proof before changing product code: correctness of every supported storage/stream mode, same effective authenticated index, bounded memory/time, one-time validation per recipe, concurrent Reader safety, and cold-open tradeoff. Independent source owners [#638](https://github.com/FCMO-AI/.CMPCT/pull/638) and [#642](https://github.com/FCMO-AI/.CMPCT/pull/642) should coordinate this; do not duplicate their implementation branches.

The J24K06 prefix verifier remains correct but incurs high suffix recompression (up to 1,048,576:1 input-to-returned-byte in its scoped study). Mode0/1 need not inherit that cost if authenticated blob metadata is used correctly. Preserve this separation in future performance claims.

**Decision:** J24K07 hypothesis corroborated on all predeclared cells/OS; issue family broadened from short-read + mode2 offsets to *authenticated physical projection not consistently enforced by ordinary selective Reader*. No product merge or release.
