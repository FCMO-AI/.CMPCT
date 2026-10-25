# O115 — A02 orthogonal-factor dictionary, charged oracle result

Date: 2026-10-25 UTC
Classification: **SCIENCE / CHARGED ORACLE ONLY; primary storage hypothesis falsified; bounded-locality Pareto seed conditional**
Status: RESEARCH RESULT / DRAFT PR #465 / NOT PRODUCT / NOT RELEASE

## Frozen authority and source custody
- Canonical development: `FCMO-AI/.CMPCT@agent/v031-development` `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, currently released v0.30.0 / on-disk r24.
- Immutable prospective preregistration committed **before instrument/results**: `4e37570b0247de1dbb37bc4648d408de4e13e7b1`, `docs/v031-research/2026-10-25-o115-a02-factor-oracle-prereg.md`.
- Code: `research/o115_a02_factor_oracle.py` (workflow-observed SHA-256 `dcd988e6bb92cfd51b56983c78b9a2446a1606694855263b7340b1481a48d4f8`).
- Result-bearing HEAD: `2820ca9a13de1d4d1b67a4e8620b5747f7c2f3f7`.
- Exact-head hosted GitHub Actions: [run 40231483763](https://github.com/FCMO-AI/.CMPCT/actions/runs/40231483763), job `121283965693`, **SUCCESS**, artifact ID `12613585828`, ZIP SHA-256 `8c7d685b981a2ffbc97ca9a4098be55023eaaf4c22645e99a28356d1f6da713f`. Embedded result JSON SHA-256 `f7945e1fda85de7758ee0bc5904e7fc71e924a4895d2e25c34e1b19714e9bfee` (timestamps differ from local). Hosted environment: Ubuntu 24.04, Zstandard CLI v1.5.7, level 19. Local initial run produced same bytes on all four families.
- Run is intentionally independent of CMPCT Builder/Reader, never a format-24 output or an official size/create benchmark.

## Hypothesis and five controls
A02 asks whether genuinely orthogonal latent factors shared across many objects support a more efficient exact reconstruction model than object-to-object explanations. The oracle is gifted slots, root bytes, factor dictionary and member assignments from the deterministic generator but must **serialize and charge** all decoder-visible facts. This generous discovery gift makes any storage loss a useful early falsifier.

All five models process *identical per-family original bytes* under the same Zstd CLI/version/settings:

| ID | Serialized information model | Selected member logical decode |
|---|---|---|
| S | One compressed stream of original file contents | Full corpus |
| I | Independently compressed originals | One original |
| R | Gifted charged root + independently compressed XOR residuals | Root + one residual |
| G | Gifted charged root + solid concatenation of all XOR residuals | Root + all residuals |
| F | Charged root + Zstd factor dictionary (each slot location, length, alternatives and bytes) + member assignment plan + exact fallback exception XOR residual | Root + full factor dictionary + optional exception |

Common metadata **64 + 40 bytes/file** (file logical length and SHA-256). Every model also charges its own member directory and additional ownership/descriptor bytes. Factor assignment bytes are serialized and accounted, with exception offset/size per member. The factor stream was actually decoded and parsed before rebuilding the originals. All models passed exact-byte checks and per-file SHA-256 checks. No compression-time, RSS, extraction throughput or true physical selective I/O claim is earned.

## Direct hosted result: fully charged stored bytes

| Frozen family | Files × logical length | S solid | R independent | G solid residual | F factors | F compared with best eligible control |
|---|---:|---:|---:|---:|---:|---:|
| Crossed orthogonal slots | 64 × 4096 B | **9,998** | 58,912 | 10,848 | 10,626 | **+628 B / +6.28% worse** |
| Correlated slot choices | 64 × 4096 B | **9,753** | 58,909 | 10,594 | 10,626 | **+873 B / +8.95% worse** |
| Held-out geometry, distinct seed/slots | 96 × 8192 B | **20,055** | 165,257 | 21,668 | 21,070 | **+1,015 B / +5.06% worse** |
| Independent random hostile | 64 × 4096 B | **265,296** | 270,253 | 269,437 | 273,602 | **+8,306 B / +3.13% worse** |

I independent: respectively 266,112 / 266,112 / 792,352 / 266,112 B. All four families completed `ALL_FIVE_RECONSTRUCT_AND_SHA256_PASS`; a distinct workflow audit checked population, complete model keys, stored bytes = payload + metadata, best-control selection, exact flags and declared win/loss, ending `O115_CHARGED_ORACLE_AUDIT_PASS`.

### Scientific interpretation
**Primary H1 storage improvement: FALSIFIED for this aligned fixed-slot dictionary representation.** Fully charged gifted F loses to a simpler **solid-original** Zstd baseline on *every* frozen family including held-out. No reason to tune offsets, token counts or sample seeds on these courts; inference/search overhead could only add cost.

**Secondary H2 locality: CONDITIONAL / UNPROMOTED.** In crossed-choice F occupies 10,626 B versus G 10,848 B and R 58,912 B, with modeled single-member decode of 7,208 logical bytes versus G 266,240 and R 8,192; S remains smaller at 9,998 B but needs a 262,144-byte solid logical decode. Held-out likewise has F 21,070 B below G 21,668, but above S 20,055. This suggests one local size-versus-selected-work Pareto point, **not** a universal compression gain or genuine measured selective latency/I/O advantage. Streaming Zstd decode and actual physical read amplification have not been measured; the model even grants gifted factor discovery.

## Strongest negative, contradictions and validity boundary
- The supposedly favorable crossed-choice corpus did NOT produce a storage win over S. This is more decision-changing than winning against the weaker independent or grouped-residual controls.
- The correlated-control F still pays all unused independent factor alternatives; all four case outputs are preserved unchanged.
- The independent-noise condition uses fully charged literal correction residuals; no dishonest discarded/unrepresentable records.
- The oracle does not model true full CMPCT member indexing, authentication per physical owner, source-search cost, update/recovery behavior, cold open, memory maximum, selective bytes physically fetched or required portability. Micro creation wall includes spawning different numbers of `zstd` processes, and is not a comparable product benchmark.
- One flat solid compressor depends on all-member decoding, a real product tradeoff. It does not negate a locality-oriented redesign; but F cannot claim global archive-byte domination from this result.
- No changes to existing format, encoder, Reader, goldens, release benchmark, disclosure history, performance thresholds or discovery policy. `docs/discovery/STATE.json` intentionally untouched (PR #440 currently owns cache reconciliation).
- No overlap with ongoing Builder/Reader/CI owners; isolated draft experiment.

## Counterfactual / no-go and next action
The cheapest prospective discriminator was the strongest solid-original Zstd control on the exact same bytes; it would have killed the **primary storage claim** before producing any new CMPCT storage kind. The additional root+solid-residual control preserved the smaller, genuinely different locality tradeoff. **Retire/narrow this fixed-slot A02 mechanism as an archive-size improvement; retain only an explicit conditional locality research seed**. Reopen only with evidence for generically discoverable factors, a measurable selected-read advantage over existing S_PACK/Mosaic alternatives and an end-to-end bounded admission path. Higher immediate product leverage likely lies in closing existing unmerged security/release-evidence owners, not another nearby factor variant.

### Release/evidence truth
Hosted science: **SUCCESS** on result-bearing HEAD; ordinary generic repository tests and official frozen performance are **not credited** by this experiment. Product files changed: **0**. New format/ABI: **0**. Merge: **NO**. Release: **NO**. New canonical scientific policy: **NONE**.
