# O202b superseding preregistration — root-revision-normalized sparse ABI court (2026-10-26)

## Trigger and preserved previous hypothesis
O202a prereg at `5a594f4986cad99955deacab6d03fdec1a2186f9` predicted the original O198/#532 valid length-4 wire would open in the native C ABI. Before any hosted result, source review revealed a **material omitted schema field**: O198 `wire_archive()` constructs a root map with `files, blobs, recipes, dict_blob, fsmeta` but **without `v`**. Native Rust `parse_entries` calls `map_field(index, "v")`; Python `validation._validate_index` also requires `index["v"] == 24`. Ordinary Python Reader does not reject the missing root version. Hence native rejection of unmodified O198 wires cannot be attributed to sparse geometry. **Do not rewrite O202a predictions; preserve the original wire and its failure as a negative/inconclusive control.**

## Materially changed question
If every O198 archive is reconstructed into a **new revision-24-consistent root index with one additional `v: 24` field, reserialized and reauthenticated**, do the three genuine, independently executed surfaces then differ on geometry?

* Ordinary installed Python `CMPCT`: should accept valid and malformed geometries, reproducing the selective-byte discrepancy on length 1/2.
* Installed Python `preflight_archive` with full header checks: should accept length 4 and reject lengths 1, 2 and 5 as malformed geometry. This is a previously existing independently maintained Python validator, not a proposed new algorithm.
* Compiled Rust native C ABI: should accept length 4, return exact `CD`, and reject lengths 1, 2, 5 with typed `FORMAT (-3)`, reflecting existing `stored == declared` semantic admission.

The new archive has a **different SHA and binary identity** from O198; never present it as the same transferred bytes. Its logical content, physical RAW record, extent lengths, logical SHA and declared storage kinds remain unchanged. The only new input fact is authenticated root `v:24`. Retain the four original O198 byte hashes in the new result for causal comparison; do not delete or weaken the O202a court.

## Preregistered outcome classification
1. If normalized valid length-4 fails any of Python ordinary, Python preflight or native ABI, the fork is inconclusive. Investigate ABI/schema cause without changing success gates.
2. If the normalized valid case passes, normal Python accepts the malformed variants, and preflight/native both reject them, then the root cause is **an ordinary-open admission gap versus existing strict validator/native**, not an absence of validation machinery.
3. If preflight/native accepts malformed, preserve the negative and narrow the proposed repair; an untested source pattern is not runtime proof.
4. If O198 originals fail strict validation solely from missing `v`, state that their `authentic` qualification requires narrowing; independent corrected root-level archives restore a meaningful format-contract test.

## Reversible smallest intervention
Add a pure research-only `with_version_root(original_bytes)` transformer that decodes only the original authenticated primary index, asserts absence of `v`, inserts `v=24`, reserializes authenticated primary/tail indexes and updates the footer with an unchanged physical RAW blob record. Do **not** edit O198 harness, product, native, validators, frozen tests, thresholds, format, or release law. Use the same pre-existing native-build and source custody workflow; record both source SHA and raw per-case outcomes. Native Rust and Python validation are independent controls of ordinary Reader behavior, not two performance experiments.

## Decision leverage
If confirmed, issue #533 can prioritize **reusing the already existing validation contract at a bounded Reader admission boundary** rather than reinventing geometry logic or repeating 4-byte falsifiers. Full-product CPU/RSS and compatibility still require measurements. A preflight call is not automatically safe to insert wholesale at open: full graph/header checks cost I/O and may interact with recovery. Scope only to bounded index geometry after proof.

**Supersedes only the O202a experimental prediction about native opening the original field-incomplete wire; never erases that input or its evidence.**
