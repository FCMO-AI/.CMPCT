# ONE-G0.3 Statistical-Law opportunity diagnostic — preregistration

**Date:** 2026-09-11
**Status:** frozen diagnostic design; no product/candidate promotion authority
**Parent evidence:** `docs/one/evidence/genesis/2026-09-11/GENESIS_ONE_V029_CAUSAL_GAP_ANALYSIS.md`

## Mission Lock / Referee

Genesis partial evidence shows that ONE-G0.2 loses 137,720,376 stored bytes to frozen v0.29 over the exact 15-workload matrix while spending dramatically less creation compute. About 44.5% of that deterministic density gap comes from analytics/database, logs/telemetry, and large-mixed-binary workloads where mature v0.29 gains are not primarily explained by Mosaic-style cross-object relations.

The Architecture Canon already permits statistical symbol prediction and Surprise consumed under an explicit probability model as generic Law. ONE-G0.2's current IR/writer does not exercise that part of the representation theory.

### Falsifiable hypothesis

A **small generic statistical Law**, evaluated only as an information-opportunity diagnostic, should expose material predictable structure in at least two of the three causal-gap workloads (`04_analytics_and_database`, `05_logs_and_telemetry`, `10_large_mixed_binary`) after honestly charging model description bytes.

This is specifically **not** a hypothesis that a legacy entropy codec should be added to the ONE reader.

### Diagnostic model

For every exact frozen Genesis workload, stream all regular-file bytes once and measure:

1. empirical zero-order byte entropy `H0`;
2. empirical first-order conditional byte entropy `H1` using the previous byte as bounded context, resetting context at every file boundary;
3. ideal Surprise bytes `ceil(H/8)`;
4. deliberately conservative reader-visible model charge:
   - H0: dense 256-entry table, 4 bytes per count = **1,024 B**;
   - H1: dense 256×256 transition table plus 256 start-symbol counts, 4 bytes per count = **263,168 B**;
5. modeled complete statistical payload = ideal Surprise bytes + fixed model charge.

The diagnostic does not include the existing ONE manifest/integrity representation, arithmetic/range-coder framing, or final wire syntax. It therefore has **no product size authority**. Its only purpose is to answer whether bounded statistical prediction contains enough information to justify implementation research.

The dense H1 charge intentionally overpays sparse models. A positive result under this charge is stronger evidence than a sparse-table estimate; a negative result cannot rule out more structured predictors.

### Promotion-of-research gate

`ADVANCE_STATISTICAL_LAW_RESEARCH` only if all are true:

- exact frozen 15 workload identities are reproduced;
- measured bytes equal the frozen logical regular-file bytes for every workload;
- at least **2/3** causal-gap workloads show modeled H1 payload at least **15% smaller** than their logical regular-file bytes after the dense model charge;
- at least one of those workloads shows at least **5 MiB** absolute modeled opportunity;
- incompressible controls (`07_incompressible_and_encrypted_like`, resemblance `05_incompressible`) do not falsely show more than **2%** modeled H1 saving after charge;
- observation work is exactly one source-byte pass for counts (no pairwise discovery/search), with bounded O(256²) model state.

Otherwise preserve the result as `HOLD_STATISTICAL_LAW_RESEARCH` and prioritize other causes of the Genesis gap.

### Disproof / hostile controls

The hypothesis is disproved for this model family if the 2/3 + 15% + 5 MiB gate fails, or if incompressible controls falsely appear compressible beyond 2%.

Even a green result does **not** promote a writer, reader opcode, format, or Genesis candidate. The next required step would be a generic bounded predictor + explicit Surprise prototype whose complete authenticated wire, creation CPU/wall/RSS, decode/read cost and selective-read amplification are measured against ordinary Surprise.

## Architectural constraints for any follow-up

- No `OP_ZSTD`, `OP_DEFLATE`, codec registry, or product-specific decoder.
- Predictor semantics must be generic, deterministic and resource-bounded.
- Reader performs predictor evaluation only; it does not discover/train a model from hidden external context.
- Model state/description bytes are part of stored cost.
- Selective reads must have explicit context/crystallization accounting; no invisible prefix decode.
- Creation value is judged by bits eliminated per CPU/wall/memory traffic, not ratio alone.
