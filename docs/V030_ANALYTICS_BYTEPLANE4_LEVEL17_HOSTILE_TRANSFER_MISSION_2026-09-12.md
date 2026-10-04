# v0.30 BytePlane4 + level-17 generator-distinct hostile transfer mission — 2026-09-12

Status: **research-only Hostile Reviewer / transfer gate** for the positive Analytics `LEVEL17_STRUCTURAL_CROSSOVER` seed. No format, selector, release, comparator, locality, integrity, recovery or ONE/Genesis authority changes.

## Frozen seed

The Analytics seed at hosted run `34731374179` used exactly:

- global Zstd level **17**;
- reversible BytePlane width **4**;
- the prior path-blind level-1 framed audition;
- transformed level-17 work only for cheap-audition winners;
- exact economic fallback to direct level 17 when the transformed frame is not smaller.

It stored 6,134,444 B versus accepted v0.29 6,135,172 B and direct L19 6,135,703 B, while complete verified creation was 55.5% faster than direct L19. The margin to v0.29 is only 728 B, so the mechanism receives no product credit until it survives generator-distinct falsification.

## Falsifiable transfer hypothesis

The BytePlane4 signal represents a real fixed-width structural effect rather than an Analytics-specific accident. With no parameter changes, it should transfer to independently generated interleaved 32-bit structures, while the cheap gate should reject entropy-dense false friends where byte-plane separation has no real benefit.

## Frozen fixtures

All fixtures are deterministic and generated without paths/extensions encoding policy labels. Their names exist only in the benchmark report.

Positive A — `counter32`:
- 2 MiB of little-endian 32-bit counters with a deterministic nonlinear offset;
- fixed 4-byte records create different statistical behavior by byte position.

Positive B — `mixed32`:
- 2 MiB of four-byte records containing a fast-changing byte, a bounded category byte, a slowly changing byte and a deterministic low-entropy flag byte;
- generator is distinct from the neutral-hostile Analytics corpus.

Negative A — `random32`:
- 2 MiB from a fixed-seed pseudorandom generator;
- retains a nominal four-byte record boundary but contains no byte-plane structure worth exploiting.

Negative B — `precompressed`:
- deterministic pseudorandom source compressed into independent zlib streams and concatenated into ordinary files;
- bytes are intentionally entropy-dense even though the outer files have normal filesystem semantics.

## Referee contract

1. Freeze `LEVEL=17`, `WIDTH=4`, the exact existing BytePlane4 frame/inverse and the exact level-1 framed audition. No sweep or threshold change.
2. For each fixture build three modes from the same bytes: direct L17, fixed BP4+L17, direct L19.
3. Use the canonical-filesystem CMPNX5 research wrapper so every mode must reconstruct the exact same logical tree and includes strong verification in creation time.
4. Run two rotated rounds per fixture. Archive bytes, trees and deterministic transform counts must be stable.
5. For both positives require at least one strong transformed selection, candidate bytes < direct L17, and candidate complete verified creation at least 20% faster than direct L19. A positive may be slightly larger than direct L19; this transfer tests mechanism reality, not product promotion.
6. For both entropy-dense negatives require **zero strong transformed selections** and candidate bytes exactly equal direct L17. Any transformed false positive fails the frozen gate.
7. Report direct-L17/L19 bytes and time, candidate bytes/time, transform counts, audition CPU and RSS for every fixture.
8. No workload name/path/extension may enter transform selection. The fixture labels are report-only.
9. Green CI means a valid receipt, not a passing scientific result.

## Decision

- **PASS — `LEVEL17_BP4_GENERATOR_TRANSFER`:** both positives show the frozen structural mechanism and both negatives are rejected with zero strong selections. Preserve the mechanism and proceed to a product-economic integration gate that pays r25 metadata/auth/recovery/native costs and an explicit cheap candidate-admission policy.
- **FAIL — `RETIRE_BP4_L17_GENERALIZATION_CLAIM`:** either positive fails to transfer or either entropy-dense negative is selected. Preserve the Analytics seed as workload evidence only; do not tune width, level, fixture thresholds or workload dispatch to repair the transfer.

`research/cmpct1` and the frozen ONE Genesis result remain unchanged.
