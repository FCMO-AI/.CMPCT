# J24K01 — Authenticated PACK selective-read structural inconsistency: confirmed

Date: 2026-10-27 UTC
Scope: **scientific/source-exact product defect reproduction**, not a repaired or released product.
Status: **FALSIFIER POSITIVE — NARROW THE PYTHON PACK RANGE GEOMETRY, NO MERGE/RELEASE**.

## Prospective source and proof

Preregistration **before instrumentation**: `bce446913564b691cb46b723ede9835df06b13d6`.
Parent immutable PR #314: `4c76440be1a84b60e574d602617740b70025df47`.
Shipping Python Reader Git blob: `e716233403dabd0966863c45635e18fa5ac6afb8` (unchanged from released v0.30.0/r24).
Immutable Builder-independent goldens: #307, `tests/conformance/v24-pack.json`, RAW and Zstd physical owners.
Experiment-bearing HEAD: `c71e712daa4de458c9fcc16d3b2067f8b98ef2a2`.

**Hosted exact-source scientific court:** https://github.com/FCMO-AI/.CMPCT/actions/runs/40510758334 — SUCCESS (Ubuntu 24.04 / Python 3.11).
Original hosted artifact ID `12737351239`, workflow SHA-256 ZIP `9f8e2818f5812b4fa6cec2bbcb88a63c2ebdeb1e72642443c60434228e8f9b7d`.
Original court JSON SHA-256 `db9f894a942267ed5c798ebce8a57c48dac6b666d03930b9428b32761f9829c7`.

The instrument executes the **actual installed CMPCT Python Reader**, not a mimicked slice, on immutable signed original and six new **internally authenticated** mutated revision-24 archives. Mutation recalculates primary and footer MessagePack/Zstd/index SHA and leaves the entire physical owner, CRC and physical SHA byte-identical. This does not claim an external signing authority.

## Observation / decision

| Independent physical PACK | Forged index tuple | Strict Python preflight | Full `read(omega.bin)` | `read_range(0,size)` |
|---|---|---|---|---|
| RAW owner | declared slice length `size+1` | REJECT | REJECT | **ACCEPT, full correct `size` bytes** |
| RAW owner | offset `owner_length-size+1` | REJECT | REJECT | **ACCEPT, `size-1` bytes** |
| RAW owner | offset `2^64-1` | REJECT | REJECT | **ACCEPT, empty bytes** |
| Zstd owner | declared slice length `size+1` | REJECT | REJECT | **ACCEPT, full correct `size` bytes** |
| Zstd owner | offset `owner_length-size+1` | REJECT | REJECT | **ACCEPT, `size-1` bytes** |
| Zstd owner | offset `2^64-1` | REJECT | REJECT | **ACCEPT, empty bytes** |

All positive original archives pass 4/4 full/read_range/verify checks and preflight. No input CRC corruption or index SHA mismatch explains the result.

The **independent wire/receipt referee** re-decodes both authenticated indexes, verifies original/archive SHA, checks physical bytes and CRC/SHA remain identical, reconstructs precise expected slice semantics, and validates the reported outcomes without importing the CMPCT Reader or its validator: **186 checks PASS**, plus **7/7 deliberate falsified receipts rejected**. This is independent receipt validation, **not an independent second Reader implementation or a cross-host reproduction**.

## Causal interpretation

`CMPCT.read_range` checks only logical request bounds, then executes `pack[base+start:base+end]` with no assertion on signed PACK tuple length or physical extent. Python silently clamps slices beyond EOF, so a `size`-byte range can yield shorter data while appearing successful. `preflight_archive` already applies the stronger `off + length <= owner_size` and `length == logical_size` constraints. The native parser's authenticated hostile index court in PR #314 already rejects analogous tuples at open.

A full `read` is not a complete universal guard either: it checks the returned length and is enough for the three mutations investigated, but should not be used as substitute for structural validation in every potential geometry collision.

## Strongest negative / excluded claims

- Invalid indexes are **internally self-authenticated**, not signed by a trusted publisher. This is a hostile-input structural consistency defect, not a forged cryptographic signature.
- These malformed archives already fail strict Python preflight and native open. Explicit preflight before ordinary read can contain this class; default Python Reader does not invoke it automatically.
- The 6 cases are deliberately bounded and do not establish real-world exploit frequency, arbitrary memory access, remote code execution or lossless reconstruction of well-formed archives failing.
- A green scientific job does not mean the original product is repaired; no Reader or native product source changed in this scientific PR.
- No CPU/wall/RSS/size/read-amplification benchmark or portability gate has been performed for a repair.
- Separate inherited CI workflow red (topology unknown `scientific` lane; Engineering Evidence missing exact required section) were presentation/process failures and subsequently repaired **without modifying the scientific oracle or its predictions**. Their updated-head statuses are separate.

## Cheapest next owner action

A small O(1) selected PACK geometry validator may enforce `len(storage)==4`, exact integral nonnegative owner ID/offset/length, `length==logical_size`, and `offset + length <= indexed owner usize` **before** ordinary selected decode; then demand exact return length, full and partial read equivalence, strong corrupted-mutant rejection, no new format bytes and bounded per-range CPU cost. Alternatively, enforce a single shared admission invariant at Reader open if whole-index overhead is measured favorable. Choose with Reader #569 and conformance #314 owners; do not duplicate their branches.

No discovery-policy change or stale mutable `docs/discovery/STATE.json` write is justified. Counterfactual transferable rule: **where strict preflight has structural validation, test ordinary selective paths against fully reauthenticated invalid metadata at exactly the same key-level contract**; unchanged physical bytes eliminate generic checksum explanations.
