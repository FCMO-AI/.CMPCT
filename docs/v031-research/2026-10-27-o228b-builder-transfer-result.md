# O228b — Builder-originated CDC virtual-run transfer: hosted result

**Classification:** `NO_BUILDER_TRANSFER_AT_THIS_SCALE` (**research-negative**, not a product benchmark, not a universal impossibility theorem). Frozen [preregistration](2026-10-27-o228b-builder-transfer-prereg.md) was committed at `9bcf813a9b20e30d5e5707db7cbe309a56d49537` **before** the experimental code `e7739e3b416929ea34b8f96fca4a3958dc2fb5fd`, independent auditor `b9c48bb0d5b384f2c399ad40e3f4efefa4efe476`, and hosted CI.

## Truth anchors (October 27, 2026 UTC)

- Released source: v0.30.0, revision-24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`; Builder original Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Hosted [run #40525914266](https://github.com/FCMO-AI/.CMPCT/actions/runs/40525914266), scientific job **SUCCESS** at exact merge checkout `1ba3413075b6342390c41af9d5abfc44a08aaecc` from source branch `76c37b56edb9bbbd6cfbef003ce5b48443aa32b6`. Both the experimental court and a separately authored result referee executed. The result is bound to the unchanged experiment source bytes, not later documentation commits.
- Original [artifact #12744401663](https://github.com/FCMO-AI/.CMPCT/actions/runs/40525914266/artifacts/12744401663), ZIP SHA-256 `6660a085802937db56446c81a96da7b31ee2e0214bd64e87e0692daa642b409d`; raw JSON SHA-256 `1e856ff354a8353552325a94f5a55746b8c2b0e5491b909bbd4bac30bbe2a120`.
- Independent second-root review **PASS**: original hosted artifact ZIP downloaded; CRC verified; ZIP checksum manifest verified for all three contained outputs; individual decoder peaks recomputed from 36 subprocess observations; charged dual-index byte deltas and prospectively frozen decision recomputed independently. The two Python source files are not inside the ZIP: their identities are recorded in the GitHub job logs, current Git paths and JSON source hash.
- Experimental platform: Ubuntu 24.04 / Python 3.12.3, authentic editable v0.30.0 package with its Rust core. Input corpus is seeded/deterministic six genuine 16-MiB one-file source trees; this is not external corpus generalization.

## Results: archive-level charges and negative controls

All genuine Builder archives emitted only **64 S_CDC references** for each 16 MiB logical file, compared with O228 synthetic's 262,144 logical references. Candidate `S_CDC` run form is a **hypothetical in-memory alternate index**; there are no new physical-format tags written, no product Reader changes, and no archive claim that future Readers accept it.

| Source family | Original complete archive (B) | CDC refs → runs | Original vs hypothetical Zstd12 index (B) | Charged hypothetical whole-archive delta (B) | Decode heap literal/run ratio |
|---|---:|---:|---:|---:|---:|
| All zero | 1,015 | 64 → 1 | 394 → 387 | **−14** | **3.807×** |
| One 1-MiB random period repeated | 1,049,818 | 64 → 64 | 425 → 426 | +2 | 0.942× |
| Two random periods repeated | 2,098,714 | 64 → 64 | 457 → 457 | 0 | 0.946× |
| Shifted/drifted period | 16,782,978 | 64 → 64 | 765 → 772 | +14 | 0.975× |
| Structured records | 3,506 | 64 → 64 | 485 → 488 | +6 | 0.951× |
| Independent random | 16,782,972 | 64 → 64 | 762 → 767 | +10 | 0.975× |

Full archive delta formula: `2 * (alternative_compressed_full_index_bytes - original_compressed_full_index_bytes)`. Physical blobs/headers/metadata remain the identical original Builder record set. Candidate index generation CPU was measured and included in receipt, but only a fully integrated future Builder could establish a usable release artifact. Decoding ratios compare **MessagePack unpack heap only**, not full RSS or Reader open.

Original files passed reader `verify()`, whole-file SHA-256 and selected genuine range reads. Logical repeated-reference expansion hashes matched exact (length,owner) sequences on the prospective index.

**Prospective result:** zero nontrivial families satisfy the joint >=8 run / >=2× unpack heap / non-increased archive bytes condition. The all-zero family is a real source-pattern positive but too trivial and small to satisfy the multi-family test; no other sample had an adjacent same-owner run >1. The family is therefore *narrowed*, not asserted universally impossible. O228's large-N synthetic representation headroom remains valid evidence, but the ordinary released Builder does not trigger that regime at this source scale.

## Mechanism, counterfactual and strongest self-critique

Code inspection prior to implementing this court could already have exposed a useful lower bound: `CDC_MIN=128 KiB`, so 262,144 real CDC references imply >=32 GiB of logical data, unlike synthetic 64–88 B references. Current `Builder.scan()` emits S_CDC rather than S_CHUNKS for ordinary large regular files; S_CHUNKS remains a valid reader/legacy grammar, but is not the ordinary Builder production path. This **source-derived cheap discriminator** would have prevented premature product credit even before this hosted test; the new court further establishes that repeating the physical byte pattern at 1-MiB granularity does not imply adjacent equal logical CDC chunk identities.

The largest uncertainty is **generality**: only six deterministic 16-MiB sources on one hosted Linux runtime, no genuine very-large-N Builder stream, no format revision/read/update portability/cross-platform experiment, no full memory attribution. Thus do not retire virtual sequence representations for massive generated files, legacy S_CHUNKS, or a different Builder. Avoid tuning run-length thresholds or reopening nearby synthetic experiments without structural transfer evidence.

## Decision and next owner-safe executable action

- Do **not** integrate unconditional run encoding or invent a format revision based on O228/O228b. Keep O228's synthetic large-run positive and this realistic negative together.
- Highest practical v0.31 priority remains owner #569's complete strict Reader admission/open-time regression and the independent extraction integrity work. The Reader owner may consider streaming structural validation or index ownership before introducing a new grammar, but must establish same-index authentication, true product economics and portability.
- Keep `docs/discovery/STATE.json` unchanged: owner PR #574 has the concurrent discovery authority/state reconciliation.
- No promotion, merge, release, weakened benchmarks, altered conformance, or changed code on `main`. Preserve this result as a bounded research falsifier that can stop premature implementation.
