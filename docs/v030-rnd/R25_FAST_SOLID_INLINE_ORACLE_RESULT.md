# R25 compact inline-solid oracle result

Status: **CONDITIONAL RESEARCH HEADROOM — LOCALITY / CANONICAL-COST DEBT UNPAID**

Date: 2026-09-03

## Authority and claim boundary

This record preserves the result-bearing `CMPCT v0.30 inline solid candidate oracle` execution from GitHub Actions run `33781561487`, substantive job `100736395840`.

The PR workflow checked out merge SHA `49ca94f496a6fbca8f07b05f3ffa47f68d590226`, the merge of authoritative PR #56 head `5c7459ca52ce212021fbf5c860a32708fad00459` into base `dd0c12cd6ee2dbb859464ea5c6be221ad34b9fdf`.

Evidence artifact ID: `9904072629`.

Artifact ZIP SHA-256: `cd7ba58c1d2a0e43b5a96e0886a18868823b5b311d2e1b28168dfb5d3806eb12`.

Schema: `cmpct-v030-fast-solid-inline-oracle-v3`.

This is research-only evidence. The candidate bytes are **not canonical r25**, carry no release credit, and have not yet paid canonical framing, <=8x selective-read locality, strong/member integrity, recovery, native/platform, or Android costs.

## Question and frozen decision rule

The oracle tested whether compact metadata interleaved with raw file payloads before one Zstd stream could produce a representation that is simultaneously:

1. strictly smaller than ordinary ZIP/Deflate-9;
2. strictly smaller than solid tar+Zstd-19;
3. strictly faster to create than ZIP; and
4. strictly faster to create than tar+Zstd-19.

Ties lose. `create_s` charges source scan, compact metadata construction, payload SHA-256, Zstd compression and archive publication exactly once. Every candidate is decoded and exact-tree verified.

The two reversible layouts were `inline-path` and deterministic extension-grouped `inline-ext`, across Zstd levels 1/3/6/9/12/15/19 and the frozen thread choices.

## Result

**6 / 15 workloads** had at least one jointly viable candidate. **9 / 15 did not.** Therefore this is conditional structural headroom, not a universal replacement.

| Workload | Winning candidate | Candidate bytes | Zstd19 bytes | Size win vs Zstd19 | Candidate create | Zstd19 create | ZIP create |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| neutral/07 incompressible+encrypted-like | inline-ext L12 | 10,189,063 | 10,199,302 | 10,239 B | 0.094023 s | 1.599925 s | 0.350665 s |
| neutral/08 many tiny files | inline-path L15 | 407,699 | 446,811 | **39,112 B** | 0.314267 s | 0.921476 s | 0.416069 s |
| neutral/10 large mixed binary | inline-ext L6 | 12,589,573 | 12,591,881 | 2,308 B | 0.058379 s | 1.245820 s | 0.388988 s |
| resemblance/01 shifted versions | inline-path L15 | 1,693,928 | 1,694,674 | 746 B | 0.249206 s | 0.747860 s | 0.828186 s |
| resemblance/02 false neighbors | inline-ext L3 | 34,643,456 | 34,660,112 | 16,656 B | 0.139537 s | 5.936839 s | 0.856463 s |
| resemblance/05 incompressible | inline-ext L1 | 10,607,692 | 10,616,616 | 8,924 B | 0.017866 s | 1.379209 s | 0.256704 s |

Across only those six viable rows, tar+Zstd19 totals 70,209,396 B and the selected oracle candidates total 70,131,411 B: **77,985 B / 0.1111%** aggregate size headroom versus Zstd19. Their summed create time is 0.873278 s versus 11.831130 s for Zstd19, approximately **13.55x faster** descriptively on this runner.

The strongest individual ratio headroom is speed, not bytes. Five of the six Zstd19 size wins are below 0.11%; `many_tiny_files` is the exception at **8.75% smaller**. This matters for carrying-cost judgment: a selector can exploit strict ties/wins, but most rows do not have enough byte margin to absorb a large canonical envelope.

The nine non-viable rows are:

- developer repository;
- office workspace;
- media library;
- analytics/database;
- Logs/telemetry;
- incremental backups;
- ML artifacts;
- boundary churn;
- Deflate family.

The aggregate closest residual Zstd19 size deficit across all 15 rows was only 10,702 B, maximum 5,306 B, but that fact does **not** authorize threshold relaxation or imply the failed rows are product wins.

## AOM and transfer interpretation

Within this deliberately hostile/resemblance corpus, the six viable rows represent:

- **6 / 15 workload identities (40%)**;
- **128,129,847 / 265,969,714 logical bytes (48.17%)**.

This is only a corpus-local, strongly biased opportunity estimate; it is not a claim that 48% of arbitrary real-world bytes are addressable. The structural transfer is nevertheless real enough to reject a single-workload-special-case interpretation: viable cases span tiny-file metadata pressure, high-entropy/incompressible data, one large mixed binary, shifted-version data, and false-neighbor data.

The result also does **not** justify a new primary Foundry thesis by itself. The mechanism is presently best classified as an R4 physical-layout/entropy-stage candidate using known primitives rather than an R5 new information ontology. The active Foundry may remain idle while this conditional R4 opportunity is tested for product survival.

## Global carrying-cost ledger

If promoted, the mechanism would add or require at least:

- content-derived nomination/admission without workload identity;
- a canonical typed framing and parser surface;
- strong archive/member integrity and hostile-input bounds;
- selective member/range access with <=8x decoded-context amplification;
- recovery/failure-domain semantics;
- native + Windows/macOS + Android parity;
- deterministic level/layout selection;
- candidate-audition cost for data where it loses;
- portfolio complexity versus existing r24/r25/PrefixGraph/Geometry paths.

Because five viable rows have small byte margins, these costs are not safely assumed to fit. The solid-stream form in this oracle is especially suspect for selective access because a small member may require decoding a much larger stream.

## Decision

`FAST_SOLID_INLINE_CONDITIONAL_HEADROOM_SUPPORTED`

The mechanism survives as a **conditional R4 research candidate**, not a product candidate and not a universal general-purpose breakthrough.

The next decisive experiment must attack exported debt rather than sweep more Zstd levels or metadata orderings: determine whether the observed winning rows retain joint size/create headroom when the representation is partitioned into deterministic bounded decode units that can plausibly satisfy the existing <=8x selective-read law and when the minimum canonical integrity/index/control charge is included.

If that bounded-locality + canonical-cost oracle destroys the size win on the transferred rows, retire this family rather than tuning the external benchmark. If material headroom survives on more than a trivial niche, only then justify a canonical Builder/admission design.

## Reopening / anti-sunk-cost rule

Do not repeat nearby level/thread/layout sweeps as the next action. v3 already explored the intended inline-path/inline-ext family across the frozen level/thread matrix.

A further layout sweep requires new causal evidence that a specific reversible ordering can pay the exported locality/integrity cost, not merely shave another few kilobytes in the unbounded solid-stream oracle.
