# O202 preregistration — native/Python sparse geometry admission differential (2026-10-26)

## Authority and scope
Canonical `FCMO-AI/.CMPCT`; released v0.30.0/r24; experimental Reader O193/#521 and O198 scientific source #532 at `16bfcf12adcb6cb1025896c4ece0f8aab7c79646`. This is **independent cross-implementation replication**, not another Python Reader fix. O198/#533 owns the existing defect, O201/#534 separately owns the S_CDC hypothesis, and O193/#521 owns the experimental product Reader. No writes to their branches or `docs/discovery/STATE.json`.

## Primary question and prospective prediction
Does the unmodified native Rust r24 C ABI reject the **same checksum-consistent S_SPARSE archive bytes** that the authentic Python Reader accepts and answers inconsistently, while accepting a valid fixed control?

Code-level prediction: native `parse_storage` sums referenced physical blob logical lengths and requires `stored == declared sparse extent length`, before publishing a native archive handle. The Python Reader accepts 1/2/5 declarations referencing one 4-byte RAW blob and in O198 returned `0000` for `read_range(2,2)` on declared lengths 1/2.

**Decisive intended matrix** using the existing O198 unmodified `wire_archive` function:
- length **4**: Python `verify==1`, `read==ABCD`, `read_range(2,2)==CD`; native `cmpct_open==OK` and `cmpct_entry_read_range(2,2)==CD`.
- lengths **1 and 2**: Python accepts and returns the previously observed wrong late bytes; native `cmpct_open==FORMAT` rather than return a handle. Any observed alternative must be reported without moving expectations.
- length **5**: Python accepts and reads whole logical `ABCD`; native `cmpct_open==FORMAT` because 5 != actual 4.

If native rejects the valid archive, parser/ABI/source-identity validation fails, results are inconclusive. If it **accepts** malformed cases, report a shared/independent native correctness gap, not a green outcome. If Python no longer reproduces O198 due to source drift, report drift and do not claim historical current-source parity.

## Stronger and cheaper controls
Static Rust code inspection supports but cannot prove actual installed C ABI behavior. Use O198's immutable 456-byte real-r24 wire construction rather than monkeypatching objects or building with the current Builder. Require independently installed Python package, pinned Cargo.lock/native release build, exact Git HEAD and source SHA, unchanged native/Reader product files, original compressed primary/tail index identities and O198 archive SHA. C ABI is invoked from Python `ctypes`, independently of Python's own r24 parser; no mock Rust parser or replacement evaluator. One Ubuntu runner is sufficient to answer the narrow language-contract fork; additional OSes only if behavior diverges or platform data matter.

## Alternative explanations and disproof
Check symbol/ABI correctness and valid positive controls before interpreting negative statuses. Catch source/library load failure separately from format rejection. A malformed archive's internally consistent SHA is not an external signature; authorship is adversarial. Refuse to infer that the production Builder emits these archives, that native is universally safe, or that 4-byte behavior generalizes to all representations. Do not equate `cmpct_open` refusal with successful whole-product release integration.

## Resource / release economics
Four tiny files, independent installed Reader and native compiled library; no compressed-size improvement; compiler/runner cost belongs to research infrastructure, not Reader runtime. A native open-time consistency check demonstrates one bounded design precedent, not an optimized Python implementation. Production fix must still measure index parsing CPU/RSS with large sparse tables, preserve valid Builder-produced archives and exact 4GiB ZIP64 behavior, and pass all release/conformance/security gates. Product/source/benchmark/format/validators untouched.

## BONK and handoff
Prior O198 already proves Python failure, so do not repeat it as a discovery. New evidence can decide whether **cross-language split** exists and whether the exact native parser is an implementable semantic control for #533. This is cheaper than writing yet another Reader fix and more reusable than threshold adjustments. Kill additional tests of this specific 4-byte family after one authenticated hosted differential unless an unexpected result changes the question. Retain independent owner lanes, including O201 CDC and J24F04 mutable mmap. Preserve negatives and link raw workflow receipts.

**Success is a decision-changing, exact-head, authentic on-wire Python/native differential, not simply a successful workflow header.**