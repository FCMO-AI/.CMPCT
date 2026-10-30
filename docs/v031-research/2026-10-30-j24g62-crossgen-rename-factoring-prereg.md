# J24G62 — Cross-generation one-operation rename factoring, no-new-bytes oracle

Date: 2026-10-30 UTC. Status: **PREREGISTERED / NO RESULT**.
Source parent: J24G60 #800 at `fb5d96cdb8855fe3e01868792e65b79d3d61661d`, inheriting #795 at `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`.
This is an isolated *research tool*, not a modification of Reader/Writer/release.

## Problem and baseline
Physical J24G60 #800 measured a 2,048-file, 63-public-rename Reader-open overhead of 24.857 ms Ubuntu, 33.632 ms macOS, 54.303 ms Windows versus an additional exact-state checkpoint (+12,659 bytes / 4.3294%). J24G61 #801 attributes approximately 98% of the extra cost to per-generation replay on Ubuntu/Windows, with macOS **inconclusive** under the predeclared perturbation limit. J24G58 #797's within-one-generation >=16-op optimization cannot run on ordinary one-operation Writer deltas.

## Primary falsifiable question
Can a series of *actual r24 one-op rename generations* be factored into a **single bounded path-identity map** with no additional archive bytes, retaining full source-index, signed operation, metadata, footer and final logical state semantics, and showing >=3x *replay-only* speedup for N=2,048, depth=63 with no more than 2 MiB additional peak traced Python allocation?

## Mechanism and alternate hypotheses
For a checkpoint and chronologically verified sequence of one-op renames, validate the complete operation grammar first, then use one path→row map and one final sort instead of regenerating an N-row lineage/sort at each generation. Preserve path identity across renames. A fast-path is admitted only for distinct logical names, exactly one admissible rename per generation, valid no-collision transfers, and **no sparse positional fsmeta records**; any other history uses the original, byte-identical #795 helper. The base index's common owner remains unchanged. Signed xattrs/owner override cases must fail open to fallback *without touching the base index*. This is a deliberately narrow oracle; no claim of general mixed-operation or metadata-rich acceleration.

**Strong simpler control:** #795 helper applied once per genuine decoded generation to the same base index; alternate execution order to limit systematic runner effects. The source-exact #800 chain and checkpoint are separate controls. Alternative explanations: Python object identity/mutation or deepcopy timing, physical footer decoding rather than helper, aliasing a row from one candidate into the other, metadata omission, or conflating imported-process overhead with replay cost.

## Evidence and kill conditions
1. Use the genuine Builder→public Writer 63-step chain and independently SHA-checked r24 footer ancestry. Extract the exact checkpoint and all chronologically ordered committed deltas from physical wire; compare original-helper and one-pass-factored final full MessagePack/JSON index equality, Reader index equality, strong verify/preflight, and original physical archive SHA.
2. Adversarial deterministic set: valid rename chains, no-op/nonexistent old path, repeated rename, rename collision, mixed put/delete, malformed operation, duplicate base name, xattrs, owner overrides, invalid ordinal. Every rejected fast-path must fall back to the original and match outcome or original exception; no mutation of the caller's input on ineligible trials.
3. Benchmark replay-only with at least 7 alternate A/B observations, process CPU/wall and tracemalloc. Report absolute deltas, speed ratios, allocations, coverage and raw samples. Host benchmark is not archive open or disk-cold latency. If <3x or >2 MiB traced additional peak, the constrained mechanism does not earn priority. A fast case that fails identity/parity or falsely admits metadata/collision is a hard falsifier, regardless of speed.
4. Any original physical footer, source Git blob, semantic recovery, checksum, or case identity mismatch is an invalid court. If CI unavailable, preserve local oracle and classify it *unmeasured for product*.

## Safety, resource and portability
Do not modify `src/`, Writer, Reader, native code, published r24 format, old v0.30 manifests, benchmarks, comparators, thresholds, or `docs/discovery/STATE.json`. No new archive bytes are emitted. The claimed no-extra-bytes property is **research algorithm only**; memory/time/maintenance costs remain charged. Experimental fallbacks do not excuse lack of Reader integration, unsafe corrupt footer recovery, multi-gen mixed operations, metadata physical correctness, xattrs/hardlink collisions, native cross-platform conformance or release parity.

## Concurrency and claim
#795 owns shared replay product semantics; #797 owns within-generation indexed helper; #800 owns same-state physical checkpoint; #801 owns observed attribution; #574 owns shared discovery state. J24G62 owns only the **renames-only across-generation factoring oracle**. Do not merge, copy implementation into product or overwrite their work without fresh reconciliation. If a near-identical independent PR appears, prefer evidence sharing and close this narrow duplicate.

## Completion decision
Positive lower-rung evidence would justify a new owner-aligned full mixed-op cross-generation replay architecture and actual Reader-open/product accounting, **not** release or performance promotion. A negative retires this factoring family under present constraints. Preserve all negatives and real source SHA/CI identity.
