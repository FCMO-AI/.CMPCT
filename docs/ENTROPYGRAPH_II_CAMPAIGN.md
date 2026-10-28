# EntropyGraph II — Resemblance Compiler campaign

Status: **active research campaign / canonical format revision 24 unchanged until promotion gates pass**.

This document is the executable engineering plan and evidence map for the campaign that follows the
v0.25 EntropyGraph frontier. It is deliberately repository-local: a future contributor should be able
to understand, reproduce, falsify and continue the work without private chat or private corpora.

## 1. Observed opportunity and inherited baseline

The inherited v0.25 research engine already removed several categories of exact redundancy through:

- global exact compressed-stream federation;
- exact object interning;
- exact inverse edges for loose/compressed copies;
- virtual ZIP reconstruction;
- bounded family-solid packing;
- authenticated physical packs and logical tree root;
- operational redundant metadata recovery.

Its public neutral/hostile record is `benchmarks/history/2026-08-16-entropygraph-v025.json`. The fixed
10-workload suite stored 90,383,940 bytes and retained losses against solid tar+Zstd-19 on developer,
media, ML and large-binary cases plus a selective-read loss on one analytics array.

The remaining structural defect is that **near-equal information is still mostly treated as distinct
information**. CDC can recover exact chunks after shifted edits, but it cannot exploit two bounded
objects whose bytes are substantially similar without containing an exact equal chunk. In parallel,
DEFLATE-bearing containers hide potentially reusable plaintext behind entropy-dense streams, and a
universal 512 KiB packing ceiling treats ratio/locality as a constant instead of a measured budget.

## 2. Invariants

The campaign may improve ratio only while preserving all of these properties:

1. reconstruction is byte-exact;
2. similarity is candidate discovery, never correctness evidence;
3. an accepted delta must be smaller after its own compression and metadata cost;
4. delta dependency depth is at most one;
5. candidate fan-out and source indexing are bounded against adversarial populations;
6. physical decode units have a declared hard ceiling;
7. wider solid context must carry explicit read-amplification accounting;
8. physical payloads are independently authenticated and participate in a Merkle root;
9. redundant metadata must be an operational recovery path rather than decorative bytes;
10. the inherited v0.25 artifact remains an exact per-workload fallback, so the research portfolio may
    never grow an archive merely to exercise the new mechanism;
11. creation CPU, verification time, unavailable competitors and losing workloads remain visible;
12. CMPNX8 research bytes do not become canonical revision-24 claims by documentation alone.

## 3. Falsifiable hypotheses

### H1 — bounded resemblance deltas remove redundancy left by exact CDC

If FastCDC-stable objects are sketched with multiple local super-features, a bounded LSH search should
find useful near-neighbors in versioned/related data without an O(N²) search. A rolling rsync-style
delta should then recover long copies after insertions/deletions.

**Disproof:** on deterministic shifted-version and boundary-churn workloads, the measured delta graph
fails to reduce final archive bytes or candidate discovery becomes unbounded.

### H2 — measured similarity ordering can buy context without unbounded random-read debt

Ordering physical roots by content sketches before packing should expose residual local context. An
adaptive pack audition over 64 KiB–2 MiB should beat a universal fixed ceiling on at least one workload
while respecting a hard weighted read-amplification budget.

**Disproof:** wider packs do not create a material byte win after framing or exceed the locality budget;
in that case the encoder must retain the 512 KiB plan.

### H3 — reversible DEFLATE precompression converts hidden redundancy into ordinary information

A pinned, memory-safe preflate-class bridge can represent supported DEFLATE-bearing files exactly while
allowing their internal plaintext/correction representation to compete with direct storage.

**Disproof:** the exact reconstructed artifact differs by one byte, the bridge cannot be resource-bounded,
or its stored representation does not beat the direct candidate after all metadata.

### H4 — explicit graph selection is stronger than threshold folklore

Once direct, packed, delta, precompressed and inherited representations have measured byte costs, the
encoder can select physical roots under explicit locality/dependency budgets rather than assuming one
representation should always win.

**Disproof:** the graph candidate loses every reproducible workload after full artifact overhead; the
portfolio must then retain inherited v0.25 and record the negative result rather than force promotion.

## 4. Competing solution classes considered

### Replace Zstd with a custom entropy codec now

Deferred. A vectorized rANS/context-mixing codec is a legitimate research track, but entropy coding is
not the dominant missing mechanism exposed by the current corpus. Reimplementing match finding,
parsing, models and SIMD before exhausting structural reuse would create a large decoder burden with no
proved Pareto gain.

### Whole-file MinHash + whole-file binary delta

Rejected as the primary design. It is cheap, but large files create unbounded base memory and a local
insertion can make whole-file similarity less stable. EntropyGraph II therefore uses bounded CDC nodes,
local super-features and a hard delta-base limit.

### Unlimited delta chains

Rejected. They can improve ratio but export hidden random-read, recovery and corruption fan-out costs.
Bases are promoted by aggregate saving centrality and may not themselves be delta targets.

### Always use larger solid packs

Rejected. Pack size is an auditioned decision with an explicit decoded-bytes/logical-bytes
amplification metric. Wider context must produce a material byte reduction and remain within the budget.

### Trust similarity score as a compression decision

