# J24B03-H — Independent RAW BHDR field coverage (prospective)

Date: 2026-10-27 UTC. Supplemental hostile-read falsifier, preregistered **after** the already-completed J24B03 three-host verdict but **before** this separate instrument. No retrospective changes to the original 24-wire outcome or original referee.

## Question

Does the candidate RAW mmap fast path reject each physically corrupted BHDR geometry field individually, even when ordinary Reader construction still accepts the unchanged authenticated logical index? Test five orthogonal physical header changes: magic, codec, uncompressed size, compressed size and metadata length. Compare on identical archives with unchanged released `main@80c358f8824ec1b20d349c92ed94c898090969b0` and exact candidate, both `K_FILE` and `K_SYMLINK`. Expected: strict preflight rejects on both sources, historical `read_range(name,7,8)` still returns the original 8 payload bytes because it ignores physical header fields; candidate returns REJECT before slice. 10 cases per source; exact archive SHA equality across arms; no Builder fixture.

## Kill and limits

Any candidate ACCEPT on these 10 physical corruptions falsifies this extension. Any historical baseline REJECT invalidates the proposed historical contrast and must be reported, not silently removed. A valid same-wire RAW 128/128 control must continue succeeding on both. Do not weaken existing original court/referee to make this green. This probes metadata/frame discrepancy only: no promised per-range CRC or SHA, no byte mutation under a valid BHDR, no mutable input/TOCTOU, no complete hostile parser proof. No version/format/release changes.

If this supplemental test passes, report separately as additional hostile-field evidence only; product promotion still requires owner composition, complete gating and parity. No Discovery Engine policy or benchmark threshold changes.
