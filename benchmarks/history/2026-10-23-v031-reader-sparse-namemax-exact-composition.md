# v0.31 — sparse logical integrity × NAME_MAX × three-owner Reader × prospective CI

**Date:** 2026-10-23
**State at writing:** PREREGISTERED; no combined candidate source modifications or result observed.
**Class:** integrated exact-source product correctness/evidence court; not a release, representation gain or benchmark win.

## Canonical authority and ownership

- Released checkpoint: CMPCT v0.30.0, on-disk revision 24.
- Development source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Parent prospective-CI × three-owner integration PR #268 head `34ca9c34fd313fff21d92577d711f82a561f75a4`: hardlink owner ordering (#262), PACK physical SHA (#258), worker join (#231), prospective candidate-source identity (#266). Preserve all parent blobs except narrowly necessary Reader integration edits.
- Sparse logical-SHA/failure-atomicity owner PR #255 head `a2afcb8302214ac05c30ae5ef32267dda987b48e`: import `src/cmpct/sparse_extract.py` and `tests/test_v031_sparse_verified_extract.py` *byte-identically*; substitute only its sparse `extractall` case.
- Chunked NAME_MAX owner PR #256 head `c893117e1caed1807443601c97393bc67aeb27c8`: import `tests/test_v031_chunked_namemax_staging.py` *byte-identically*; apply only its bounded short staging prefix.
- Active adjacent destination-symlink owner PR #269 has overlapping Reader and distinct threat model. Do not copy its static-only policy or promise race-safe extraction; #269 remains independently owned.

## Why this integration is needed

A Reader green separately for PACK/hardlink/close and for sparse logical-SHA and valid full-length POSIX names is not proof of coexistence. The sparse owner itself stages using `'.'+basename+'.cmpct-part-'`, which fails `NAME_MAX` on 255-byte valid basenames. Repair *that* interaction using the same short private stage naming proved for chunked files; do not modify the canonical filename, serialized record or identifier.

## Falsifiable primary question

Can one authentic revision-24 Reader retain the three verified owners + prospective candidate CI source identity and simultaneously (a) authenticate logical sparse holes before replacing any preexisting destination and (b) extract valid long-name sparse and CDC members without losing inode/content atomicity after forged SHA?

### Required outcome

1. Read exact source for all five owners; source and test blobs unchanged except scoped transplant Reader and sparse-helper prefix.
2. Hosted installed-package suites: 7 hardlink-owner, 3 PACK, 4 worker-close, 1 PACK×hardlink, 7 sparse-owner test cases, 4 NAME_MAX parametrizations, plus added *cross-owner* sparse `NAME_MAX` corruption/atomicity case. No skipped test credited.
3. A genuine Builder-created sparse or frozen independent r24 conformance sparse record with a 255-byte POSIX pathname must extract, preserve length, logical SHA, sparse hole bytes and (after in-memory SHA forgery) preserve previously materialized bytes/inode and clean up stage.
4. Full `CMPCT tests` exact combined HEAD must pass; targeted or workflow-only green cannot authorize promotion.
5. No change to `docs/V030_RELEASE_LOCK.json` or historical benchmark records; no weakened verifier, release gate, comparator, CI admission, format law, version, or threshold.

### Controls, negatives and debt

- Baseline inherited `S_SPARSE` extract path truncates without verifying full logical SHA (PR #255), while prior sparse staging has name-derived NAME_MAX failure (PR #256 observation).
- Simple control: adopt original sparse-owner helper unchanged. Kill if this can pass a verified 255-byte long-name sparse case; no extra code then justified.
- Alternatives: (i) direct `Reader.read()` then ordinary write consumes full logical memory; (ii) stage under global temp breaks same-filesystem atomic rename; (iii) reject/truncate long names loses filesystem identity. Retain short same-directory randomized O_EXCL name.
- Include CPU/RSS/sparse-hole logical hashing cost and portability debt. O(logical sparse size) hashing is a security/exactness cost; if unaffordable, redesign proof representation, not silently omit it.
- This integration is **not** a race-safe capability-root extractor. Symlink/hardlink preexisting destinations and concurrent TOCTOU require independent #265 resolution; keep #269 separate.
- Preserve negative CI runs, exact HEADs and skipped jobs. No release/product performance claims before genuine same-runner gate and host/platform controls.

## Coordination and stopping condition

Treat parent PR #268, owner #255 and #256 as independent; no edits to those refs. If an active PR has already implemented the *same* exact five-owner composition before mutation, stop duplicate implementation and contribute independent result/evidence there. Maintain this branch as stacked, draft, not merged. Scientific decision is either **COMPOSED/FUNCTIONAL WITH PROMOTION DEBT**, **FALSIFIED**, or **BLOCKED** with exact culprit and evidence.
