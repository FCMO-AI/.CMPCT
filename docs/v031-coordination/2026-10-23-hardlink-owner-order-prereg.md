# v0.31 — Hardlink owner traversal/order falsifier (PREREGISTRATION)

Source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, revision 24; code is not to be edited for this court.

## Narrow scientific question

Can a Builder-emitted valid hardlink tree fail `CMPCT.extractall()` solely because depth-first `os.scandir` selects the original inode owner in one order, then `self.files.sort(key=lambda x: x[0])` publishes hardlink aliases before their owners in a different order?

## Prospective prediction

Use real POSIX hardlinks. Make `a/owner.bin` the first inode discovered while walking directory `a` before adjacent root-level aliases. The published byte-string lexical order places `a!.bin`, `a-.bin`, `a..bin` *before* `a/owner.bin` because `!`, `-`, `.` compare below `/`. A valid owner under `a` and alias `a0.bin` or `z.bin` should extract correctly. Three hostile and two controls, each from an independently built complete archive; verify full archive and read alias first.

The original Reader is predicted to reject all three hostile cases with `hardlink target not yet extracted` despite original source and archive being valid, and accept both controls. Reordering only the in-memory `reader.files` so owner `K_FILE` entries precede `K_HARDLINK` should make all three hostile cases reconstruct with matching inode identity and exact bytes *without changing archive bytes*.

## Independent controls, decision and attribution

Measure Builder-produced index order, literal hardlink target, `CMPCT.verify()`, `preflight_archive()`, actual extracted bytes, and POSIX inode equality. A hostile case that passes original extraction falsifies the bug as claimed; a control that fails likewise invalidates causal attribution. Successful in-memory dependency-first extraction with identical archive proves extraction scheduling is sufficient for the flat ownership shape; it is **not** a product fix or general proof for hand-built chained hardlinks.

No format, evaluator, threshold, recovery law, release lock, test fixture or product module changes. This is a research-only reproduction. Productization would have to preserve existing index bytes, account for hardlink graph depth/cycles, destination confinement and metadata, recovery, and measured full-product costs. Nearby hardlink branches inspected at orientation are identical to development; active PRs #241/#245/#247/#250 concern transactional hardlink ownership, not Builder-to-extractor ordering. Concurrency should be rechecked before any product write.

## Prohibitions

Do not weaken parser or change archive sorting to make the experiment pass. Do not infer product credit from a hosted scientific oracle. Keep a negative result even if surprising.