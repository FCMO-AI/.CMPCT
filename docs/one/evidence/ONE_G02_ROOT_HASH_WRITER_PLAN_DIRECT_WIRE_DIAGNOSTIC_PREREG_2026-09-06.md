# ONE-G0.2 root-hash writer plan-direct wire semantic diagnostic preregistration — 2026-09-06

## Mission lock

The frozen plan-direct canonical writer falsifier at exact source `9083603dff3cb311340b3c56429e0165cc2ec34e` terminated before timing with `AssertionError: plan-direct writer changed canonical semantics/oracle`. The full `tests/one` suite remained green (93/93), so the failure is isolated to the experimental candidate/oracle comparison rather than canonical ONE generally.

This lane is diagnostic only. It cannot promote the candidate and cannot alter any speed threshold. The original semantic failure remains preserved.

## Falsifiable hypothesis

The semantic failure is caused by a specific, deterministic mismatch between the candidate's plan-direct serialization and the already-authoritative Program-based writer. A first-failure diagnostic over the same frozen matrix can identify the exact mismatch field and first differing wire byte without changing writer semantics.

## Disproof

Reject this diagnostic hypothesis if the same exact-source inputs do not reproduce the failure, if the mismatch is nondeterministic, or if the diagnostic itself changes admission/plan behavior relative to the frozen source.

## Method

For the first mismatching row only, preserve and report:

- size and case;
- enabled/classification state;
- baseline/candidate `WireStats`;
- native plan signature equality and oracle equality;
- hierarchy depth and node counts;
- decode/evaluate reconstruction truth;
- baseline and candidate wire lengths;
- first differing wire offset plus a bounded hexadecimal context;
- baseline Program node op/declared-length/ref signatures and decoded candidate node signatures.

No timing is performed. No thresholds are changed. The diagnostic imports the frozen candidate and baseline functions directly.

## Decision

- If the mismatch is a candidate implementation defect that violates the preregistered byte-identical semantics, preserve `invalidate_plan_direct_wire_writer` for the original candidate. A corrected candidate, if causally justified, requires a new independent research ID/preregistration; it may not inherit the failed candidate's performance gate as a result.
- If the diagnostic reveals an oracle/diagnostic defect while candidate wire and evaluation are actually canonical, preserve that fact and amend only the diagnostic methodology before any new performance run.
