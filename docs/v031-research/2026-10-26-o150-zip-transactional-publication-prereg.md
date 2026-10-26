# O150 — transactional ZIP export, preregistration

Date: 2026-10-26 UTC. Status: hypothesis frozen before product edit or result observation. Scientific/product-candidate only; no release authority.

## Exact inheritance and ownership

Canonical `main` v0.30.0, format r24. Candidate starts from ZIP export O140 [#488](https://github.com/FCMO-AI/.CMPCT/pull/488) commit `d8b69758dbcbb66fe28fa7cf59598916df160d2d`, Reader blob `e46e6121842d485cb209118576ebf3ba3719080d`. Inherits O135 own-source alias rejection and O140 nonregular destination rejection. O143 [#489](https://github.com/FCMO-AI/.CMPCT/pull/489) established two independently observed pre-existing regular-ZIP destruction modes on Ubuntu/macOS; its original defect-expecting tests must not be edited. O284 [#284](https://github.com/FCMO-AI/.CMPCT/pull/284) owns Deflate stream verification, not this new failure-atomic publication implementation. Source surface overlap is explicit: independent candidate only, handoff to owners rather than silently editing their branches.

## Primary scientific question

Can a bounded, same-directory staged ZIP materialization with a single final `os.replace` prevent **partial or emptied existing regular ZIP publication on normal read/CRC/late-member exceptions**, preserving genuine O140 source-inode and nonregular-leaf rejection and bit-exact successful ZIP export, without claiming power-loss or hostile concurrent namespace atomicity?

## Hypothesis, strong control, and disproof

- Baseline: O143's builder-independent r24 RAW CRC mutation leaves an original valid 190-byte target as zero bytes; separate genuine Builder two-member late corruption leaves a >30-byte invalid partial ZIP. O140 has no protection for existing regular ZIP destinations against late verification failures.
- Candidate: validate the publicly requested output's current static inode/type **before** staging; create a private regular sibling in the same directory; run the *unchanged* ZIP serializer against that private sibling; replace the requested output path **only after** serialization closes successfully; unlink stage on every caught exception. `os.replace` stays on one filesystem by sibling construction. This is the same general publication class used by the repository native portable CLI, but not its backup/rename sequence.
- Prediction: on both source-exact negative controls, `export_zip` still rejects corrupt CMPCT data, original valid ZIP SHA and decoded content remain unchanged, source CMPCT SHA remains unchanged, and no stage is left. Clean RAW, Zstd and direct-Deflate ZIP controls still decode exactly via independent `zipfile`.
- Independent negative controls: retain O143's original defect-expecting test untouched on its original historical Reader; run a **new** inverse-assertion positive court on the candidate, sourced from the frozen vector and original 2-member Builder experiment. A trusted regular existing target must not be modified on failure; a newly requested target must not be created on error.
- Disproof: any original target overwritten/truncated after error, wrong decoded ZIP after success, source alias/nonregular/FIFO unexpectedly allowed, stage leak, source SHA change, or materially excessive/unsafe temp/execution cost defeats promotion. A green science court alone cannot establish crash consistency, TOCTOU resistance, ZIP64 >4GiB, Windows handles, or release performance.
- Stronger control considered: preverify all members before opening destination, which can protect only read failures, doubles logical decode work, and does not cover mid-stream write failures. In-place restore-on-error is not atomic and may fail after partial writes. Stage-and-replace is the cheapest general positive semantic control for ordinary exceptions.

## Ownership and economics

Staging adds up to the entire output ZIP as temporary physical storage (O(output bytes)) and may incur additional writeback/page-cache work. It **changes pre-existing target inode/hardlink semantics**: a successful replace swaps the directory entry, while other hardlinks to the old ZIP retain old data. For a symlink-to-ordinary-output, the destination symlink itself can be replaced; the target is no longer overwritten. This is a real compatibility tradeoff and **must be made explicit**, not credited silently. We do not claim fsync or power-loss durability. Windows, adversarial concurrent swaps, distributed filesystems, output permissions/xattrs, update semantics and performance remain separate gates.

## Evidence ladder and bounded intent

First preserve prereg, then implement minimal stage boundary without changing inner ZIP serializer/comparator; add positive exact-source tests and raw SHA receipts; run locally where possible and a dedicated hosted Ubuntu/macOS court; leave CI identities and negative evidence. Full official ABBA and inherited host tests are required before product promotion. No version/format/benchmark/validator/release law changes. If staging fails cost/semantic obligations, retain only research evidence and hand off design alternatives to the original ZIP owners.
