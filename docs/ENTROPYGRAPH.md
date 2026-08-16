# CMPCT EntropyGraph — v0.28 research frontier

Date: 2026-08-16

Project milestone: **v0.28.0**  
Canonical executable/on-disk format: **revision 24 (unchanged)**  
Research grammar: **CMPNX8 when EntropyGraph II wins; exact inherited CMPNX5 fallback otherwise**

## Result

EntropyGraph II changes the remaining problem from exact duplicate elimination to **bounded resemblance
reuse**. The research encoder now finds near-equal bounded objects, measures concrete reversible deltas,
auditions physical context under an explicit read-amplification budget, and retains the inherited v0.25
artifact whenever the new representation is not actually smaller.

Across the fixed public neutral + resemblance-hostile suites the inherited v0.25 research engine stores
**166,816,028 bytes**. The v0.28 portfolio stores **137,557,457 bytes**, a **17.5394% reduction**, with
**3 workloads improved and 0 regressed**. The other **12/15 workloads are exact inherited fallbacks**;
no average score is allowed to hide a losing representation.

The three mechanism-level wins are:

- shifted near-duplicate versions: **30,200,827 → 1,761,588 bytes (-94.17%)**;
- repeated one-byte boundary churn: **866,651 → 89,945 bytes (-89.62%)**;
- ML artifacts: **13,879,065 → 13,836,439 bytes (-0.31%)**.

The accepted public evidence is `benchmarks/history/2026-08-16-entropygraph-v028.json`. It retains all
15 workload rows, source-tree fingerprints, inherited/candidate/raw-graph sizes, representation
selection, creation and strong-verification costs, graph/locality statistics, structural competitor
aggregates, unavailable tools, and the SHA-256 of the complete raw CI evidence artifact.

## Why v0.28 exists

v0.25 proved that an archive can be treated as an authenticated reconstruction graph: exact streams,
objects and inverse views can share physical roots rather than remaining isolated by filename/container.
Its dominant remaining defect was that **near-equal information was still mostly distinct information**.
Exact CDC helps when identical chunks survive edits, but does not exploit two bounded objects that are
strongly similar without sharing a sufficiently large exact chunk.

EntropyGraph II therefore adds a resemblance layer without making similarity part of correctness.
Similarity only nominates candidates. Final admission always depends on encoding the concrete reversible
representation and measuring its complete stored cost.

## EntropyGraph II mechanisms

### 1. Bounded FastCDC-style units

Large logical files are divided into deterministic bounded units so insertions/deletions can rediscover
nearby boundaries. The reader never needs the chunking heuristic: logical lengths and references are
recorded explicitly.

### 2. Bounded similarity discovery

Each unit receives multiple local super-features. A bounded LSH search nominates only a small number of
near-neighbors per target; hostile false-neighbor populations cannot trigger an unbounded all-pairs
search.

### 3. Measured COPY/LITERAL deltas

Candidate base/target pairs are encoded with a rolling rsync-style COPY/LITERAL transform. A delta edge
is accepted only when its compressed payload **plus record/metadata overhead** is materially smaller than
the target's direct representation and copies a meaningful fraction of the target.

Similarity score is never correctness evidence.

### 4. Dependency depth = 1

Bases are selected by aggregate saving centrality and may not themselves be delta targets. This prevents
ratio wins from becoming hidden recursive read/recovery chains. A target either decodes directly or from
one independently decodable base plus one delta.

### 5. Adaptive physical context

Root objects are similarity-ordered and the encoder auditions pack ceilings from **64 KiB through 2
MiB**. Wider context is accepted only when it wins bytes and the weighted selective-read amplification
remains within **8x**. If a wider plan does not materially earn its cost, the encoder retains the 512 KiB
baseline.

Footnote: “2 MiB pack allowed” is not “2 MiB pack always used.” The pack width is a measured physical
choice with an explicit locality budget, not a new universal constant.

### 6. Exact DEFLATE precompression

A pinned memory-safe bridge around `microsoft/preflate-rs` can invert supported DEFLATE-bearing files
into an exactly reconstructible preflate representation. Every produced transform is immediately
recreated through the inverse path and byte-compared before it can compete for storage.

The bridge is an optional research transform. Canonical revision 24 does not depend on it.

### 7. Merkle-authenticated physical records

Physical payload hashes participate in a Merkle root while logical nodes/files retain exact SHA-256/CRC
checks. This allows local corruption refusal without turning every ordinary read into a whole-archive
verification pass.

### 8. Recovery that is operational

Primary metadata and an authenticated tail copy are both real recovery paths. Deliberate primary
metadata damage must recover from the tail; physical payload corruption must still fail closed rather
than being confused with metadata recovery.

### 9. Portfolio selection

EntropyGraph II builds both the inherited v0.25 candidate and the new graph candidate for a workload.
The smaller exact artifact wins. When resemblance loses, the inherited artifact is copied unchanged.

This makes “0 workload size regressions” a property of the representation tournament rather than an
aggregate reporting trick. The tradeoff is extra encoder CPU, which remains recorded.

