# J24G46-A — prospective stronger discriminator: journal positional metadata reindexing

Date: 2026-10-29 UTC. Additional question frozen after review of `transactions.py` and `reader._index_from_footer()`, **before executing an experiment**. This adds to, never revises, the earlier J24G46 preregistration.

## Causal suspicion
The authenticated revision-24 `fsmeta.xattrs` and `owner_overrides` are keyed by the **ordinal index in sorted `files`**. When a committed journal delta inserts `a-new.txt` before `z-owner.bin`, `_index_from_footer` sorts `files` without visibly remapping those positional metadata tables. If true, strong `CMPCT.verify()` can still return success while xattrs attach to the wrong logical pathname. `compact_archive()` then turns that logical metadata identity error into a new physical artifact, possibly permanently losing or misattributing source metadata.

## Exact source
Source base is #757 `911e66053bd997ad0c85895cf61da02f9ce06625`, carrying ordinary Darwin native xattr support plus #428 O72. `src/cmpct/transactions.py` is inherited unmodified from released main; `src/cmpct/reader.py` is inherited apart from #757/O72 native xattr portability. Never imply this is a #757-induced defect.

## Stronger controls / prediction
1. Build a genuine Builder r24 archive containing lexically late `z-owner.bin` with **native** binary and empty-valued attributes. Prove native OS source values independently.
2. Control: append-update an existing member `z-owner.bin` (order unchanged). Predict metadata remains attached to `z-owner.bin` after replay and compaction, unless `append_update` itself changes captured metadata.
3. Challenge: append an independent new member `a-inserted.txt` so sorting shifts `z-owner.bin` from index 0 to index 1. Predict if suspected failure is real: `CMPCT.verify()` still accepts both contents but after replay `fsmeta.xattrs[0]` becomes associated with `a-inserted.txt`, and `z-owner.bin` no longer has its attribute. Strict extraction may misapply attribute to `a-inserted.txt`; after compaction that misassignment can persist.
4. Structural control: directory and non-xattr member sha+path remain authentic; no release/magic/format mutation.
5. Negative neutral control: Windows lacks a native POSIX-xattr admission path; show ordinary update/canonical data correctness, but Windows cannot certify the xattr proof.

## Falsifiers / alternative explanations
- If `fsmeta` is remapped internally on replay, both original and inserted members retain correct pathname-bound metadata: hypothesis FALSE.
- If native source xattr admission fails, this is an OS-fixture failure, **not** a CMPCT pass/fail.
- If the metadata is absent already in the Builder archive, attribute source/capture fidelity to #757/O72, not journal indexing.
- If the new file appears before `z-owner.bin` but `verify()` fails for content, keep that separate negative and do not claim the precise metadata-only bypass.
- If an earlier existing owner already fixed this exact positional table, reuse that owner. GitHub PR search for `fsmeta append`, `journal xattr row index`, `metadata update index shift`, `journal metadata remap` returned no narrow owner as of 16:20 UTC, though #247/#289/#732 cover adjacent journal safety and ZIP transfer.

## Information value and scope
This is a cheap exact-source real-archive O0 falsifier with strong independent OS and logical metadata oracles. It could expose a **general identity/metadata corruption** not limited to macOS, so the test should use Linux as an independent positive and macOS as target. No product repair, release or discovery policy change is authorized by an oracle alone. If reproduced, preserve evidence, notify relevant Writer/Reader/metadata owners and choose a bounded generic Reader/Writer repair under a new claim rather than another platform-specific workaround.
