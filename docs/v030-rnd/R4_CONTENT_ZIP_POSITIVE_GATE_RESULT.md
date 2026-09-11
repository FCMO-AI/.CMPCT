# v0.30 R4 per-container positive-byte ZIP gate result

**Status:** MATRIX POSITIVE / PREREGISTERED EQUALITY PARTIALLY FALSIFIED BY A BETTER RESULT / FURTHER HOSTILE ECONOMICS OPEN  
**Exact matrix source:** `636cc718a3838ebcaa2c7ee2bf8a0616103215cc`  
**Hosted run/job:** `34640661646` / `103399265714` — SUCCESS  
**Artifact:** `10279774088`, digest `sha256:7ccb8354373dc1091d1565d2dccd2e9309661964ed48d00e5dd31f6811d43ecd`  
**Shipping/release credit:** none

## Why V2 existed

The first cross-container correlation gate retained almost all Office savings and rejected Analytics, but hostile controls falsified it: a repeated zero-length member manufactured a signal, and a genuine correlated pair admitted an unrelated passenger because the rule was cohort-wide.

V2 was fixed *before* result-bearing execution:

1. ignore zero-length member signatures;
2. sum positive shared member bytes separately for each valid container;
3. admit a hidden container only if **that container** has `shared_positive_bytes > 0`;
4. keep explicit `.zip/.whl` behavior unchanged;
5. preserve exact recipe/tree/range proof.

No workload/path identity or fitted byte threshold is available to the policy.

## 15-workload matrix result

| Metric | unchanged Builder | all-valid hidden ZIP | V2 positive-byte gate |
|---|---:|---:|---:|
| archive bytes | **181,602,602 B** | **172,616,783 B** | **172,231,990 B** |
| saving vs baseline | — | **8,985,819 B** | **9,370,612 B** |
| aggregate creation CPU | **7.7895 s** | **10.2860 s** | **10.4962 s** |
| byte regressions | — | 0/15 | **0/15** |
| exact reconstructed trees | — | 15/15 | **15/15** |

V2 retains 104.28% of the all-valid saving. That is not a typo: it is smaller than the all-valid policy because it refuses one valid but economically harmful Office container.

### Office

- baseline: `15,445,458 B`;
- all-valid: `6,460,536 B`;
- V2: **`6,074,846 B`**;
- V2 saving versus baseline: **9,370,612 B / 60.67%**;
- five hidden containers admitted;
- exact sampled VZIP ranges and full reconstruction pass.

Per-container observed positive shared bytes:

- `board_deck.pptx`: `3,704,055 B`;
- `operating_review_v1.docx`: `2,242,385 B`;
- `operating_review_v2.docx`: `2,177,541 B`;
- `operating_review_v3.docx`: `2,139,246 B`;
- `operating_review_v4.docx`: `2,295,659 B`;
- `finance_model.xlsx`: **0 B**.

`finance_model.xlsx` was therefore left on the ordinary path. Doing so makes the complete archive **385,690 B smaller** than the all-valid six-container policy.

This falsifies the preregistered assertion `office_retains_all_valid_bytes` (`V2 == all-valid`) while strengthening the actual mechanism-level result. The assertion remains recorded as false; it is not rewritten after observing the data.

### Analytics

- baseline: `10,392,496 B`;
- all-valid: `10,391,599 B`;
- V2: **`10,392,496 B`**;
- `features_compressed.npz`: `shared_positive_bytes = 0`;
- hidden recipe avoided completely.

Thus V2 preserves the intended economic rejection of the prior ~0.9 KiB low-yield win.

## Hostile controls carried inside V2

Both causal repairs survive their original attacks:

### Empty-member signal

Two unrelated hidden ZIPs shared only an empty member.

- both report `shared_positive_bytes = 0`;
- hidden admissions: 0;
- hostile passes.

### Correlated pair + unrelated passenger

- pair A: `57,344 B` shared positive evidence;
- pair B: `57,344 B`;
- unrelated passenger: `0 B`;
- only A/B become VZIP;
- passenger remains ordinary;
- hostile passes.

## Interpretation

The useful predictor is now more specific:

> exact positive member reuse owned by the *candidate container itself* is a strong indicator for the existing virtual-container representation.

The Office `finance_model.xlsx` outcome is especially valuable because it shows recognition and admission are not the same thing. A file can be a perfectly valid ZIP and still be better stored as an ordinary file. Content correlation is therefore doing actual economic selection rather than merely identifying file types under misleading extensions.

However, `shared_positive_bytes > 0` is still deliberately underfit. It may admit two very large containers that share only one byte. A dedicated tiny-positive hostile receipt is therefore required before any product integration.

## Performance caveat

The research V2 still executes a separate observation walk and then calls the duplicated research `ContentZipBuilder.scan()`. Its aggregate CPU is therefore not representative of a fused product implementation. The matrix proves mechanism and admission behavior, not release-performance readiness.

The correct integration direction—if further hostile tests survive—is a single canonical scan that caches magic/preflight/central-directory observations and consumes them during recipe admission. A second filesystem walk would violate the campaign's marginal-information-yield goal, particularly on tiny-file roots.

## Decision

**Advance V2 as the current economic-admission seed, but do not promote it.**

Open gates before shipping credit:

1. tiny-positive shared-byte economics;
2. bounded EOCD/central-directory preflight before optional stdlib ZIP parsing;
3. fused single-pass observation rather than research pre-scan;
4. repeated fresh-process creation CPU/wall/RSS;
5. S_PACK selective amplification/failure-blast accounting when discovered cohorts cross the existing >=8 threshold;
6. full v0.30 portfolio integration and exact 15-workload product comparison, not r24-Builder projection.