## Fixed public workload contract

The research frontier now combines the original 10 deterministic neutral/hostile workloads with five
resemblance-hostile attacks:

1. developer repository;
2. office workspace;
3. media library;
4. analytics/database;
5. logs/telemetry;
6. incremental backups;
7. incompressible/encrypted-like data;
8. many tiny files;
9. ML artifacts;
10. large mixed binary;
11. shifted near-duplicate versions;
12. false sketch neighbors with mostly random bodies;
13. repeated one-byte boundary churn;
14. related DEFLATE container family;
15. incompressible resemblance-control objects.

Every workload remains visible. Promotion cannot delete an inconvenient row or weaken the selective-read
contract to make an aggregate prettier.

## Structural competitor context

The v0.28 structural sweep archives each public suite as a complete recursive tree with ZIP/Deflate-9,
solid tar+Zstd-19, 7z/LZMA2, ZPAQ method 5, Borg and DwarFS when available.

On the resemblance-hostile aggregate:

- CMPCT EntropyGraph II: **47,197,165 B**;
- tar+Zstd-19 solid: **47,065,652 B**;
- ZPAQ method 5: **47,062,641 B**;
- 7z/LZMA2: **47,430,344 B**;
- Borg: **76,460,621 B**;
- ZIP/Deflate-9: **76,690,799 B**.

DwarFS was unavailable in the evidence runner and remains recorded as unavailable rather than omitted.
These are **structural size comparisons, not semantic-parity claims**. A monolithic solid compressor and
a bounded dependency/recovery graph export different random-access and failure costs.

## Reliability and resource contract

The v0.28 campaign additionally exercises:

- exact reconstruction and strong verification;
- dependency depth <= 1;
- declared physical decode-unit ceiling of **8 MiB**;
- separate decoder working-memory ceiling;
- <=8x weighted read amplification for admitted pack plans;
- bounded candidate fan-out and delta output;
- malformed-delta and malformed-graph fuzzing;
- authenticated tail recovery;
- local physical-leaf corruption refusal;
- strict HTTP/range sources that cannot silently fetch the whole archive;
- byte-identical one-worker vs multi-worker reproducible canonical creation.

## Canonical performance lesson from the campaign

The first reconciled v0.28 release-gate run exposed one fresh-process regression: media CLI creation
measured **192.99 → 203.07 ms (+5.22%, +10.08 ms)** even though the underlying library create path moved
by less than 1 ms. The cause class was exported thread-pool startup on a small CLI workload.

The release candidate therefore keeps the in-process `Builder` parallel default, but a fresh
`cmpct create` process remains serial unless the caller explicitly supplies `--workers N`. This protects
small-command latency while preserving deterministic parallel creation for batch/large workloads. The
fix is subject to a fresh direct-base ABBA gate; the failed result remains evidence rather than being
explained away or hidden.

## What remains research-only

CMPNX8 is **not** a reader-visible revision-24 extension. Existing r24 readers must never be handed
CMPNX8 bytes under an r24 magic/version claim.

Canonical promotion must happen representation-by-representation and requires:

- precise byte-level grammar;
- independent golden vectors;
- hostile parser/resource tests;
- recovery semantics;
- native-core parity;
- explicit ZIP export/compatibility behavior;
- platform/browser implications;
- a deliberate on-disk revision bump when readers actually need new semantics.

## Historical v0.25 milestone retained

The original v0.25 public neutral/hostile record remains
`benchmarks/history/2026-08-16-entropygraph-v025.json`. On its 10-workload suite CMPNX5 stored
**90,383,940 bytes**, **16.46% smaller than ZIP/Zstd-93**, **18.88% smaller than ZIP/Deflate-9**, and
**6.91% smaller than the solid tar+Zstd-19 diagnostic** in aggregate. It won 8/10 workloads against
ZIP/Zstd-93 and 6/10 against solid tar+Zstd-19 while preserving its losses.

Those results remain important because v0.28 builds on—not retroactively rewrites—the v0.25 information
model: exact compressed-stream federation, directional inverse views, exact object interning, compact
micro-pack indexing, bounded context, hot/cold roots, authenticated metadata, and operational recovery.

## Next frontier

The strongest next step is **not deeper delta chains**. It is to productionize proven graph mechanisms
one reader-visible representation at a time, while reducing portfolio audition cost without replacing
final byte measurement for admitted candidates.

After structural reuse is exhausted, a separate entropy-coding research track can evaluate rANS/context
models or other native codecs against the same locality, decoder-complexity and hostile-resource budget.
A codec that wins a synthetic ratio while exporting unbounded memory, fragile recovery or a giant reader
is not a CMPCT improvement.

## Publication boundary

Only deterministic public corpora, generalized engineering conclusions, public benchmark artifacts and
reproducible mechanisms belong in the repository. Private development corpora may remain local regression
signals, but private names, paths, hashes, artifact filenames, contents or organization-specific
provenance must never enter release notes, benchmark history, the public site or source comments.
