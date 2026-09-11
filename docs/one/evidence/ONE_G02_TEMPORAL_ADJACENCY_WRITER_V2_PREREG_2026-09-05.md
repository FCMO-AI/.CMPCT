# ONE-G0.2 — temporal-adjacency writer integration v2 preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Status: frozen before result-bearing execution

## Mission lock

The original temporal-adjacency writer preregistration froze a deliberately narrow compiler boundary: exact `+1` shift structure could compile through existing generic ONE `surprise` + `concat` + ranged `Ref`, while damaged proof-led relations were to fall back to literal Surprise in this integration experiment. Hostile review found that `one_g02_temporal_adjacency_writer_integration.py` exceeded that boundary by compiling damaged `+1` relations into multiple ranged references plus Surprise islands.

No result from that harness is admissible as the frozen temporal-integration gate. This v2 preserves the original corpus, dispatcher choices, 31-round timing method, and timing thresholds, and changes only the implementation so it obeys the already-frozen compiler boundary.

## Falsifiable hypothesis

For adjacent versions already supplied as `(previous, current)`, the amortization-safe relation turnstile will preserve the exact baseline relation decision while reducing complete research-writer elapsed time enough to survive Program construction and wire encoding, without changing reader semantics or stored bytes for an equivalent decision.

Disproof is any classification mismatch, best-shift mismatch, reconstruction failure, wire mismatch for equal semantic decisions, stored-byte mismatch for equal semantic decisions, any size-class ratio above `1.03x`, or aggregate mixed-stream ratio above `0.92x`.

## Frozen inputs and timing

Unchanged from `ONE_G02_TEMPORAL_ADJACENCY_WRITER_PREREG_2026-09-05.md`:

- sizes: `4, 8, 16, 32, 64, 128, 256 KiB`;
- five deterministic transitions per size: exact `+1` shift, quarter damage, fragmentation every 96 bytes, mutation every 32 bytes / false-pattern control, independent random control;
- 31 interleaved baseline/candidate rounds;
- timing includes relation admission, exact proof when reached, Program construction, and ONE wire encoding;
- semantic decode/reconstruct verification remains outside the timed writer region and must be exact.

## Corrected compiler boundary

For both baseline and candidate:

1. if the dispatcher accepts best shift `+1` **and every target byte after the first obeys `target[i] == source[i-1]`**, compile through the existing generic ONE grammar;
2. otherwise emit the same literal-Surprise fallback for the current version, even when the proof-led dispatcher accepts a damaged relation;
3. no relation-specific reader opcode, hidden codec, extra discovery pass, or alternate fallback mechanism is permitted.

The corrected harness must explicitly count accepted-but-literal damaged relations so compiler debt is visible rather than accidentally converted into a density claim.

## Frozen gates

Advance only if all are true:

- exact relation classification and best shift match baseline on every row;
- every emitted program round-trips byte-exactly;
- equal semantic decision yields byte-identical wire between baseline and candidate;
- no stored-byte regression for an equal semantic decision;
- every size-class candidate/baseline elapsed ratio `<= 1.03`;
- aggregate mixed-stream candidate/baseline elapsed ratio `<= 0.92`;
- zero new persistent writer state and zero reader-visible operations.

No threshold, corpus member, or compiler rule may be changed after the result is observed.

## Claim boundary

A pass proves only an adjacent-version known-pair research-writer admission win under the current minimal compiler. It does not prove product speed, arbitrary resemblance discovery, full damaged-relation density capture, or superiority to v0.29/v0.30. A failure of timing preserves the previously proven turnstile micro-result but blocks promotion into this writer path.
