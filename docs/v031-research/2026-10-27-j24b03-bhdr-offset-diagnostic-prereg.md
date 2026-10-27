# J24B03-H2 — independent byte-custody differential after H's frozen false prediction

Date: 2026-10-27 UTC. **PROSPECTIVE** diagnostic extension on #609. This document is committed *before* H2's instrument/workflow/observations. It does not supersede or edit original J24B03, J24B03-H, H's failed original assertion, original source, benchmark thresholds or release law.

## Problem and strongest current evidence

The original three-host J24B03 24-wire source-exact court passed on guarded Reader `f9e95633db832b6c2ab95de8d7aaaf80c4b3ece8`. Its supplemental H court ([Actions #40554574952](https://github.com/FCMO-AI/.CMPCT/actions/runs/40554574952)) failed *before* candidate hostile-field observation: it predicted the released RAW read would return the **same original bytes** for all five corrupt header fields. That was false. Static source derivation suggests changed `BHDR.rml` shifts the payload offset from `pos+BHDR.size` to `pos+BHDR.size+1`; per-fault observed output has not yet been acquired. Preserve that original negative rather than rewriting its expected output.

An independent performance rung J24B03-P ([Actions #40555542073](https://github.com/FCMO-AI/.CMPCT/actions/runs/40555542073)) separately reports 36 source-exact subprocess observations and referee PASS. Its raw candidate/base per-call wall ratio is 1.3794 (+135.47 ns), CPU ratio 1.3794 (+135.46 ns); **the preregistered combined 500 ns absolute veto did not fire**. This is not zero cost or release parity. Future H2 work must not adjust that threshold.

## One primary scientific question

For ten **identical** authenticated-index revision-24 images (`K_FILE`/`K_SYMLINK` × RAW BHDR magic, codec, usize, csize, rml faults), what *actually* happens to the released Reader's selected eight bytes, and does the guarded candidate reject **all ten** without corrupting the two valid controls? In particular, does a one-byte metadata-length lie shift the historical mmap slice by one byte despite a fully intact signed index?

The comparator is the frozen released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, not a simulated raw-array slice. Guarded comparison uses exact #609 reader source, separate packages/native deps and identical archived wire bytes. Preserve original H's failed preregistration.

## Predicted discrimination and alternatives

* Expected from reading the actual historical `reader.py`: `rml=1` returns original `PAYLOAD[8:16]` instead of `PAYLOAD[7:15]` on both kinds, while at least some other corrupted fields may still yield normal bytes. This is a **prospective H2 prediction**, not observed truth. If it fails, record raw output without rewriting it.
* Candidate `read_range(name,7,8)` should reject all ten corruptions; the valid controls return exactly `PAYLOAD[7:15]`.
* Stronger alternatives: an early BHDR decoder exception or an unrelated file framing effect could explain an observed historical rejection; a completely broken constructor could trivially reject every corrupt case *and* all valid controls. Capture both.
* Compare named, independently reconstructed physical archive bytes: same pair SHA, same unchanged primary/tail authenticated logical index and only one intended physical BHDR field differing from the immutable valid image.

## Kill / narrow

Candidate ACCEPT on **any** corrupt BHDR (even changed bytes) falsifies this candidate coverage. A valid control REJECT or incorrect contents invalidates the test/candidate. An unchanged signed logical index, intact physical payload and same-wire pairing are required for a scientific decision. If the baseline rejects all corrupt controls, there is no historical fast-path gap (not a success claimed for the candidate). If `rml=1` does not shift exactly one byte, reject the H2 mechanistic prediction while preserving whatever output is observed. Independent stdlib referee must recompute all archive SHA, physical header deltas, expected payload offsets and per-fault receipts without importing the project.

## Evidence rung / product limits

Use one bounded three-platform (Ubuntu/macOS/Windows, Python 3.11) instrument, source-exact historical-vs-candidate branches, 10 corrupt archives + 2 valid-control archives, and independent stdlib referee. Preserve original JSON receipts, wire images and exact source HEAD/blob identities; ensure process exit captures do not truncate the first failure. No reread of mutable source, no weakening `verify`/preflight or format semantics, no new codec or reader optimization.

H2 is **hostile-frame science only**. It cannot earn full reader correctness, throughput, memory, release parity, hardlink or transactional extraction credit. Read the separate J24B03-P run receipt for absolute cost. No changes to Discovery policy or `STATE.json` (PR #574 independently owns its reconciliation). Never merge or release based on this isolated court.

## Concurrency / handoff

Continue only the already owned isolated #609 branch. J24B04 hardlink alias research is #610's separate owner; Reader composition and its 27–28× many-chunk cold-open debt remain #569. If H2 is decisive, update a small append-only result document and PR description with the source-locked receipt link, and alert #569.