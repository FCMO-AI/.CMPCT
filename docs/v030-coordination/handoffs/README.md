# v0.30 handoff records

Task files carry current state. Add a handoff file here only when a task reaches `REVIEW`, is reassigned, or exposes a new cross-slot dependency worth preserving.

Name handoffs `YYYYMMDDTHHMMZ-TASKID-short-name.md`.

Every handoff must record:

- source task and owner slot;
- source branch and exact head SHA;
- integration SHA the work started from;
- intended import scope (whole commits vs specific files/blobs);
- changed semantics and invariants;
- tests/benchmarks actually executed;
- durable evidence paths/run IDs when available;
- known losses, ambiguity, platform gaps, or regression debt;
- expected conflicts with main/integration/other slots;
- recommended next task/dependency change.

Do not use a handoff file to claim a benchmark pass that is not represented by actual evidence.
