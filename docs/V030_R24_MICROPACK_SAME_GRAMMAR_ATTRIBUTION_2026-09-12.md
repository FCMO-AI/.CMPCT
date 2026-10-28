# v0.30 r24 micro-pack same-grammar attribution — 2026-09-12

Status: **Mission Lock / Referee / research-only**.

Parent mechanisms:

- locality-derived grouping law: `sum(group raw bytes) <= 8 * smallest logical member bytes`;
- bounded implicit `membership-v1` control grammar.

## Why this referee exists

The complete candidate changes two things relative to plain independent r24: physical grouping and control representation. Comparing a packed `membership-v1` artifact directly with an independent artifact that still carries the older explicit control grammar can over-credit the packer.

This referee makes the comparator symmetric. For each source it builds:

1. independent r24 with micro-packing disabled;
2. locality-derived r24 with the frozen `<=8x` grouping law;
3. `membership-v1` over the independent artifact;
4. the same `membership-v1` implementation over the locality-derived artifact.

The decisive delta is `(4) - (3)`. No metadata grammar advantage is unique to the packed contender.

## Falsifiable hypothesis

For every tested family where the derived Builder actually emits one or more multi-member groups, the locality-derived physical grouping remains **strictly smaller** after both sides pay the same compact-control grammar, while preserving exact trees, authenticated tail recovery and `<=8x` locality.

A source with zero emitted groups must be byte-identical between the two same-grammar candidates; this is a required fallback control, not a win.

## Sources

Origin controls:

- deterministic Developer repository generator;
- deterministic Many Tiny Files generator.

Held-out hostile controls:

- balanced structured text;
- skewed structured text;
- incompressible bytes carrying text-like suffixes;
- duplicate forest;
- singleton context buckets.

The policy sees only the mature Builder's existing content/hint inputs. Source names remain diagnostic only.

## Required accounting

Per source record:

- plain independent/derived r24 bytes;
- same-grammar independent/derived candidate bytes;
- physical data-span bytes for both;
- complete same-grammar delta;
- emitted group/member counts;
- max/weighted member amplification and max decode unit;
- r24 build CPU/wall;
- membership transform/open CPU/wall;
- strong-tree exactness and authenticated tail recovery for both same-grammar artifacts.

This in-process referee does **not** claim isolated RSS or release throughput.

## Verdicts

`SAME_GRAMMAR_MICROPACK_CAUSAL_WIN`
: every source with emitted groups is strictly smaller under the same grammar, every zero-group source is equal, and all invariants pass.

`MICROPACK_REQUIRES_EXACT_ECONOMIC_ADMISSION`
: invariants pass but at least one emitted-group source ties or loses under the same grammar, or a zero-group source differs. The next Builder must choose the physical representation by exact complete-byte economics and fall back on tie/loss. Do not tune the `8x` law.

`RETIRE_SAME_GRAMMAR_MICROPACK`
: correctness, recovery or locality fails.

## Disallowed responses

- no widening the locality budget;
- no path/extension/workload identity dispatch beyond the already-frozen mature context buckets;
- no hidden comparator grammar mismatch;
- no threshold sweep to rescue a losing family;
- no deletion of negative families;
- no format/release credit from this lane.

If exact economic admission becomes necessary, first build the exact oracle. Only then attempt a cheaper proof/branch-and-bound gate that reproduces the oracle without constructing both full alternatives when a bound is decisive.
