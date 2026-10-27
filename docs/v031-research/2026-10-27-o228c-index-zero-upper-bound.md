# O228c counterfactual: a zero-byte-index upper bound before integration

**Independent source:** original O228b authentic Builder court (not the subsequent native-mode O228c), [hosted Actions #40525914266](https://github.com/FCMO-AI/.CMPCT/actions/runs/40525914266), [artifact #12744401663](https://github.com/FCMO-AI/.CMPCT/actions/runs/40525914266/artifacts/12744401663), source `76c37b56edb9bbbd6cfbef003ce5b48443aa32b6`, original ZIP SHA-256 `1e856ff354a8353552325a94f5a55746b8c2b0e5491b909bbd4bac30bbe2a120`. I inspected `o228b_raw.json` from that existing artifact and independently recomputed the following exact *upper bound*, without changing the original preregistration, measurements or decision.

## Bound

O228 changes only the complete logical index; physical records, header/footer framing and the 16-MiB logical input remain fixed. The r24 archive includes a primary and tail copy of the Zstd-compressed index. Even a gifted oracle that makes *both compressed indexes zero bytes* cannot save more than `2 * index_bytes` from `archive_bytes`. Thus the maximal whole-archive size reduction is exactly bounded by:

```text
max_savings_bytes <= 2 * original_index_compressed_bytes
max_savings_percent <= 100 * 2 * original_index_compressed_bytes / complete_original_archive_bytes
```

This is deliberately **unachievable** (a real index needs nonzero bytes); it is a favorable impossibility oracle, not a new representation or product claim. Any representation requiring new decoder facts, tags, checksums or framing must do worse, absent a separately measured physical-payload transformation.

| Genuine 16-MiB O228b corpus | Complete archive (B) | Two original compressed indexes (B) | Maximum hypothetical whole-archive saving |
|---|---:|---:|---:|
| All-zero | 1,015 | 788 | 77.635468% |
| One-period high entropy | 1,049,818 | 850 | **0.080966%** |
| Two-period high entropy | 2,098,714 | 914 | **0.043551%** |
| Shifted/randomized | 16,782,978 | 1,530 | **0.009116%** |
| Structured records | 3,506 | 970 | 27.666857% |
| Independent random | 16,782,972 | 1,524 | **0.009081%** |

The three nontrivial large-physical-payload families **cannot** provide the O228b/O228c preregistered >=1% whole-archive saving from index replacement alone, even under an impossible zero-index oracle. All-zero/structured remain mathematically eligible, but O228b measured only -14 B and +6 B respectively and its positive all-zero case does not satisfy the two-nontrivial-family test.

## Transfer, self-critique and policy

The previous native-versus-fallback confound remains real: O228b used fixed 256-KiB fallback boundaries, whereas a loaded canonical CDC helper can alter run ownership and index sizes. Consequently this **numeric bound applies only to the recorded O228b Builder archive sizes**, not every future native CDC archive. Recompute it from original native-mode records before making a native claim; O228c provides that independent test. Do **not** retroactively replace its preregistered criterion with this cheaper observation.

**Counterfactual prospective discriminator:** before experimenting with a new index grammar, inspect `2 * compressed_index_bytes / whole_archive_bytes` for several real archetypes. If the required whole-archive size win already exceeds that favorable bound, the family cannot win through index-only representation regardless of how good its decoder heap microbenchmark looks. This source-visible, cheap and transferrable observation could have narrowed O228/O228b product expectations earlier. It does **not** imply a policy mutation from one finding. The Reader's validated admission/memory economics, recovery, and compatibility remain separate product gates.

**Status:** derivation/independent recomputation on immutable hosted evidence; no source-code or published-format change; no release credit.