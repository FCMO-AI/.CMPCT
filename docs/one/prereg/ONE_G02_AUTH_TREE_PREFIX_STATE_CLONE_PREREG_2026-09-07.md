# ONE-G0.2 AuthTree SHA prefix-state clone A/B — preregistration

## Mission Lock / Referee

**Experimental version:** ONE-G0.2  
**Scope:** writer-side implementation of the existing AuthTree byte grammar only.  
**Non-goals:** no wire-format change, no digest truncation, no weakened integrity, no fanout/leaf tuning, no reader change, no v0.29/v0.30 promotion claim.

The resource-accounted multi-buffer experiment at source head `502e2e75a0d78ab4d164c3b73188ab804caf17f3` rejected node-count dispatch: the candidate remained slower across 1 KiB-256 KiB and staged about 1.86 source-equivalents at large roots. The next experiment therefore removes staging and attacks repeated per-node SHA initialization/domain-prefix work instead of adding parallel batching.

## Frozen hypothesis

For current AuthTree semantics, many SHA messages share a fixed prefix:

- every leaf begins `ONE-L\0`;
- every parent at one level begins `ONE-P\0 || le32(level)`;
- the root commitment begins `ONE-R\0 || le64(total) || le32(leaf_bytes)`.

Initializing and hashing those fixed prefixes once, then copying the resulting `SHA256_CTX` into each independent node hash, should reduce writer CPU/wall time while presenting exactly the same byte stream to SHA-256 and without copying source payloads into staging arenas.

This is a research implementation technique, not a new ONE Law or reader primitive.

## Candidate

Baseline is the current native OpenSSL streaming grammar: `SHA256_Init`, domain/meta/payload `SHA256_Update` calls, `SHA256_Final` per node.

Candidate:

- preinitialize one leaf SHA context with `ONE-L\0`; copy that context for each leaf, then hash the leaf-specific `<index,total>` and payload;
- preinitialize one parent SHA context per tree level with `ONE-P\0 || le32(level)`; copy it for each parent, then hash the exact two 32-byte child digests;
- preinitialize the one root context with `ONE-R\0 || le64(total) || le32(leaf_bytes)`, then hash the top digest;
- perform no payload/message staging introduced by the candidate.

The candidate must emit byte-identical roots to baseline for every row.

## Frozen corpus and timing

Deterministic pseudo-random roots at bytes:

`1 KiB, 2 KiB, 4 KiB, 8 KiB, 16 KiB, 32 KiB, 64 KiB, 128 KiB, 256 KiB, 512 KiB, 1 MiB`

Leaf size is frozen at 112 bytes, matching the current authenticated selective-access research point. Use at least 31 repetitions per implementation per row; alternate measurement order; report median monotonic wall time and process CPU time. Compile both paths into the same native executable with the same compiler flags and OpenSSL library.

All allocation/tree-storage work performed inside one implementation's timed build must be performed equivalently inside the other. No prebuilt tree, prehashed payload, cached candidate output, or root oracle may sit outside candidate timing unless the same work is outside baseline timing.

## Frozen advancement gate

Advance prefix-state cloning as the preferred native AuthTree construction shape only if:

1. every candidate root equals the baseline root;
2. no malformed/accounting condition is observed;
3. for every root >= 8 KiB, candidate median wall ratio is <= 0.97x baseline;
4. median wall ratio across roots >= 8 KiB is <= 0.92x;
5. median process-CPU ratio across roots >= 8 KiB is <= 0.95x;
6. no root of any size regresses beyond 1.05x wall or 1.05x CPU;
7. candidate-added staging bytes are exactly zero and candidate-added explicit workspace is bounded by SHA context prefixes: one reusable leaf context plus one current-level parent context plus one root context, independent of root size.

If exactness passes but performance misses any frozen gate, preserve the result as a negative or partial seed. Do not rescue it by changing leaf size, excluding failed rows, weakening ratios, or composing it with the rejected multi-buffer path in the same experiment.

## Hostile Reviewer questions

- Does `SHA256_CTX` copying actually save work on the hosted OpenSSL/CPU, or merely replace cheap initialization with equivalent memory copying?
- Does OpenSSL already make initialization/prefix processing cheap enough that payload compression dominates?
- Are gains limited to tiny messages while leaf payload hashing dominates large roots?
- Does the deprecated low-level OpenSSL API make this only a research clue rather than a portable implementation strategy?

A positive result establishes only a causal implementation seed. A production/native ONE core would still need an implementation-neutral or explicitly supported SHA state-clone abstraction and broader ingest evidence.
