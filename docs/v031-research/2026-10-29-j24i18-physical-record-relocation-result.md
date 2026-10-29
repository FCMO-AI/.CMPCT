# J24I18/J24I18b — Physical-record relocation result, 2026-10-29 UTC

**Decision:** `REPRESENTATION_SEED_SURVIVED_LOWER_RUNG`; not a product candidate or secure compactor. The first all-indexed-blob mechanism is **size-negative**, the strict descriptor-closed pruning follow-on removes that measured debt on the tested physical archive and recovers exact Builder-output **size parity**. Original bytes and semantic identities are not conflated.

## Preregistration and exact provenance

- All-blob prior prediction: `c416cbe46489bfe2a32184367f7fc36cfde1fca4`.
- Follow-on live-blob closure prediction, written after the first negative and before implementation: `02536f73f50facf47b5bfe5763398d19bd6ced0d`.
- Released `main` base `80c358f8824ec1b20d349c92ed94c898090969b0`. Provisional #723/#728 original hosted physical artifacts; not an invented source dataset. #723 J24I06 original eight-case evidence is the principal baseline. Another nine authentic Ubuntu/macOS/Windows-origin source archives are from #728/J24I10; the transformation was run on Linux, not three hosts.
- Standalone tested local Python+msgpack+system libzstd implementation, with an independently rooted earlier #723/J24I06 parser as referee. Equivalent source is committed under `research/j24i18/`; hosted exact-source integration is adjudicated separately via `.github/workflows/v031-j24i18-physical-relay.yml`.

## Measured physical archive result

| Scenario | Original | All-blob relay | Live-blob relay | Existing Builder compaction |
|---|---:|---:|---:|---:|
| Genuine committed journal update | 1,382 B | **1,297 B** | **1,176 B** | **1,176 B** |
| Seven original single-checkpoint r24 archives | Identical | Identical | Identical | Identical |

The journal source SHA-256 is `e423777d4a6d668879bdd3c290d12aedc2a4bc4070ec8b325165e1c9d8de8471`. Its strict-relay output SHA-256 is `9e95d3c3ca00d7a2ca71a486c94e2a004903e5fa2f174118537e86b75c0b17ea`. The current live blob is old physical blob index 1; original index 0 is provably unreferenced and was deleted. The resulting archive differs bytewise from the Builder reference although it has exactly the same **1,176 B** length and externally parsed file/meta semantics; its live physical record is the **exact unchanged original compressed record**, whereas the Builder re-encodes it. No superior size, create speed, compression ratio or release credit is asserted.

Independent parser equivalence: **8/8** #723 source/relay/Builder triples match logical member bytes, kind/mode/mtime/owner/xattrs/hardlink target/symlink target. On **9/9** additional #728 original source files (three Linux, three macOS, three Windows), relay output is byte-identical to input and independently decodes the same logical metadata. These are 17 physical source/output semantic comparisons, **not** 17 distinct new compaction wins; 16 no-op checkpoints provide compatibility controls.

## Hostile counterexamples

A separate signed-index/physical-record mutation test rejected **13/13** bounded cases: content flip, BHDR SHA flip, physical length distortion, truncated record, out-of-range or boolean blob reference, virtual storage, unknown storage, absent dictionary, duplicate path, absent hardlink owner, hardlink cycle, and nonempty virtual recipe. A negative court does **not** prove complete hostile-archive safety. In particular, adversarial canonical path aliases, full virtual-container dependencies, source path rebinding, signed journal rollback and immutable-fd custody remain unresolved.

## Large logical sparse probe (synthetic, not installed product)

An r24-compatible metadata-only synthetic sparse variant with **134,217,731** logical bytes had **1,251** physical source/output bytes; a **4,294,967,299** logical-byte variant had **1,255** physical source/output bytes. No filesystem file tree or logical sparse holes were reconstructed by the prototype. A separate decoder fully materialized and verified the 128 MiB variant; the 4 GiB variant was authenticated only using streaming author SHA and exact structural index/record equivalence, **not** by an independent 4 GiB decode. Timing from this synthetic run cannot be treated as Builder-vs-Builder performance evidence. The container Python process has ~95 MiB baseline RSS even when doing no meaningful work, so its ~96.9 MiB VmHWM is not evidence of a measured 4 GiB product RSS win.

## Hosted CI execution truth and correction

Initial exact-head hosted job [#40840252999](https://github.com/FCMO-AI/.CMPCT/actions/runs/40840252999) **FAILED** on a **test harness** assumption: authentic installed Builder+append_update source exposed journal depth 2, while the test incorrectly assumed exactly 1. Crucially, the script had already generated a valid 1,313 B source and 1,118 B strict-relay candidate, one dead blob removed, and genuine Reader logical byte/metadata comparisons had passed before the mistaken depth assertion. Its `J24I18_RESULT` receipt was retained in the log. The artifact uploader separately failed because a workflow authoring escape introduced a literal backslash into a GitHub expression. Both issues were corrected prospectively in commits `5ea530f` and `a9e6179` without modifying the relay mechanism or weakening any content, integrity, type, hardlink or metadata assertion. A green re-run **must be measured**, never inferred from those repairs.

## Limitations, strongest self-critique, next discriminator

The current relay reads the **entire physical archive into memory**, and current independently authenticated blob decoding can materialize a large raw blob. This is not a bounded-memory compactor. A secure product would need source file-descriptor ownership across scan+verify+copy; streaming index and blob proof; authenticated complete reference closure for every representation and recipe/dictionary; no stale/unverified shared path; crash-safe publication in a pinned destination directory; genuine adversarial r24 chain recovery; and full filesystem metadata/reader verification on Ubuntu, macOS and Windows. #726/#740 stage authority and #738/#620 sparse alias ownership are independent existing owners and must be reconciled, not duplicated.

The prospective counterfactual discriminator that could have saved the first pass was *live-blob reachability before copying physical records*. That rule transfers to a future physical relay and has decision-changing evidence; it does not justify rewriting Discovery Engine policy or `docs/discovery/STATE.json`. The cheapest next independent test is a full installed CMPCT Reader/Builder check at exact-hosted HEAD followed by a source-FD-bound streaming version and real sparse alias memory/CPU equivalence.
