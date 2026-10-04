# Logs authenticated-pack materialization component attribution — preregistration

Status: **FROZEN FORGE D2 FOLLOW-UP / NO RELEASE CREDIT**

## Predecessor fact

`R25_LOGS_RESTORE_INNER_ATTRIBUTION_RESULT.md` established two material owners inside the promoted Logs authenticated restore boundary on `neutral_hostile_v1/05_logs_and_telemetry`: authenticated pack materialization at **14.730192 ms / 31.7265%** of total extraction and inverse decode at **13.365921 ms / 28.7881%**. The pack boundary is the slightly larger owner and is therefore the next lowest-radicality Forge target.

This follow-up asks which work *inside the existing authenticated `_read_pack` operation* owns the actionable millisecond-scale cost. It is attribution only: every byte read, decompression operation, CRC32 check and SHA-256 authentication remains mandatory and is still executed.

## Frozen target and semantic owner

- target: deterministic `neutral_hostile_v1/05_logs_and_telemetry`;
- exact promoted fused extractor and selected `logs-inverse` archive bytes;
- semantic owner: `experiments.entropygraph_v030_logs_inverse_profile.Archive._read_pack` as inherited through v2/v3 and the fused extractor;
- exact source tree required after every extraction;
- no production source, archive bytes, pack framing, codec, locality, integrity, recovery or release threshold changes.

## Frozen tracked components

The instrumented arm replaces `_read_pack` only for timing, reproducing its inherited logic exactly and retaining all checks. It measures these existing sub-boundaries separately:

1. **seek/read** — file seek plus exact compressed/raw payload read;
2. **Zstd materialization** — `ZstdDecompressor` construction plus decompression for compressed packs only;
3. **CRC32 authentication** — CRC32 over the complete raw pack;
4. **SHA-256 authentication** — SHA-256 over the complete raw pack;
5. **explicit remainder** — total instrumented `_read_pack` wall minus the four tracked components. This remainder is real and includes Python dispatch, tuple unpacking, bounds/length checks and timer overhead; it is never gifted away.

The instrument also records stable raw-versus-Zstd pack call counts so a cost is not misattributed to a codec path that did not execute.

## Frozen execution

- one untimed warm-up per arm;
- **11 paired rounds**, alternating control-first / instrumented-first;
- control is the exact uninstrumented promoted fused extraction;
- `gc.collect()` before each timed extraction;
- same archive bytes/SHA/selected representation in all rounds;
- exact canonical user tree after every extraction;
- complete promoted strong verification before timing;
- stable pack call counts and codec call counts required.

Instrumentation is valid only when instrumented median total extraction / control median total extraction is `<=1.10x`.

## Frozen material-headroom rule

A tracked component is material only if its median is both:

- `>=0.0020 s` absolute; and
- `>=5%` of instrumented total extraction wall.

This keeps the same millisecond-scale Forge floor as the two predecessor attribution experiments. A component crossing the floor authorizes only a narrow implementation A/B that still performs all authentication and reconstruction work.

Terminal decisions:

- invalid exactness/selection/instrumentation/call-count evidence -> **`INVALID_PACK_COMPONENT_ATTRIBUTION`**;
- seek/read material -> include **`PACK_IO_HEADROOM`**;
- Zstd materialization material -> include **`PACK_ZSTD_HEADROOM`**;
- CRC32 material -> include **`PACK_CRC32_HEADROOM`**;
- SHA-256 material -> include **`PACK_SHA256_HEADROOM`**;
- no tracked component material -> **`TRACKED_PACK_COMPONENTS_INSUFFICIENT`**.

If multiple components are material, preserve all of them and prioritize the largest median for the next lowest-radicality Forge intervention. Do not collapse several components into one optimization merely because their summed time is large.

## Safety and release law

This experiment does **not** skip CRC32, SHA-256, decompression, pack bounds, short-read rejection, logical-member SHA-256, recovery, locality charging or transactional publication. No hash is replaced by a weaker primitive and no verification result is cached across operation boundaries. It grants **zero release credit**. Any later product intervention must preserve exact archive bytes/tree, hostile-corruption rejection, declared recovery guarantees and all frozen release/runtime thresholds.
