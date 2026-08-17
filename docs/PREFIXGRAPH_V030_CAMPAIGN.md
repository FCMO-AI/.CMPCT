# CMPCT v0.30 PrefixGraph causal campaign

Status: **research oracle; no version bump; canonical r24 unchanged**.

## Problem

The accepted v0.29 graph is strong at chunk resemblance, but the public shifted-version and boundary-churn
rows still expose source versions whose useful context survives byte insertions better than a fixed aligned
patch. A generic archive also should not need a format-specific parser to exploit that context.

## Hypothesis

A stored direct member can be reused as **raw byte history** for Zstandard while encoding a sibling. The
result is self-contained because the anchor itself is inside the archive. PrefixGraph keeps the first seed
strictly depth 1: every derived member points directly to a stored direct anchor, never to another derived
member.

This mechanism is intentionally orthogonal to Geometry Compiler. Geometry changes the coordinate system of
one byte stream before entropy coding; PrefixGraph changes the entropy coder's available history across
related byte streams. They must prove themselves independently before composition.

## Encoder law

1. Build ordinary Zstd-19 payloads for every file.
2. Nominate a bounded set of possible direct anchors from byte-order only.
3. For each nominated anchor, raw-prefix-compress every other member.
4. Each member keeps raw-prefix only when its actual compressed payload is at least 32 B smaller than its
   ordinary Zstd payload.
5. Serialize the **entire** archive, including authenticated metadata and its recovery copy.
6. Select the smallest complete serialized candidate, not the largest estimated payload saving.

Footnote: for <=32-member families the anchor tournament is exhaustive. Larger families sample at most 32
ordered anchors to bound research work. Approximation may nominate candidates; only exact stored bytes can
admit one.

## Frozen oracle gate

The executable oracle is deliberately narrow and tied to immutable accepted evidence:

- regenerate `01_shifted_versions` and `03_boundary_churn`;
- require both source tree SHA-256 values to match accepted v0.29 history;
- rebuild accepted v0.29 and require its exact archive byte count to match history;
- exact PrefixGraph round trip on both rows;
- complete-artifact fallback makes per-row regression tolerance 0 B;
- require >=24 KiB aggregate saving;
- require >=2 KiB saving on **each** workload;
- require at least one prefix record per workload;
- dependency depth <=1.

The thresholds are below but close to the prior local measurements (~27.7 KiB aggregate) so ordinary
implementation noise cannot be promoted as a win and the weaker boundary row still has to contribute.

## Why raw-prefix rather than a trained dictionary

A trained archive-wide dictionary was already rejected by earlier v0.29 evidence after complete storage
charges. PrefixGraph asks a different question: can the *actual previous version bytes* act as history for a
single sibling? No learned dictionary blob is stored separately; a directly stored file serves both as user
data and reference context.

## Promotion blockers even after a green oracle

- integrate as an authenticated graph edge rather than keep the standalone CMPNXP1 oracle grammar;
- preserve per-member locality <=8x when any future packing is combined with prefix edges;
- compare create/extract CPU and memory against v0.29;
- test malformed base ids, payload spans, dictionary/reference integrity and recovery;
- prove native/shared-reader parity;
- run the full 15-workload release matrix and external format baselines;
- compose with Geometry only after an ablation proves both gains survive together.

A green oracle is therefore evidence to **preserve and integrate**, not permission to publish v0.30.
