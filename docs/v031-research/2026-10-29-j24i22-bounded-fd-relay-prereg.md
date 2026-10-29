# J24I22 — Source-FD bounded physical-record relocation (prospective preregistration)

Date: 2026-10-29 UTC. Parent #742 exact `eb4de9b65417987fdf69975237431b5473877e30`. Research-only, revision-24, **not a production compactor**. Frozen before implementation/test.

## Primary question and predictions

Can J24I18b's latest-checkpoint live-record relay be executed using an **opened source file descriptor** and bounded physical-I/O buffers without materializing the entire source archive, while retaining the same live physical record bytes and logical filesystem semantics?

P1: an O_NOFOLLOW-opened regular source held by FD, with at-most-32-MiB index decompression and <=128-KiB physical streaming buffers, transforms the original #723 1,382-B two-blob journal into the same 1,176-B physical archive as J24I18b; source and result logical bytes, hardlink/symlink topology and metadata match an independent parser. Eight old physical fixture classes are equality controls; no fixture-name dispatch in the transform.

P2: a synthetic **64-MiB incompressible RAW** physical record can be relocated with source/output byte identity and measured child-process incremental peak RSS < 48 MiB above a warm empty-process control. This is an oracle resource bound on this corpus, not a product memory guarantee or proof for every codec. An unsupported codec or malformed signed descriptor must fail before publishing.

P3: a source mutation **after index admission but before physical stream copy** must be either rejected by a changed header/payload content proof or change the source identity witness. If the relay accepts an output derived from content that no longer matches the signed physical blob SHA-256, its custody hypothesis fails. Do not assume that source FD makes content immutable.

## Strong simpler controls / alternatives

- Preserve unmodified J24I18b full-memory relay as output/size/metadata control for small physically authentic input.
- Preserve existing Builder-based compaction (#723/#738) as real product control; this branch does not change it or claim superiority.
- A full source-in-memory buffer is simpler, but by construction scales O(physical archive size). A tempfile snapshot/reflink may improve mutation safety but exports I/O/space and is **not** silently assumed free.
- Independent #741/#745 stage publication/ownership work owns destination safety; this branch intentionally does **not** create a competing production publisher.

## Evidence ladder and falsifiers

1. Local POSIX Python+msgpack+libzstd source-FD relay: index via bounded pread, signed HEAD and tail/generation validation; strict known storage closure; per-record header and logical SHA256+CRC32 verification, bounded streaming; no pathname reopen for record bytes. Require exact SHA of output vs J24I18b for 1,382-B delta fixture.
2. Detached physical original/output audit using independent J24I06 parser, 8 original fixture types, plus authentic installed CMPCT Builder/append_update/Reader hosted run where practical.
3. Held-out structural corpus with a physically large RAW content record (64 MiB, deterministic seeded bytes) and same semantic archive; measure child max RSS and wall, include the input size/physical hashes in receipts.
4. Hostile checks: corrupted payload/header, bogus blob ID, dead blob policy, source mutation between admission and streaming, symlink source refusal and incomplete footer. Fail closed. Never weaken historical frozen tests or mutate release comparators.

Kill/narrow: any unauthenticated physical record accepted, logical/metadata mismatch, output larger than matched full-memory control on identical input, or 64-MiB RSS increase >=48 MiB disproves the scoped claim. If source mutation after fully finished proof but before final publication cannot be excluded, keep a **concurrent-source custody veto**. Do not promote to product or general TOCTOU certification.

## Charged system scope

Record complete old/new stored bytes, live/dead blobs, verification CPU/wall, RSS, physical read/write bytes where measurable, index bound, stream buffer size, incomplete codec/recipe coverage, temporary file bytes, exact source SHA, and unsupported-platform debt. No full v0.31 benchmark or cross-platform claims until independently exercised. Python helper process, staged scratch writes and bounded index memory count in real total cost. No version, format, release, license, frozen comparator or Discovery STATE changes.

## Coordination

This is a continuation of previous Phase3 #742 J24I18 representation work, not a duplicate of #738/#741/#745 compaction product source or #620 Reader SHA hardlink work. Preserve any independent negative. After result, leave a minimal decision-complete PR handoff; do not mark source FD immutable under a mutable writer.
