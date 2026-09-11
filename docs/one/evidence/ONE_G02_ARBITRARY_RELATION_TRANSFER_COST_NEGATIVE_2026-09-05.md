# ONE-G0.2 — Arbitrary relation structural-transfer cost negative

**Experimental line:** `ONE-G0.2`  
**Branch:** `research/cmpct1`  
**Status:** immutable negative evidence / first arbitrary-offset implementation retired  
**Result-bearing source:** `a8174f48a0b74b9f678c00e8fc4f2fcc657b6837`  
**Workflow:** `33961664568`  
**Job:** `101294480847`  
**Artifact:** `9968143331`  
**Artifact zip SHA-256:** `a4a417dd6128e8e6d7f2462f0191a2a82947d9ba8080c19a5b2dbd4977d56a07`

## Frozen question

The proof-led branch-and-bound admission law had only been exercised on an artificial half-to-half layout. The structural-transfer experiment moved the same relation into three independent source/target placements inside a 512 KiB carrier, at relation sizes 8, 32 and 64 KiB. Promotion required exact placement-invariant classification/proof behavior, <=25% modeled relation reads, and for 32/64 KiB relations <=1.10x elapsed versus the equivalent half-to-half proof-led kernel.

## Exact result

`tests/one`: **76 passed**.

Semantic transfer was complete:

- every positive +1 relation was admitted at every placement;
- quarter-damaged +1 relations remained admitted;
- every-96-byte fragmented positive controls remained admitted;
- every-32-byte fragmented false relations remained rejected with zero exact proofs;
- independent random controls remained rejected;
- nominated shift / proof signatures were placement invariant.

The experiment nevertheless returned:

> `retire_arbitrary_relation_transfer`

because the arbitrary-offset implementation exceeded the frozen compute ceiling.

### Cost evidence

At **32 KiB**:

- clean +1: **1.218–1.236x** half-layout elapsed;
- quarter-damaged +1: **1.257–1.285x**;
- every96 positive: **1.223–1.233x**;
- every32 negative: **1.220–1.223x**;
- random negative: **1.234–1.250x**.

At **64 KiB**:

- clean +1: **1.187–1.202x**;
- quarter-damaged +1: **1.176–1.179x**;
- every96 positive: **1.196–1.207x**;
- every32 negative: **1.190–1.193x**;
- random negative: **1.163–1.168x**.

The smallest 8 KiB rows were slower still (roughly **1.36–1.46x**) and one every96 row used **27.22%** modeled relation reads, above the 25% ceiling; those small-row bounds were diagnostic because the frozen relative-cost promotion limit applied to 32/64 KiB.

## Causal interpretation

This is not a semantic failure of proof-led admission. It is a code-shape failure in the first generalized kernel. The arbitrary implementation repeatedly carries `source_offset` / `target_offset`, performs relation-bound checks and constructs absolute addresses inside hot coverage/proof loops. The half-layout kernel works directly from one compact coordinate frame.

The clean transfer signature across all three placements is evidence that the relation algebra itself is location-independent. The exported debt is therefore the cost of representing arbitrary placement in the hot loop, not a need for another admission threshold.

## Superseding predicate

A superseding Builder may change only address formation / loop representation while preserving the exact arbitrary relation API, frozen corpus, proof-led admission semantics and <=1.10x / <=25% gates. A natural lowest-sufficient intervention is to validate bounds once, rebase source/target pointers before iteration, and keep all hot coordinates relation-local. If that fails, investigate compiler/codegen shape before altering the branch-and-bound law.

## Claim boundary

Writer-side structural transfer only. Candidate-pair discovery remains external. No reader-visible ONE operation, stored-byte claim, v0.29/v0.30 comparator claim or release authority changes.
