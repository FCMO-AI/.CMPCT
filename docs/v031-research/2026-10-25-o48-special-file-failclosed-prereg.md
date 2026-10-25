# O48 — fail-closed revision-24 admission of unsupported special filesystem entries

Date: 2026-10-25 UTC. **Prospective preregistration.** This is an independent narrow source-tree completeness lane, not a new compression mechanism or a format revision.

## Exact authority and observed source-level risk

Canonical main `80c358f8824ec1b20d349c92ed94c898090969b0` and v0.31 development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` share `src/cmpct/builder.py` blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. In `Builder.scan()`, symlinks, directories, and regular files are materialized; every other `stat.S_IFMT` type reaches `if not stat.S_ISREG(st.st_mode):continue`. This is a source-level fact, not yet a hosted outcome. The r24 index exposes no accepted FIFO/socket/block/character kind. A successful archive of a tree containing such entries could therefore silently omit them while reporting success.

## Primary question and prediction

Can a real authentic Builder be made to *appear successful* while silently dropping existing POSIX FIFO and Unix-domain socket filesystem entries? **Prediction for the unchanged baseline:** it succeeds and the resulting authenticated archive omits those names. This is a high-severity semantic truth gap regardless of archive size.

**Candidate mechanism:** default fail-closed admission, raising an explicit `OSError` when an entry is neither symlink, directory nor regular file, identifying that unsupported type, rather than silently publishing an incomplete archive. This does not add support for reconstructing special files, does not change revision 24, and does not turn them into ordinary empty files.

## Simpler controls, alternatives, and kill condition

Controls: a regular-file/directory/symlink tree still archives and reconstructs identically (including reproducible SHA); an unsupported FIFO and Unix-domain socket fail before successful `Builder.build()` return. A mixed tree should not be mistaken for a complete archive. For sockets, merely creating a bound filesystem socket is enough: never read from FIFO/socket or block on special input.

Alternative explanations: an outer CLI/admission layer may already reject special files; platform adapters may explicitly document a best-effort ignore contract. We must inspect public CLI and current frozen semantics before promoting default-behavior change.

Alternative solutions:
1. support special entries in a new format (not an r24 safety repair; needs clear semantics);
2. permit silent skip (unsafe for a user expecting an exact archive; baseline control);
3. expose an **explicit opt-in** ignore mode with a lossiness receipt (higher complexity, no evidence of product need);
4. reject unsupported files before publishing any archive (bounded, simplest truthful choice).

**Kill/narrow:** if existing public product contract explicitly promises exclusion of special entries and users are informed per skipped path, the case is not an unannounced loss; if upstream already reliably errors, skip this code change. If the candidate alters valid regular/symlink/dir inputs, format bytes, reader, native ABI or release evaluators, do not promote. If POSIX-specific tests cannot execute, classify evidence as static until a genuine hosted court runs. The existing test source must not be made green by skipping unsupported cases.

## Hosted falsifier and product verification plan

1. Commit this prediction before tests/product mutation.
2. On Linux/macOS with no mocked Builder, create `os.mkfifo()` and a bound `AF_UNIX` socket inside a source tree. Check no archive success on candidate. On Windows, skip the unsupported construction with documented reason, and still exercise ordinary fixtures.
3. Run the unchanged baseline behavior as a separately frozen negative, with its exact source identity. Use temp source and output, one-worker/reproducible Builder, true Reader verification and extraction for legal shapes.
4. Retain source-exact logs/JUnit with **actual executed case counts**. Do not claim broad installed-wheel or full product promotion before true job evidence.
5. Account for extra CPU/bytes: just one branch on the unsupported path; archive size and encoding of valid trees must be byte-identical. A real source-structure difference is *not* a valid r24/ZIP performance comparison.

## Concurrency and safety

PR #401 owns the separate Windows *regular-file physical hardlink* admission change in the same `Builder.scan` neighborhood. This branch is based on the frozen v0.31 development SHA and MUST NOT overwrite/rebase or supersede that owner; keep this one-line type rejection logically independent, later reconcile both changes before integration. No global discovery cache update unless decision-changing evidence earns it. No merge/tag/release authority from this draft.
