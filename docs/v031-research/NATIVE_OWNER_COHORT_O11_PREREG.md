# Native owner-cohort extraction O11 — prospective experiment

Date: 2026-10-24 UTC
Status: FROZEN PREDICTION, BEFORE IMPLEMENTATION
Scope: test-only C research client, *not* a shipping extractor or native ABI amendment.

## Source authority and concurrency
Canonical development branch at orientation: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Exact independently owned parent PR #335 at `501a063ee665950b4363f532c0a044f4ef3ee4eb`, carrying PR #327 O7 grouped/eager controls. This experiment adds distinct O11-only files; it does not edit their C, Python, native ABI, Writer, Builder, policies or shared discovery state. PR #335 itself expressly defers bounded-per-owner staging as a separate candidate. Other neighboring CI/product/namespace owners remain separate.

## Primary scientific question
Can a single *physical-owner-at-a-time* authenticated batch reconstruct PACK members with most of O7's grouped throughput while maintaining an aggregate caller-memory ceiling independent of the number of archive files and a streaming fallback for RAW/oversized groups?

## Real baseline, discriminators, alternatives
O7 showed ~9.52x whole-test-consumer improvement on 512 tiny files by batching, but kept every file buffer until all output was written. O10b bounded eager memory by 64 KiB streaming and showed 36,020 -> 2,754 KiB VmHWM on RAW 32 MiB, but repeated Zstd PACK decoding. Simpler controls are both original O7 serial/group and O10 stream clients, compiled unchanged at *exact same new HEAD*. Proposed O11 uses current `cmpct_entry_pack_owner` and `cmpct_pack_read_batch`, only one owner group resident at once, and 64KiB range streaming for every unsupported or oversized group. No long-lived cache, no new reader parser or format.

## Prediction before results
For 512 structured text files, the candidate should observe >=2 actual eligible Zstd physical owner groups and >=512 batched files, yield correct full content hashes on each output, be materially faster than O10's per-file streaming and remain within a credible range of O7's eager group latency. For 32MiB RAW-friendly files, batching should not be attempted; streaming RSS should stay close to O10's measured 2.7 MiB (host variance acknowledged), far below O7 eager serial; neither new archive bytes nor decoded bytes may be changed. Held-out 2048-member structured corpus tests multiple owners: processing one owner at a time should avoid aggregate retention growing linearly with all extracted logical content, though metadata allocations and native buffers must be charged. No presumptive ratio or product credit until hosted measurement.

## Falsifiers / kill conditions
Any wrong output SHA, silent omission, unsafe leaf or external-canary mutation, incorrect group ownership, different original-source archive, physical bytes mutated by the client, unbounded cumulative allocation, failure to fall back safely when unsupported, or substantially worse RSS plus no meaningful Zstd speed benefit disproves the proposed combination. A measurement missing the intended PACK execution cannot support the batching hypothesis. Single-call and RAW controls are allowed to win. The batch cap (1024 requests, <=16MiB output, <=16MiB physical owner) is inherited and never weakened; if cohort exceeds it, retry with bounded independent reads rather than altering ABI/evaluator.

## Evidence and cost law
Independent Python original-source SHA-256 oracle, same exact archive, fresh output directory per invocation, 3 alternating ABBA blocks per cohort/arm with raw repeats; process-inclusive wall and child CPU; *process-local* VmHWM instead of inherited getrusage highwater. Charge batch staging memory, native decode, per-entry metadata, output writes, size, and partial-publication risk. Do not call VmHWM equal across modes without adequate signal a proof of allocation neutrality. Host-only Linux and root-level filenames are deliberate research scope. No symlink/hardlink/tree atomicity, mutable-source RAW integrity, crash/power-loss/portability or released-product claims. Keep exact-head CI and artifact custody.

## Decision unlocked
If the two mechanisms coexist materially, next work is a *platform-safe owned* extractor with aggregate memory budget, checksum publication and namespace controls. If grouped latency collapses or RSS carries disproportionate decode cost, retain existing APIs as separate options rather than forcing one policy. No change to discovery policy absent repeated causal evidence.
