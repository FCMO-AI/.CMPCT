# J24G71 — Source-exact hardlink-owner guard composed with fail-closed signed r24 replay

**Pre-result preregistration — 2026-10-30 UTC.** No code/source test has been modified in this branch at this commit.

## Authority, actual owners and baseline
Released main remains v0.30.0 / r24. Candidate parent is #795 exact `1935c14c76f1bb39fd218d73cdbee93d3c2b76a1`, which owns Reader/preflight signed journal op/footer admission. Existing #241 at `4863ab3653e111b73ee6591f87a177f7919f25b1` already independently found and repaired the *Writer* hardlink-owner mutation defect, on older v0.31 development. Its Writer source Git blob is `129fd0f953c55e9094fd07a04677aca564c80d12`, and the tested guard has no change to r24 grammar. The candidate parent Writer blob is `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`. This is **source-exact composition/product convergence, not novel invention**, not an alternative implementation of #241.

## Primary question
Can the already proven bounded precommit hardlink-owner guard from #241 coexist with #795's shared semantic replay and footer admission, preserving authentic Builder hardlink inode identity and the source-exact inherited journal tests on Ubuntu, macOS and Windows, **without modifying any format bytes, journal grammar, preflight, Reader, or release evaluator**?

## Baseline failure and control
The unchanged #795 Writer permits `append_delete(owner)` / `append_rename(owner)` while a K_HARDLINK alias targets that owner, creating a valid-checksum committed journal with a dangling path. Issue #237 and #241 preserve direct prior reproduction. The strongest simpler control is the *exact already-tested* #241 guard, not a new lineaged algorithm. No alternate mechanism is invented here.

## Falsifiable predictions and kill conditions
Positive: copy only the #241 precommit guard into #795's Writer; independent tests build physical source hardlinks and require (1) both owner mutations raise before writing any archive byte; (2) unchanged SHA and whole archive bytes after refusal; (3) alias mutation and unrelated file mutation continue with signed Reader/preflight parity, extraction shares physical inode; (4) after deleting every dependent alias, owner mutation becomes admissible; (5) all inherited J24G55/J24G57 tests still pass. For signed journals, verify committed footer generation and full read after allowed mutations. Run exact-head original three-host CI with raw receipts and source attestation.

Kill/narrow if guard fails any of (1)-(5), alias graph changes, source bytes differ from Git, any host fails a required case, or a required inherited J24G57 correctness assertion changes. Preserve original #241 and #795 tests unchanged. Do not treat an inherited historical fingerprint/defect-red as a new failure or green promotion.

## Cost, alternative and release boundaries
The scan is O(file count), adds no archive bytes and no decoder-visible metadata; it deliberately refuses legitimate owner renames/deletes until atomic hardlink reparenting is proved. Whole-system CPU/RSS and large-`N` overhead are unmeasured at preregistration. An atomic owner-reparenting new opcode or Reader acceptance relaxation is higher risk and not authorized by this composition. Avoid merging across owner branches without review. No main merge, version/format bump, benchmark edit, public-site claim, or discovery cache mutation.

## Concurrency and evidence plan
#241 owns original Writer guard; #795 owns signed replay; #808/#810/#813 own cross-generation research; #574 owns discovery cache. Only this isolated #795 child owns their **composition**. Before late writes re-read exact heads and surface; preserve original donor bytes and parent source identity in durable Git history. Specialized host jobs are the cheapest decisive rung. Full official product performance and release gates remain mandatory and unmeasured; any performance claim from the specialized test is disallowed.
