# O129 — A12 cross-wrapper exact Deflate physical-root oracle (preregistration)

Date: 2026-10-25 UTC. Independent Phased3 Foundry lower-rung study. Canonical development source: `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, released 0.30.0, format revision 24. No reader/writer/format/release/frozen-test mutation. Before this preregistration, GitHub PR search found no active owner for this *narrow cross-wrapper compressed-byte identity question*. CMPCT already has ZIP Deflate reuse and gzip inverse edges: they are stronger inherited prior art, not ignored novelty.

## Question and mechanism
Does a content-discovered **identical RFC1951 compressed payload** present inside byte-distinct RFC1952 gzip, RFC1950 zlib and raw-Deflate views provide a practical A12 exact-view ownership opportunity, after charging every wrapper byte, decode-visible owner fact, full physical root, member descriptors and complete archive-level cost, versus a *strong simple same-input* solid Zstd-19 control? Compare also independent Zstd-19 members. This is different from sharing decompressed plaintext or ZIP internal raw stream reuse: byte identity of the *compressed physical information root across framing grammars* is the proposed owner.

## Falsifiable prediction
For repeated byte-identical compressed payloads under distinct legitimate wrappers, there will be some large-member/large-cohort regime with complete charged size below solid Zstd-19 while conserving exact reconstruction and <=8x member-local physical-read and decode-unit amplification. One member and unrelated compressed streams should favor simpler fallback. Hold-out regimes must include structurally distinct plaintext distributions and independent seeds. No assumed payoff on all corpora.

## Strong controls / alternative explanations
- Solid Zstd-19 of the *exact same ordered wrapper files* plus the same path/length index charge: Zstd may already deduplicate common binary spans more cheaply; **it is allowed to win**.
- Per-member Zstd-19 plus the same path index and framing.
- Raw physical-byte identity does not imply equality of decoded content or all alternate compressions. Exact source-root equality is checked bytewise, not inferred from CRC, file extension, filename, dictionary, or fingerprint alone.
- Headers/trailers are kept literally, including gzip mtime/filename/CRC, zlib RFC1950 header/Adler and any raw stream byte count. No decoder-implicit per-file properties gifted.
- The proposed representation stores each distinct RFC1951 bitstream exactly once, its original literal per-member prefix/suffix, root reference, lengths, path/index bytes, and a fixed measured additional model/container overhead. Compare full charged bytes, not an unpriced internal sum.
- Analyze invalid/raw-lookalike and different-compression-level cases; detection/validation must be exact and bounded, while research selection search cost is reported separately.
- For each member, count root physical bytes + framing+index and all required reconstruction bytes, depth 1. A solid Zstd stream has full-solid read amplification where selective access demands it.

## Cheapest decisive experiment / kill
First implement a small deterministic stdlib Python oracle using actual gzip/zlib/raw framing and **external Zstd-19** as the strong control (same inputs and ordering); four seeds each from at least: repetitive telemetry, mixed structured records, incompressible payload, and unrelated payloads; vary number of views 1/2/4/8 and include some nonidentical compressed levels. Verify every output exactly. Report raw per-case bytes, index accounting, physical selective-read/decode amplification and any negative. If solid wins across all meaningful positive regimes, NARROW/RETIRE this specific A12 framing family without implementing a new CMPCT storage kind. If a win survives, it remains O0/O1 science only pending real CMPCT Builder/Reader/format/portable/runtime/security/benchmark gates. No claims about a released feature or full generality.

## Decision / scope boundary
One primary question, no parallel sibling implementation. PR is a scientific court, no promotion. Artifact / negative source results must be durable. Do not modify `docs/discovery/STATE.json` absent a decision-changing finding and concurrency reconciliation; do not change Discovery Engine rules.