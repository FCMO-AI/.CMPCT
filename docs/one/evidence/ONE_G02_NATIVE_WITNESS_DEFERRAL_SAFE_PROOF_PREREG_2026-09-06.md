# ONE-G0.2 native witness-deferral + safe-proof A/B — preregistration

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Mission Lock

The corrected reference experiment established that an exact 64-byte witness can act as an Opportunity Gate and reduce relation-specific proof traffic to 0.170168x baseline without losing a required relation. Separately, the overlap-safe generic relation dispatcher has exact semantics and a proven disjoint no-alias fast path, and fused nomination now carries a demand-grown event index rather than the old fixed 198,144-byte prototype.

The next question is whether the witness-first principle survives native execution once the same safe relation proof is charged. This experiment intentionally begins with the already-validated native selector trace + native event consumer boundary. It is a native causal transfer before modifying the fused observer itself; a result here is not yet fused-writer promotion.

## Frozen arms

Both arms receive the exact same native minimizer trace and run the same native nomination scan/index policy.

**Baseline:** on the first cross-object exact 64-byte witness, perform the existing exact-reuse left/right extension work up to first relation nomination, then execute the same overlap-safe relation proof.

**Candidate:** on the first cross-object exact 64-byte witness, do not extend. Treat the witness only as an Opportunity Gate and immediately execute the same overlap-safe relation proof.

After the first accepted relation nomination, relation-specific audition/extension work is outside both arms' measured boundary, matching the corrected symmetric accounting law. Index maintenance needed to preserve the same nomination opportunity remains charged.

The safe relation proof is sole Law authority. The 64-byte witness can never emit a Law by itself.

## Safety / overlap law

The safe dispatcher may use its no-alias path only when source, target and result spans are proven disjoint. Explicit overlapping layouts must select the conservative fallback and remain semantically exact. A blanket `restrict` contract is forbidden.

## Frozen matrix

Sizes: 4, 8, 16, 64 and 256 KiB. Seeds: 7, 29 and 53.

Cases: `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`, plus explicit same-pointer/forward-overlap/backward-overlap safety probes.

## Measurements

Record per row:

- baseline/candidate elapsed under alternating A/B-B/A order;
- verification and extension read bytes;
- safe-proof coverage/proof compared bytes;
- proof attempts/exact proofs;
- cross auditions and accepted relation nominations;
- dispatcher path;
- index peak entries and state accounting inherited from the trace/consumer boundary.

## Promotion / disproof law

All semantic and safety gates are hard:

- identical accepted/rejected relation decisions between arms;
- no false accepted Law on `fragmented_every32` or `independent_random`;
- every overlap probe selects safe fallback;
- no required positive accepted by baseline may be lost by candidate.

Performance advance requires:

- productive median candidate/baseline elapsed <= 0.95x;
- no productive row > 1.03x;
- every negative-control size median <= 1.03x;
- candidate relation-specific compared/read traffic <= 0.70x baseline in aggregate.

Decision is `advance_native_witness_deferral_safe_proof` only if all gates pass. If semantics pass but elapsed does not, return `hold_native_witness_deferral_safe_proof`; if any semantic/safety gate fails, `reject_native_witness_deferral_safe_proof`.

## Claim boundary

A pass proves native causal transfer at the selector-trace/event-consumer boundary. It does not yet prove a one-pass fused writer, product creation speed, stored-byte superiority, authenticated placement, selective-read integrity, or comparator supremacy. The next step after a pass is to move the same accepted boundary into the demand-grown fused observer and remeasure total carrying cost.
