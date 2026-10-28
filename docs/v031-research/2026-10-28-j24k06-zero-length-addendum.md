# J24K06b — zero-byte selective request must not regenerate Deflate

**Prospective addendum, 2026-10-28 UTC.** Parent J24K06 candidate mechanism already restores correct nonempty suffix offsets, as demonstrated by first exact-hosted three-platform court #40630071575. Before further change, inspect `CMPCT.read_range()`: unlike other storage modes, S_VZIP delegates an in-bounds `length=0` request to `range_vzip`, which currently reaches already-skipped mode2 streams and regenerates their payloads even though no bytes are requested.

## Distinct falsifiable question

Can zero-byte ranges short-circuit immediately *after existing signed logical range bounds*, without decoding any skeleton or regenerated Deflate, while preserving the caller's range-validation semantics? Strong simpler control is a single early return in `range_vzip`; no recipe or Reader changes.

### Prediction

- For arbitrary valid recipes, `range_vzip(..., start, 0)` returns `b''` for `0 <= start <= recipe.total` with **zero calls** to content or stream providers, including a suffix after 2 MiB of regenerated streams.
- Out-of-bounds `start`, negative length, and a zero-byte request beyond `recipe.total` still raise exactly as before.
- No change to any nonempty read, including J24C07c's 130→131 signed wrong-byte falsifier. Original 3-host court must remain green.
- Keep the original source-parent custody distinction explicit: J24K06b may add only the exact early-return line to `range_vzip` in addition to J24K06's already-frozen bounded stream check; no Reader, validator or freeze tests are modified.

### Resource/negative interpretation

This is a resource-bound correctness improvement for empty requests, not compression size or full Reader speed. If any valid range semantics require physical integrity verification for an empty result, preserve and disclose that conflict; do not relabel returned no bytes as authenticated content. The resulting implementation must still fail closed on nonempty contradictory stream offsets. No full-product performance credit.

### Cheapest decisive instrument

Extend standalone two-stream independent oracle to explicitly count zero provider calls and rejected out-of-bounds empty requests. The scientific court uses the installed wheel, frozen adversarial test and other inherited conformance in Linux/macOS/Windows. Preserve exact source substitution proof and signed original failure's historical baseline.
