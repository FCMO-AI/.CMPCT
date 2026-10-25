# O40 — Mixed-size S_PACK selected-member locality (2026-10-25 UTC)

**Decision: `SUPPORTED_SCOPE_SELECTED_MEMBER_GAP` as preregistered; source/format unmodified; no release credit.** An actual v0.30 shipping-r24 fallback may decode **754 times** the complete selected one-byte member from its cold Zstd owner even though its owner is only **1.0013× the globally largest regular member**. The 8× rule in shipping code uses a **largest-member proxy**, not an individual selected-file bound. The existing *frozen* 8× product-locality evaluator was not changed or run by O40; **do not present this finding as a failing frozen gate**.

## Independent source and host custody

- Question and kill criteria frozen first in [O40 prospective preregistration](2026-10-25-o40-mixed-size-pack-locality-prereg.md), commit `695a4951e8fd738a39f1e2b26fec4b06671ceebc`.
- [PR #394](https://github.com/FCMO-AI/.CMPCT/pull/394) on isolated `agent/phased2-v031-mixed-size-pack-locality-o40-20261025`, base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Exact source-bounded [GitHub Actions SUCCESS run #40147051382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40147051382), executed HEAD `f01eed36b9907089d2b68f591d62d94ac24c59ce`, job `121030518466`. Artifact **`12581222983`**, ZIP SHA-256 `1e6aa17443dcbe7400207b9cac87c4e002eff5e7a6654482ac36ccb6f40919d8`, retains full JSON, raw log and exit code. Scientific result is a **real executed measurement**, not a code-based estimate.
- Git source gate bound exact original Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, product front door `b6b87b5c2b2f50fe53114ad3b5d228cd1e887367`, and preregistration ancestor. Zero Builder/Reader/format, historic evaluator or release-gate modifications.
- Two earlier runs are transparently infrastructure failures, **not scientific negatives**: [#40146803829](https://github.com/FCMO-AI/.CMPCT/actions/runs/40146803829) failed `py_compile` from a generated source newline error; [#40146898697](https://github.com/FCMO-AI/.CMPCT/actions/runs/40146898697) built the genuine package and passed custody but lacked existing research-only dependency `zstandard`. The final source-only/workflow-only fixes repaired these issues without modifying the scientific acceptance criteria.

## Exact physical observation

All pairs are actual shipping `revision-24` archives. The smaller member was read first through `CMPCT.read_range` on a fresh Reader with an empty cache; a traced `_blob` call materialized the **entire S_PACK owner** and populated the cache. The independent physical owner SHA-256 matched the authenticated BLOB record. A second new Reader performed strong whole-archive verification and byte-exact reconstruction of both members.

| Source regular member sizes (B) | Full shipping archive (B) | S_PACK uncompressed (B) | Physical owner compressed (B) | Decode amplification versus small member | Decode amplification versus largest member | Singleton-control archive (B) | Singleton size debt (B) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **1 / 753** | **1,022** | **754** | 72 | **754.00×** | 1.0013× | 1,094 | +72 |
| **32 / 768** | **1,022** | **800** | 74 | **25.00×** | 1.0417× | 1,125 | +103 |
| **128 / 512** | 1,028 | 640 | 74 | 5.00× | 1.2500× | 1,117 | +89 |
| **512 / 512** | 1,015 | 1,024 | 75 | 2.00× | 2.0000× | 1,103 | +88 |

Preregistered classifications: **2/4** physically admissible mixed-size cases violate a hypothetical ≤8× **per-small-selected-file** decoded-work objective, and **0/4** breach the ≤8× **largest-member proxy**. The two remaining shapes are independently useful negative controls against a claimed universal regression.

The one-factor simpler control uses the original Builder on the same source tree, only `micro_pack_target=1` to force separate S_PACK physical owners. It reconstructs exact content with **1.0×** cold owner decoded work for the small member but exports **+72, +103, +89 and +88 complete stored bytes**, respectively. The control is not an alternative product contract or an official release baseline.

## Interpretation, negatives and architectural boundary

The direct formula is `decoded_owner_bytes / requested_full_file_bytes`; actual Python Reader `_blob` has to decompress a whole shared Zstd frame to recover an arbitrary member, and its cold path caches that full output. The encoder's `min(2 MiB, 8 × largest_member)` bound limits total physical owner size using a **global maximum**, not a particular member's length. Therefore heterogeneous membership allows arbitrarily high **relative** small-member decode amplification within the absolute ≤2MiB owner policy. This is a **scope distinction** in the documented locality promise; it is not an exploit, an exact latency benchmark, or a claim that O34c's tighter cap has no value.

The measured 754 B and 800 B decode owners are individually **tiny**, so a 754× scalar alone does not establish material CPU/RSS/product urgency. More challenging heterogeneous large-owner cases, native C API, cross-platform behavior, decompression CPU, physical read bytes, selective cold I/O, index work, tail metadata, update/recovery, and full release parity remain **UNMEASURED**. Independent physical SHA on the owner was necessary because the inherited Python S_PACK `file_sha256` hashes reconstructed bytes and does not by itself prove the stored physical commitment for this test. No attempt to rewrite the original evaluation or historical thresholds was made.

## Decisive next action and counterfactual

Before proposing a seekable large-shared-context format, ask which promise is actually needed: (A) bounded *global-largest-member* locality, already observed within its envelope, or (B) bounded *every-selected-member* cold reconstruction, which this source does not provide. Validate that difference against the authoritative frozen release gate's actual metric, user-facing API claims, and one **material** mixed-size physical-owner workload, not merely microsecond-friendly 754B examples. If (B) is truly a product requirement, compare admission-aware physical splitting, independent frames with reusable dictionaries and explicit charged seek indexes against the simpler current shipping layout, pricing **complete stored bytes, decode CPU/wall, peak RSS and physical I/O**. No admission threshold adjustment is warranted from this one result.

Counterfactual: source inspection already predicted a likely distinction; the only uncertain fact was whether the authentic shipping Builder actually grouped those members. One cold, source-exact positive 1/753 pair could have answered that fork, while the other three prospective shapes prevent framing a universal claim around one cherry-picked example. This is a narrowly transferable experimental-design lesson, **not** repeated evidence for editing Discovery Engine policy.

**Status:** O40 scientific question **CLOSED/POSITIVE WITH SCOPED SEMANTICS**. Product: unchanged. Format: r24 unchanged. Discovery policy/state: unchanged. Merge: no. Release credit: zero. Source exact-hosted implementation plus row-level evidence: positive; all unmeasured product economics explicitly deferred.
