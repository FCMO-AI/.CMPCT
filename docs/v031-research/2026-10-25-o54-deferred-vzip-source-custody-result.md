# O54 — Real installed O50 deferred VZIP split-read source-custody result

Date: 2026-10-25 UTC
Status: **DECISIVE SCOPED NEGATIVE FOR ORIGINAL O50 BUILDER**; research only.
Pre-registration: [O54 prereg](2026-10-25-o54-deferred-vzip-source-custody-prereg.md) landed first at `be7d2c42a5c7a6d1d603555224f1b8d7f8e516c2`.
Source-bound test/CI at `377fe5887d30b53b636491f918fdca918d702743`, inherited unmodified O50 `src/cmpct/builder.py` Git blob `21a9ec696df13961c25301654feb607a7e161a4c`.
[Full actual hosted scientific run #40163268238](https://github.com/FCMO-AI/.CMPCT/actions/runs/40163268238). Draft research [PR #410](https://github.com/FCMO-AI/.CMPCT/pull/410); Builder product owner [#405](https://github.com/FCMO-AI/.CMPCT/pull/405), tracked [Issue #408](https://github.com/FCMO-AI/.CMPCT/issues/408).

## Exact observed result
| Host | Actual installed tests | Source pivot | Builder outcome | Reader ordinary read | Reader explicit verify | Artifact |
|---|---:|---|---|---|---|---|
| Ubuntu 24.04 | 3/3 PASS | same inode, 4214 B → 4214 B | emits 1198 B r24 | `OSError: virtual ZIP reconstruction mismatch` | same | 12587581685 |
| macOS 14 | 3/3 PASS | same inode, 4214 B → 4214 B | emits 1198 B r24 | same | same | 12586544523 |
| Windows 2025 | 3/3 PASS | same inode, 4214 B → 4214 B | emits 1198 B r24 | same | same | 12587017618 |

All three CI jobs executed effectively and concluded SUCCESS because their *scientific assertion* was that the real original Builder emits an unverifiable archive; this is **NOT** a product safety PASS. Immutable ZIP_A and ZIP_B each separately form authentic CMPCT revision-24 `S_VZIP` outputs with exact round trip and explicit `verify()` PASS.

The deterministic interleaving uses a real valid ZIP_STORED A and a same-length, different-SHA valid ZIP_STORED B, both one inner entry, changing *the bytes of a single existing ordinary inode* immediately after `codec.make_vzip_recipe` captured original A and before its independent `ZipFile(path)` parse. The original source remains regular, rooted within the source tree, and its device/inode and byte length are unchanged. There is no symlink, FIFO, path alias, root traversal or pathname replacement. The mutator fires exactly once; original real Builder/Reader and SHA/CRC validators are unchanged.

Ubuntu/macOS synthetic ZIP_A SHA `c510e30a6c8cde3b3ff6587b337778a16f3b18f705bb018383cd3ab433fdea8b`, ZIP_B SHA `0fcba172e5061c918ba997c5f4b85b1a4ae1094bbc5310e45f1a368dccd07b7f`; physical emitted invalid r24 SHA `2824391e382dbd5a7e5900f4a49919d394ed8ae326de5d6f8a5da9134450a2c1`. Windows generated ZIP_A/B bytes differ in host metadata and have different SHA, but equal sizes and same source-inode continuity; Windows invalid r24 archive SHA `85669cbc34258ae34b874d4967892924777afbb3e11479a374f42d2e20591fe6`. Do not claim cross-platform binary identity.

Original artifact ZIP SHA-256: Ubuntu `0d38824fb8f70c97ae138b3e1c551523d050ad5170f03dbeec290a72dcfdfef7`; macOS `ac1e1291bcc9ebaaadc9ed06077588ec74d15b7272867cad30fd7fd5c12ec9dc`; Windows `6adf890c8bee5f90982441715c9aedab9626588213d58083575dd9089678a47b`. Raw JUnit, JSON and full logs retained per host by CI (30-day artifact retention). No independent complete binary-byte audit of those ZIP downloads was performed in this activation; claims about results are based on exact logged source, JUnit and artifact metadata.

## Mechanism, stronger controls and scope
- Original `codec.make_vzip_recipe`: reads `original=ap.read_bytes()`, separately opens `ZipFile(ap)`, independently opens `open(ap,'rb')` for physical offsets, then derives a recipe from potentially different temporal data; Builder later re-reads the path for an otherwise discarded row-level hash on this `S_VZIP` branch.
- A statically correct `(st_dev,st_ino)` check or a source-rooted `dir_fd` is **insufficient alone** to guarantee content consistency when the same inode can change in place. This is distinct from O52's pathname root-escape and FIFO results.
- Actual CMPCT Reader safely *detects and refuses* the malformed virtual ZIP on read/verify. It does **not** prevent Builder returning success for an internally unreconstructable physical archive. No undetected plaintext tampering or SHA collision was observed.
- Mathematical lower-rung reproducer with independent stdlib ZIP_A skeleton + ZIP_B stored member yields a hybrid ZIP whose CRC fails; it does not replace the true product-hosted result.
- This demonstrates a deterministic possibility under orchestrated concurrent source mutation, not real-world frequency, remote exploitability, network-filesystem behavior, general snapshots or other representations.

## Counterfactual and bounded next action
A static inventory of the independent opens (initial `ap.read_bytes`, `ZipFile(ap)`, `open(ap)`, Builder `p.read_bytes`) could have predicted the source-custody ambiguity before any full product test. A single tiny stored ZIP with same-inode equal-length perturbation was enough to decide the original hypothesis; no full frozen benchmark was justified.

**O55 reference hypothesis** was separately preregistered after observing this negative: make the already-captured `original` buffer authoritative for every virtual-ZIP parse/extraction step. Source reopens and exported buffer copies/memory/CPU need measurement; any actual Builder implementation must be coordinated with owner #405/#408, preserve ZIP/WHL S_VZIP/VZIP-fallback, packed cohorts, symlinks, xattrs, hardlinks, sparse/CDC, old archive reader and exact official ABBA/portability checks. O55 is an *oracle*, not a product patch.

No product code changed, no benchmark/proof/release threshold changed, no `STATE.json` shared state mutation, no canonical merge/format/version/release. Scientific decision: **O54 `EMITTED_UNVERIFIABLE_R24` on Ubuntu, macOS, Windows**.
