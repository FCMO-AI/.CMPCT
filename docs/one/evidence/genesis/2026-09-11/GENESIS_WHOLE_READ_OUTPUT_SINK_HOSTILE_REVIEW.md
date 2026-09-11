# Genesis whole-read output-sink hostile review

**Date:** 2026-09-11  
**Status:** adjudication guardrail; no raw Genesis row is changed  
**Parent audit:** `GENESIS_WHOLE_READ_SEMANTICS_AUDIT.md`

## Finding

The first whole-read audit correctly identified that the frozen historical worker charges `strong_verify + extract + source/extracted-tree digest comparison` while ONE charges one authenticated open/read pass and hashes returned bytes inside its timed action.

A tempting repair would be to remove `strong_verify` from the historical clock and call `extract()` once. That is still not same-semantics throughput evidence.

The frozen product APIs expose different output sinks:

- ONE `open_authenticated_archive(...).read_file(...)` reconstructs regular-file bytes into process memory;
- frozen v0.29/v0.30 `extract(archive, dst)` reconstructs through their product extraction API into a filesystem tree.

Therefore a simple `ONE read_file loop` versus `historical extract` clock would charge directory/file creation and filesystem writes to the historical side while the ONE side keeps decoded bytes in memory. Removing `strong_verify` alone would make the benchmark look cleaner without actually making it fair.

## Consequence

Until an authority-backed same-sink measurement exists, whole-read speed remains **qualified diagnostic evidence only** and must not decide Genesis supersession.

Do not manufacture same semantics by:

- subtracting estimated filesystem time;
- moving only one contender to an internal/private decode function after seeing results;
- hashing bytes inside one product clock but outside another;
- dropping integrity work that is part of one product's ordinary reconstruction contract;
- counting a two-pass strong verification as ordinary one-pass decode throughput.

## Fair paths that remain open

A defensible future throughput audit needs one of these structures fixed before seeing result-bearing timings:

1. **same byte sink:** expose/identify frozen-authority byte-stream or in-memory reconstruction paths for all contenders, with ordinary integrity retained and identical external sink/hash placement; or
2. **separate product-operation costs:** report canonical product extraction/open-read latency as different operations and stop claiming they are the same throughput metric; or
3. **core reconstruction diagnostic:** instrument semantically equivalent internal reconstruction functions under a preregistered adapter contract, while keeping that evidence explicitly below product-authority level.

The source-owned exact-output oracle should remain outside the product timing and be identical in placement for every contender.

## What remains usable now

This qualification does not affect:

- deterministic stored bytes;
- creation CPU/wall/RSS where source/work semantics are matched;
- exact reconstruction success/failure;
- independently supported selective-access evidence;
- runtime-source provenance and frozen-checkout binding.

It only prevents an invalid read-throughput supersession claim from a measurement whose work and output sink are not equivalent.