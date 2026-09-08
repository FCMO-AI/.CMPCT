# ONE-G0.2 trusted prior-root reuse hostile review — 2026-09-08

## Status

Pre-result hostile review. No performance result from this experiment is admissible unless it comes from a source at or after the commit containing this receipt and preserves the frozen preregistration unchanged.

## Mission

Try to reject the claim that adjacent-version creation should reuse an already-authenticated previous-root digest instead of rehashing the entire previous root inside every writer invocation.

## Strongest objections and dispositions

### 1. This can accidentally weaken authentication

A caller-supplied previous digest is not automatically trusted. The candidate is valid only for a persistent writer boundary where the prior generation's root identity has already been authenticated and retained as state.

Disposition: the benchmark explicitly computes an independent previous-root SHA-256 oracle before timing and requires both arms to embed that exact digest. The claim boundary excludes establishment/authentication of prior state. A green result cannot be cited as permission to trust arbitrary input digests.

### 2. The candidate could hide source conversion while the control pays it

Disposition: both arms perform source and target `ctypes.from_buffer_copy` inside the timed call. Only previous-root SHA-256 differs. Current-root SHA-256 remains charged in both arms.

### 3. The candidate could change the Program/wire because Root construction differs

Disposition: semantic probes require exact equality of admission, shift/proofs, Segment plan, canonical wire, Surprise bytes, reader work, Program root digests, segment count/capacity and reconstructed previous/current outputs.

### 4. A micro-win at one case could drive an architectural conclusion

Disposition: the decision scale is 1 MiB across five distinct temporal/control cases. At least four rows must independently beat `0.95x` on both wall and CPU. No 1 MiB row may exceed `1.02x`. Every 64 KiB row has a `1.05x` veto.

### 5. Missing matrix rows could exploit `all()`/count behavior

Disposition: the adjudicator requires the exact full `(size, case)` matrix before any gate can advance. A dedicated test removes one row and verifies HOLD.

### 6. The 5% threshold may simply measure SHA-256 implementation speed

That is partly the point: this experiment asks whether re-proving an already-known generation materially taxes the real writer envelope. It does **not** claim a new hash algorithm. If the cost is material, the system-level response is to preserve authenticated identity across versions, not to declare SHA-256 itself defective.

### 7. The benchmark may overstate product savings because previous-root authentication has to happen somewhere

Correct. Establishing the prior generation's authenticated identity is outside the candidate interval. The architectural hypothesis is that this cost belongs to the prior generation/open-state boundary and should be amortized/reused, not repeated per adjacent update. Product promotion would still need authenticated state-transfer/placement evidence.

### 8. Reusing the prior digest may be irrelevant when the previous root is not resident or comes from an untrusted source

Correct. This is scoped to persistent adjacent-version creation. Standalone import, repair, untrusted external bases and cold-open paths may still need a full prior-root verification. A future product writer may need separate trusted-state and untrusted-state entry paths without changing ONE representation semantics.

### 9. Garbage-collection or result teardown could contaminate alternating timing

The benchmark disables cyclic GC during the matrix and clears the owning `value` reference before the next pair's clocks. The returned value remains alive until both wall and CPU clocks stop. This follows the corrected lifecycle discipline established by the preceding ONE timing work.

### 10. A green result could be misused to justify authentication+observation fusion immediately

Disposition: prohibited. This experiment first decides whether previous-root rehashing is avoidable and material. Only the unavoidable current-root authentication cost may subsequently justify fusion with observation. A green result actually argues **against** fusing prior-root hashing into a new mandatory source pass.

## Falsifier integrity tests

`tests/one/test_trusted_prior_root_reuse.py` proves:

- a complete green matrix advances;
- only three material 1 MiB wins hold;
- one 1 MiB ratio of `1.021x` blocks advancement;
- one 64 KiB ratio of `1.051x` blocks advancement;
- semantic failure invalidates;
- a missing row cannot advance.

## Claim boundary if green

A green result may support:

> In persistent adjacent-version ONE research writing, carrying an independently authenticated previous-root digest across the writer boundary is a material compute optimization compared with rehashing the previous generation on every update, under the frozen matrix.

It may **not** support:

- weakening archive authentication;
- accepting unverified caller-provided digests;
- claiming full product ingest throughput;
- claiming a stored-byte or decode win;
- removing cold/untrusted previous-root verification;
- claiming authentication+observation fusion is already proven.

## Decision

The experiment is admissible after this review. Consume only exact-source evidence that includes this receipt and the unchanged preregistration/decision tests.
