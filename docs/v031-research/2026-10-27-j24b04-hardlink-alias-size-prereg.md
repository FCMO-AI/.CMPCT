# J24B04 — Hardlink alias declared-length custody (prospective)

Date: 2026-10-27 UTC
Status: PREREGISTERED before instrumentation and result
Released authority: `FCMO-AI/.CMPCT main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, r24.
Related but independently owned: J24B01/B02 #604 and J24B03 #609 (direct S_BLOB regular/symlink), Reader composition #569. This lane is **research only**, no edits to any Reader, Builder, validation or owner branch.

## Question / prospective claim

Can a fully authenticated effective revision-24 index give a `K_HARDLINK` row a declared logical size different from the final regular-file owner, while released strict `preflight_archive`, full `CMPCT.read`, and `CMPCT.verify` all accept, and `read_range(alias, start, length)` uses the target size instead of its alias row? The Builder is expected to emit the same size for an actual inode alias; this is a structurally inconsistent but properly rehashed hostile index, **not** external signature forgery.

Strong simpler control: verify against one Builder-independent exact-wire direct RAW owner and a legitimate size-matched hardlink alias before mutating **only** the alias logical size. Unlike #609's direct S_BLOB file/symlink mismatch, the actual target/physical owner remains exactly valid. Controls use direct RAW and Zstd owner codecs when available. Full owner content, SHA-256, CRC32, primary/tail index consistency and footer integrity must be preserved.

Prospective predictions (to falsify, not assume):
1. Size-matched 128/128 hardlink: preflight, owner and alias read, verify, valid ranges all pass; bytes match owner, including empty EOF.
2. Signed alias sizes 136/128, 120/128 and 0/128: released preflight/read(alias)/verify all accept; read(alias) yields 128 bytes despite alias row claiming otherwise. A short declared alias may allow a logically out-of-alias-range query, because range forwarding precedes alias-row bounds. The owner path should remain valid.
3. The observed mismatch may also affect extracted filesystem sizes, but extraction should be classified separately and only on a safe temporary directory. Do not claim physical out-of-archive disclosure from an alias; underlying target's boundary still holds.
4. A negative control with a missing/cyclic hardlink target must be rejected by preflight, confirming the structural validator is active rather than generally bypassed.

## Kill/narrow conditions

A size-discordant alias rejected by strict preflight, read, verify or range before returning a contradictory result falsifies the corresponding prediction. A valid alias failing authenticity, a nonidentical owner/archive frame, an independently rejected receipt, or alias rules permitting intentionally different logical size by normative format make the defect claim narrower or invalid. No evaluator, fixture or threshold may be changed retroactively to rescue a prediction.

## Evidence ladder and cost

First rung: independent derivation from released `src/cmpct/reader.py` and `validation.py`; host actual installed-Reader same-wire positive and adversarial archives, with a second-root wire/receipt auditor. A full product implementation is *not* authorized by this experiment. Archive bytes are unchanged in product; instrument is research-only. A future guard should resolve effective owner once under hardlink-chain limits rather than rescan recursively for each alias; charge creation/open/read CPU, wall, memory and chains separately before promotion.

## Concurrency, scope and handoff

J24B03 #609 owns direct physical-blob equality for files and symlinks. J24C02 #569 owns Reader composition. The new narrow question is **hardlink alias metadata versus ultimate owner**, not the same direct S_BLOB repair; do not write into their PR branches or claim their CI outcomes. After decisive evidence, preserve artifacts and communicate the result to the owner and issue #605. Discovery STATE is under #574, so no shared-state mutation.