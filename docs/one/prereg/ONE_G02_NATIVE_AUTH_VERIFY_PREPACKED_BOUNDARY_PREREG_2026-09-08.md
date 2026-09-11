# ONE-G0.2 native auth verifier — prepacked boundary preregistration

**Date:** 2026-09-08  
**Branch:** `research/cmpct1`  
**Experimental version:** `ONE-G0.2`

## Mission lock / Referee

The exact-source native verifier at `1e6a08a005f8fdb9e2b510b85752d1b229b12dd9` returned `HOLD_NATIVE_AUTH_VERIFY`. All semantic and hostile integrity gates passed, but the charged wrapper exceeded the frozen performance ceiling, especially at 192-byte leaves where three of four rows were approximately 1.11x–1.17x the Python reference.

The current wrapper repeatedly joins payload tuples, copies payload bytes, allocates/populates ctypes sibling coordinate/hash arrays, copies the expected root, then calls the native interval fold. The strongest causal hypothesis is therefore that **proof-boundary marshalling, not the native hash/fold itself, prevents broad advancement**.

## Falsifiable hypothesis

If the exact same `RangeProof` elements are marshalled once into stable ctypes buffers outside the hot verification call, the unchanged native interval verifier will:

1. recover the original native-verifier performance target against Python verification; and
2. show a material direct improvement versus the fully charged native wrapper.

This is a causal implementation probe, not a proposed canonical proof format.

## Frozen matrix

- source size: exactly 1 MiB;
- deterministic source seed: `0xA075B0D1`;
- leaf sizes: 80, 96, 112, 192 bytes;
- requests per leaf size: first 4 KiB, middle 4 KiB, final 4 KiB, middle 64 KiB;
- 16 unique decisive rows;
- 21 measured repetitions after two warmups;
- three arms rotate order across repetitions: Python control, fully charged native wrapper, prepacked native kernel call.

## Hard semantic/integrity gates

Every row must reconstruct exactly the requested bytes through all three paths. The existing native hostile-root failure check remains mandatory. Unit tests separately require prepacked verification to reject tampered payload, sibling digest and expected root.

Any semantic or hostile failure yields:

`INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY`

No performance result can override integrity failure.

## Frozen performance gates

Against Python verification, prepacked native verification must:

- remain `<= 0.65x` on **both wall and CPU for all 16 rows**;
- achieve `<= 0.50x` on **both wall and CPU for at least 12/16 rows**.

To establish that the removed boundary itself is materially causal, prepacked native verification must also:

- remain `<= 1.03x` the fully charged native wrapper on both wall and CPU for every row;
- achieve `<= 0.90x` the fully charged native wrapper on both wall and CPU for at least 12/16 rows.

Otherwise the result is:

`HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY`

The thresholds are frozen before hosted result-bearing evidence.

## Cost boundary

Preparation outside the hot call includes only work already performed by the current native wrapper on every call:

- joining proof leaf payloads;
- copying the joined payload into a stable ctypes buffer;
- validating and materializing sibling level/index/hash arrays;
- copying the expected root to a stable ctypes buffer.

The timed prepacked call still pays for:

- Python function dispatch;
- the ctypes call itself;
- native verifier scratch allocation/free;
- every SHA-256 leaf/parent/root operation;
- root comparison;
- output allocation;
- copying authenticated requested bytes into the output;
- conversion of the output to Python `bytes`.

Proof payload/hash traffic and authentication grammar are unchanged.

## Disproof / retirement

If the prepacked path fails the original control gates, the native interval fold is not strong enough in this shape and further wrapper shaving should stop.

If it beats Python but does not materially beat the charged native wrapper, the prior HOLD cannot honestly be attributed to repeated proof marshalling; investigate measurement or a different owner before fusing APIs.

If it passes both groups of gates, the correct next engineering target is a single packed proof/selective-open boundary that avoids constructing and then re-marshalling a Python `RangeProof` in the production hot path, while retaining Python proof objects as oracle/debug machinery.

## Claim limits

A pass does not authorize:

- changing the reader-visible ONE Law + Surprise grammar;
- weakening authentication;
- claiming a persistent-index density solution;
- claiming full product selective-open latency;
- making OpenSSL/libcrypto a canonical portability dependency;
- removing the independent Python verifier/oracle.
