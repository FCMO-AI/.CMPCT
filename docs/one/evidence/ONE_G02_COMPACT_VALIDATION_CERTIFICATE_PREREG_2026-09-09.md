# ONE-G0.2 — compact reusable validation certificate preregistration

Date: 2026-09-09  
Branch: `research/cmpct1`  
Experimental version: `ONE-G0.2`  
Status: preregistered before result-bearing implementation

## Mission Lock / Referee

### Observed cost owner

Reusable `ValidatedProgram` moves full-Program validation out of repeated selective requests, but its retained `_Preflight.lengths` is currently a Python tuple containing one Python integer per stored node. That is semantically correct and fast to index, but its physical resident state can be several times larger than the information it carries.

The validation certificate logically needs one bounded output length per node plus `max_depth` and `worst_work_bytes`. Node lengths are non-negative and already bounded by `Program.limits.max_output_bytes`; the current representation should therefore be challenged as implementation overhead, not treated as architectural necessity.

### Hard invariants

This experiment may change only the in-memory representation of already-proven node lengths after a complete immutable Program snapshot has passed ordinary `validate_shape()` and `_preflight()`.

It may not:

- skip or weaken full stored-Program validation;
- alter any ONE wire byte, opcode, root identity or authentication rule;
- make validation authority caller-mutable;
- change declared resource limits or unsupported-topology behavior;
- infer node lengths lazily from only a requested cone;
- hide one-time packing CPU or retained bytes from accounting.

### Hypothesis

Packing validated node lengths into an immutable little-endian uint64 byte table can reduce retained certificate memory toward the information-theoretic 8 bytes/node model while preserving exact range semantics and keeping per-request indexed length access within a small CPU premium.

### Candidate

Add a research-only compact validation constructor that:

1. creates the same immutable Program snapshot as `validate_program_snapshot()`;
2. runs the same ordinary full shape validation and `_preflight()` once;
3. converts only the returned node-length tuple into one immutable packed uint64 table;
4. preserves `max_depth` and `worst_work_bytes` exactly;
5. returns the existing sealed `ValidatedProgram` authority so all optimized readers consume the same capability type.

The ordinary constructor remains unchanged as the incumbent.

### Frozen matrix

Program family: fixed 128 KiB add8 and XOR roots with unrelated valid Surprise nodes appended.  
Unrelated-node counts: `0, 64, 256, 1024, 4096`.  
Selective request: first 4 KiB of `current`.  
Timing: 15 warmed CPU measurements per per-request range-reconstruction cell after both validation authorities have been created.

Measure separately:

- incumbent validation/open CPU;
- compact validation/open CPU including pack construction;
- incumbent retained Python preflight bytes;
- compact retained Python preflight bytes;
- modeled certificate bytes;
- generic range-read CPU from each authority;
- exact output parity;
- certificate entry parity and scalar parity.

### Frozen gates

Required for `ADVANCE_COMPACT_VALIDATION_CERTIFICATE`:

- exact semantic parity on every row;
- compact certificate cannot be mutated through its public API;
- retained compact certificate bytes <= 0.40x incumbent retained Python preflight bytes at 4096 unrelated nodes for both Law families;
- compact retained bytes <= 12 bytes per preflight entry + 256 bytes at every row;
- median compact/incumbent per-request range CPU <= 1.15x;
- worst compact/incumbent per-request range CPU <= 1.30x;
- compact validation/open CPU <= 1.25x incumbent median across the matrix;
- no format, integrity, resource-limit or unsupported-topology weakening.

If memory passes but request CPU fails, retain a `HOLD` and localize whether unpack/index overhead is the owner. Do not weaken the CPU gate to rescue the memory result.

### Disproof

Retire this packed-table shape if it cannot produce a material retained-memory reduction without exporting more than the frozen CPU budget into repeated selective reads. A lower-memory certificate that materially slows every cone lookup is not a systems win.

## Hostile-review focus

The most dangerous false win is claiming compact state while keeping the original Python integer tuple reachable anywhere in the authority. The candidate must own only the packed lengths plus the two scalar preflight values after construction; the temporary ordinary `_preflight()` object may exist during open but must not be retained by the compact authority.