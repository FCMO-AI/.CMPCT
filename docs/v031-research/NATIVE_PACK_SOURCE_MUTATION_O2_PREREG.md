# Native r24 S_PACK physical-source mutation court — O2 prospective

Date: 2026-10-24. Status: **preregistered BEFORE hosted product test**.
Parent question: issue #315 / PR #319 native PACK decode ownership O1. This O2 is the cheapest safety discriminator following a positive repeated-decode result, not a separate cache implementation claim.
Base: PR #307 exact frozen builder-independent `tests/conformance/v24-pack.json` and original Rust Reader; no format change and no mutation of the frozen golden files. Initial O1 run `40054009161` / candidate `b9bc385b40be4505343919b61e84f00bec43ca3f` found 160.68x *conditional one-decode oracle headroom* at N=256 Zstd reads, but an unsafe persistent cache would invalidate existing per-call SHA freshness.

## Primary falsifiable security question

On the **same open native `cmpct_open` handle**, does the current Rust `cmpct_entry_read_range` reconsult the physical Zstd packed-blob bytes/header and reject mutations made *after opening*, or might it silently reuse a previously authenticated decoded buffer? Prediction: a real valid fixed-byte Zstd PACK is readable; an in-place flip of the physical header's SHA-256 (with compressed payload/index unchanged) makes the next read fail, and restoration makes the same open handle read the original exact bytes again. Independently flip one byte inside compressed physical payload and demand refusal before any bytes return; restoration must recover. Positive controls: original immutable archive SHA and complete independent logical member hash; original valid fixed RAW pack. This test demands the source freshness the unsafe one-decode snapshot oracle lacks.

## Stronger and weaker controls

A separately created damaged file and new `cmpct_open` is too weak: it does not challenge open-handle retained state. A mocked codec/sha is also too weak. Use byte-in-place edits with one opened Rust ABI handle and physical offsets derived independently from frozen r24 header/physical record structs. Assert same pathname/inode/file size throughout and no appended material, and prove positive reads both before and after restoration. RAW physical PACK is an important *intentional* contrast: direct RAW range does not authenticate unseen bytes per call, so mutating a **requested** byte should change the next raw range output and restoring must reverse it; do not falsely demand full RAW SHA verification for ordinary selective range.

## Kill / decision

If Zstd same-handle read succeeds after physical SHA mutation or returns bytes after compressed corruption, source freshness is weaker than hypothesized and owner needs a specific physical-source-integrity issue. If it rejects and restores, the current Zstd strong-integrity behavior is established on frozen bytes and **a cross-call decoded cache that retains bytes without reauthentication has a new proven regression debt**. Per-batch verified ownership might avoid repeated decode within a single explicit immutable operation, but must still bound RSS and reject mutation inside batch or define a stronger snapshot contract.

## Scope

O2 modifies only ephemeral copies of independent fixed goldens in a temporary directory. No Builder/native/Reader/index/format/compiler changes, no historical golden edits, release gate or thresholds change. Small bounded edits to same exact byte offsets, SHA-256 source hashes preserved in repo, no private inputs. All outcomes are conformance/correctness research; no cache, release or product timing credit. PR #307/#314 native PACK controls remain owners and untouched.
