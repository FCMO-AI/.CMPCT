# CMPCT transcription normalization

This file records a repository-wide terminology normalization for user speech transcribed by ChatGPT.

## `CSTD` means `Zstd`

Any user-originated mention of **`CSTD`** (including forms such as `CSTD-19`, `CSTD 19`, or similar variants) is a speech-to-text mishearing of **Zstd** / **Zstandard** unless an explicit later instruction says otherwise.

Interpret examples as follows:

- `CSTD` -> `Zstd`
- `CSTD-19` -> `Zstd-19`
- `CSTD level 19` -> `Zstd level 19`

`CSTD` is **not** a distinct CMPCT codec, competitor, benchmark family, or project term. Do not create new technical meaning from that transcription artifact, and do not propagate it into new benchmark names, engineering claims, or documentation.

When editing mutable prose or new evidence, normalize the term to `Zstd`. Do not rewrite immutable/frozen historical evidence solely for this spelling correction; if such an artifact ever contains `CSTD`, preserve the artifact and interpret/annotate it as `Zstd`.
