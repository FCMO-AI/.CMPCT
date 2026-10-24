# O7 prospective court — public-C consumer end-to-end grouped extraction, not micro ABI

This preregistration is frozen **before introducing any consumer or performance test**. Base is PR #326 exact SHA `43ba79f9b9395af22a0f408de565704c268a4758`, stacked on native PACK batch #322, owner-discovery #325, authenticated index hardening #316/#321/#324. No shipping C platform handler yet.

## Primary productization question
Can a C program using **only public header ABI** enumerate a mixed real revision-24 archive, group eligible members by intra-handle physical-owner equality, read a whole group with verified native `cmpct_pack_read_batch`, reconstruct the exact original filesystem payload bytes, and preserve serial fallback for nonpack/RAW/singletons — with a material full-operation wall/CPU win over the identical C program running one `cmpct_entry_read_range` per member?

## Predicted result before observing
For a reproducibly built ~512-file structured source plus a high-entropy 70-KiB nonpack file, group API should recover two independent Zstd PACKs and one ordinary file. Both C modes must reconstruct the identical tree and SHA identities on every run; both use the same source archive and native package. For sufficiently large, shared-pack-heavy group, grouped mode should be materially faster with CPU savings after charging discovery, C process startup, file writes, and output tree materialization. The operation must never use Python private index metadata. Prediction may fail or become ambiguous because filesystem I/O, process startup or grouping overhead can mask the ABI-only gain.

## Controls and strong alternatives
- Baseline C program: per-entry independent authenticated read (strong same-output control); no Python-specific fast path.
- Candidate: query native `cmpct_entry_pack_owner`, group 2+ bounded Zstd owners and invoke native `cmpct_pack_read_batch` once per compatible group. Singletons and unsupported files retain baseline.
- Frozen same-input Builder archive built once (no random bytes per arm). Verify exact output bytes/path tree against independent original files after every run.
- Seven ABBA alternated paired repetitions, capturing raw wall and child CPU where available; report losing singleton regime separately. Include C consumer startup overhead in both arms and extraction file writes, not just ABI loop.
- Record process peak RSS if available, total output bytes, compressed source archive bytes, physically eligible group sizes, actual batch count, fallback count.
- Hostile regression is inherited owner court: signed duplicate map archives rejected on open; source corruption rejected by batch; no bypass of physical verification.
- Never grant release credit or infer universal extraction win from one synthetic favorable cohort.

## Disproof
Any tree/bytes mismatch, invalid-path write, grouped mode silently accepts nonpack, mutable payload corruption bypass, or skipped original regression gate blocks candidate. If all costs are paid and grouped performance is not materially better or memory amplification too high, narrow to API-only optional capability. Any ABBA input variation or source SHA mismatch invalidates comparisons.

## Portability, custody, concurrency
C test executable and Python harness are evidence tools, not production platform integration; no new Reader/Builder/format/version code. C consumer must compile public `cmpct.h` and link exact built Rust native library. This prospective lane is **independent evidence/productization** on top of #326, does not overwrite #322/#324/#325 owners. Do not silently weaken CI or change frozen comparators; no Discovery Engine STATE update.
