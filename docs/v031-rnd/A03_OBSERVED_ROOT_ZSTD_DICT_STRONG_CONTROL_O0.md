# A03 independent stronger control — observed-root Zstd dictionary vs grouped XOR residuals (O0)

**Status:** SCIENCE ONLY / `SCOPED HEADROOM, NOT PRODUCT` — 2026-10-19. This is a new, dependency-safe **representation control**, not a CMPCT format change, source implementation, CI promotion, or new version.

## Authority and question

- Based on `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, released v0.30.0/r24, `docs/ASSUMPTION_LEDGER.md` A03.
- `docs/ACTIVE_RESEARCH_THESIS.md` keeps the efficiency-recovery directive higher priority than discretionary Foundry work. No new Foundry thesis is activated.
- There was no A03 PR or active A03 implementation claim in the inspected open-PR inventory. This separate branch does not alter existing product owners.
- Pre-result hypothesis: can mature Zstd raw-dictionary/`--patch-from` compression using the **same charged observed source base** explain away the research-only grouped-XOR positive? A raw dictionary is a simpler reconstruction abstraction with potentially lower selective work; it must not receive a free 128-KiB basis.

## Controlled method

The inherited A03 O0 court uses **12 × 131,072 bytes** from deterministic source generators. Same-input comparisons here use two independent seeds (20261101, 20261231); five independent byte-edit densities (0.5%, 2%, 5%, 15%, 40%); 2%- and 15%-density scattered 128-byte block edits; Zstd levels 3 and 19. Total **28 source/level cases**, each with five physically materialized arms:

1. Direct Zstd group-six and unrestricted direct solid group-twelve.
2. Observed medoid base + XOR residuals compressed group-six.
3. The same observed medoid base stored once, plus **dictionary-compressed direct source members**, in individually decodable frames (g1) or groups of up to six (g6).

Every research capsule charges the compressed root, all frames, serialized MessagePack file/group indices, source SHA-256, group physical and reconstructed-content commitments, decoder-visible reference selection and framing. Base search is an expensive gifted medoid oracle, **measured separately** and NOT credited as product runtime. Source data, roots and codec levels are identical between candidate and controls. Both native Zstd and Python-level XOR constructors include CLI process time; reported wall-time is research-constructor time, not CMPCT creator time.

**Scope of claims:** these are independent research capsules, not archives produced by a CMPCT revision-24 writer. No generic source detector, product cost, or current r24/r25 control is established.

## Decisive results — Zstd level 19

| Source shape | XOR g6, seed 20261101 | Dictionary g6, seed 20261101 | XOR g6, seed 20261231 | Dictionary g6, seed 20261231 | Decision |
|---|---:|---:|---:|---:|---|
| 0.5% independent edits | 163,643 B | 157,157 B | 163,026 B | 157,190 B | Dictionary wins both |
| 2% independent edits | 228,289 B | 215,645 B | 229,138 B | 215,747 B | Dictionary wins both |
| 5% independent edits | 347,602 B | 326,145 B | 348,729 B | 330,512 B | Dictionary wins both |
| 15% independent edits | **605,824 B** | 678,187 B | **608,718 B** | 677,990 B | **XOR wins 11–12%** |
| 40% independent edits | 1,178,472 B | 1,369,143 B | 1,176,038 B | 1,369,620 B | **XOR wins ~16%** |
| 15% scattered block edits | 378,424 B | **376,236 B** | 376,828 B | **374,915 B** | Small dictionary win (~0.5%) |

All byte counts include full research capsule metadata. These numbers must be checked against the committed raw experiment output before quoting beyond this court.

Across all fourteen level-19 cases, dictionary g6 is smaller in **10/14**; XOR g6 retains a material >=5% and >=8,192-B win in **4/14**. At level 3, dictionary g6 wins 5/14. Hence the general A03 grouped-XOR benefit **does not survive a mature simpler control in most tested regimes**; a high-density independent-substitution seed remains.

Independent reader replay reproduced all **56 dictionary arm archives** (2 per 28 source/level cases), source SHA identity and exact reconstructed members with stable archive hashes. For the 15%-independent case, independent reader source SHA is `25be14db45464ced229f2a1469005632aa5dbd5648a47db3b2b272066db932a5`, matching the inherited A03 materialized XOR capsule. Two targeted encoded-payload corruptions were rejected. This is not a hostile parser/fuzz/recovery/portability court.

## Whole-system tradeoffs and negative evidence

- Dictionary g1: at most **2× logical decoded work** for a member (base + target). Dictionary g6 and XOR g6: at most **7×**. Unrestricted direct solid: **12×**.
- On the 15% independent same-input source, dictionary g6 **678,187 B** versus XOR g6 **605,824 B**, but with six interleaved research-constructor executions each, median wall was **0.429 s** versus **0.866 s** (first seed), and **0.392 s** versus **0.772 s** (second). These are Python+CLI measurements; native product behavior remains unmeasured, and XOR's Python byte loop is a possible confound.
- On 15% scattered-block changes, dictionary g6 was slightly smaller and took ~0.24 s versus ~0.32 s for the paired XOR research constructor. Small byte wins are below materiality; both should remain controls.
- The experiment's synthetic source structure may not describe real project trees. Product representation and admission search can erase O0 gains. Dictionary compressor requires an authenticated decoded root; count both root decode and all group work. No product credit from this result.

## Decision and next cheap discriminator

**NARROW A03.** Do not generalize the original 4/5 density wins when those were only against direct/XOR-independent controls. Prefer mature native dictionary/reference compression as the stronger baseline in future A03 research. Preserve the grouped-XOR result specifically for diffuse independent edits at >=15% in these source generators. Block-correlated edits are a hostile structural negative for XOR.

**Highest-value next decision:** test existing actual CMPCT r24/r25 delta/graph/solid mechanisms on a *versioned real family* with the same complete semantics and exact source, **before** implementing another residual-factor representation. If their complete size/create/read economics beat this oracle, retire A03 as product priority. Keep the efficiency-recovery/Issue194 product critical path primary.

Counterfactual prospective discriminator: changing the spatial arrangement of edits at fixed density (independent byte scatter vs 128-byte blocks) plus a native raw-dictionary control would have narrowed the claim earlier. This does not yet justify changing Discovery Engine policy or release law.

## Evidence integrity and promotion boundary

Preregistered question/controls/kill rule before this measurement. Raw matrix 28 rows: SHA-256 `3be93c412a3be67f394909f45a5ed7bd005edaaffb18d80234b01d9108ff7d97`. Independent 56-arm replay: `89d1f1846165626857347e99c42cd699ef134d882ef60b57ffdf2172936165e1`. Paired timing (48 arm executions): `a877142361f014bb27f9b0174449c88d5966168ecd557249cefa2585e70ea799`. The complete runnable files, generated capsules and hash-manifest are in the activation's exported research capsule; these SHA values identify the local evidence and **do not imply** the evidence JSON has been committed here.

No frozen workload, thresholds, comparator semantics, source release, format, `STATE.json`, or policy was modified. Product promotion **0**; release promotion **0**. This result is an isolated scientific frontier update, not a CI pass.
