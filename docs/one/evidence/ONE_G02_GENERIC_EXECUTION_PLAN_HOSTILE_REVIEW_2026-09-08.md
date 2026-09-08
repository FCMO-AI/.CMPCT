# ONE-G0.2 Generic Execution Plan — hostile review before result

Status: preregistered, no hosted performance verdict yet.

The candidate is intentionally broader than the retired terminal-specific line: every existing ONE operation participates in the same compiled representation and executor. The benchmark includes XOR/add8 and sliced/multi-parent composition so a Fill-specific implementation cannot pass by accident.

Hostile constraints:

- `_preflight` remains mandatory before plan construction; compilation cannot bypass cycle, depth, output, range, declared-length, work, or root-shape checks.
- Unreachable stored nodes remain compiled/validated so validity cannot depend on current roots.
- Root SHA-256 remains charged on every replay.
- Compilation is measured separately; repeated-read evidence may not be narrated as cold-read evidence.
- The executor preserves the reference VM's work accounting exactly in semantic tests.
- No corpus/family dispatcher is allowed. A red XOR/add8/reuse row remains a real red.
- No reader-visible grammar change is authorized by a green result.

Strongest expected failure mode: for large bulk arithmetic, byte processing dominates recursive graph-control overhead, so a Python topological plan may be neutral or slower. That would be useful evidence that the next boundary must be a genuinely bulk/native generic executor rather than another Python control-structure rewrite.

Another likely failure mode is high compile cost with small replay gain. Break-even is therefore reported rather than hidden.

A result is promotion-inadmissible if the matrix is incomplete, output semantics differ, work accounting differs, or exact-source CI binding is absent.