Rejected. Sketch collisions are expected. Every candidate edge is encoded and measured; only the final
stored delta cost can admit the edge.

## 5. Implementation phases and acceptance gates

### Phase A — reusable bounded resemblance primitives

Implemented in `src/cmpct/resemblance.py`:

- deterministic Gear/FastCDC-style bounded chunking;
- multi-band local super-feature sketches;
- bounded LSH candidate generation;
- rolling rsync-style COPY/LITERAL deltas;
- bounded delta decoder;
- depth-1 centrality-based base selection;
- deterministic similarity ordering.

`tests/test_resemblance.py` attacks deterministic boundaries, insertion recovery, malformed copy
references, false-neighbor fan-out and dependency-chain formation.

### Phase B — EntropyGraph II research grammar

Implemented in `experiments/entropygraph_v028.py` as **CMPNX8 research bytes**, not canonical grammar:

- exact chunk interning before resemblance work;
- measured delta edges and central-base promotion;
- similarity-ordered adaptive packing from 64 KiB through 2 MiB;
- explicit pack read-amplification budget;
- 8 MiB declared decoder-unit ceiling in header/metadata;
- O(1) file and physical-record lookup metadata;
- Merkle root over physical payload leaves;
- SHA-256/CRC logical/physical checks;
- redundant primary/tail metadata;
- per-workload inherited-CMPNX5 fallback based on actual artifact size.

Before this phase can be considered complete, deliberate corruption must prove that primary metadata
failure recovers through the authenticated tail and physical leaf corruption fails locally.

### Phase C — exact DEFLATE inversion bridge

Implemented under `native/preflate-bridge/` using a pinned upstream `microsoft/preflate-rs` commit. The
bridge forbids unsafe Rust and immediately recreates every produced preflate payload through the
opposite path, byte-comparing the result in bounded buffers before the payload is eligible for CMPCT.

The bridge remains an **optional research accelerator/transform**. Revision 24 does not depend on it.
A canonical promotion would need an independently specified transform/version contract and native
reader integration rather than a shell-out dependency.

### Phase D — hostile and competitor evidence

`benchmarks/resemblance_hostile_corpus_v1.py` adds five deterministic attack workloads:

1. shifted near-duplicate snapshots;
2. false sketch neighbors with mostly random bodies;
3. repeated one-byte boundary churn;
4. related DEFLATE ZIP families;
5. incompressible/random objects.

`benchmarks/entropygraph_v028_bench.py` runs the inherited and new engines on identical trees. It also
attempts ZIP/Deflate-9, solid tar+Zstd-19, 7z/LZMA2, ZPAQ method 5 and DwarFS when available, recording
missing tools and semantic differences instead of dropping them.

`.github/workflows/entropygraph-v028.yml` builds the pinned bridge, runs full tests, executes the public
neutral + resemblance-hostile benchmark and uploads the raw JSON/stdout evidence.

### Phase E — promotion decision

A numeric core release is permitted only if the committed evidence demonstrates a material CMPCT
advance under repository rules. Research success alone does **not** change revision 24.

If the research portfolio materially improves reproducible bytes without a hidden regression:

1. commit the accepted raw research record under `benchmarks/history/`;
2. advance the project line to v0.28.0 under the scarce-version policy;
3. add `docs/releases/v0.28.0.md` and update current-state/history/research/benchmark documentation;
4. run the canonical direct-base release gate against v0.27.1 on its one immutable parity tree;
5. commit that accepted canonical candidate record as well;
6. update the website only from committed benchmark evidence;
7. merge only after ordinary tests, public-surface, version-discipline, engineering-evidence and
   performance gates are green.

Canonical reader-visible promotion of CMPNX8 remains a separate future revision and requires the full
research-to-production checklist in `docs/AGI_ENGINEERING_STANDARD.md`: precise bytes, independent
vectors, hostile parser/resource tests, recovery semantics, native parity, portability and export
implications.

## 6. Explicitly separated 1.0 work

The broader format still needs deterministic parallel creation, non-seekable/resumable streaming,
remote HTTP/object-store range sources, AEAD/KDF design, complete ACL/Windows/macOS metadata rules,
coverage-guided fuzzing, optional payload parity/recovery coding, frozen specification, independent
implementation completeness, media-type registration and final license adoption.

Those items are not silently claimed by EntropyGraph II. Some combine naturally with this campaign
(Merkle-authenticated range reads in particular), but pretending a compression-research milestone has
completed governance or ecosystem work would violate the project's evidence hierarchy.

## 7. Completion dossier checklist

Before merge, the PR/repository evidence must answer:

- exact direct-base and candidate bytes for every workload;
- which workloads selected resemblance vs inherited fallback;
- accepted/rejected delta counts and estimated bytes removed;
- preflate attempts/wins and exact reconstruction status;
- selected adaptive pack ceilings and read-amplification values;
- create and strong-verify cost, including the portfolio audition tax;
- hostile false-neighbor behavior and candidate-work bounds;
- primary-metadata recovery and physical-leaf corruption refusal;
- competitor availability/settings/semantic differences;
- canonical r24 performance-gate outcome;
- public-surface scan outcome;
- all remaining losses and unresolved promotion blockers.

The campaign is complete only when those claims are backed by durable files or CI evidence, not by a
chat summary.
