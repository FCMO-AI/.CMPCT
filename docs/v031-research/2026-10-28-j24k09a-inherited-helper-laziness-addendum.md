# J24K09a — Stand-alone helper scope and inherited laziness (post-prereg addendum)

Date: 2026-10-28 UTC.
Original immutable preregistration: `36c5950931cef292c7cc37602e62dcf7be2f44b0`.
Product source start: `113e569bbd48c15313ef726d4536f9c4e6a5edb2`.

## Discovered inherited contract before hosted verdict
An unmodified inherited J24K06 source test requires that a stand-alone `range_vzip(recipe,get_content,get_stream,...)` on an authentic retained/STORED valid suffix does **not** invoke the earlier stream decoder. Our first candidate replaced this with a safe-but-expensive decoding fallback even without the new metadata callback. That changes the inherited component's selective-work semantics and could export CPU/memory amplification.

## Reconciliation (not a changed experiment threshold)
Preserve the inherited stand-alone internal helper's no-callback selective laziness; do **not** award it a guarantee it does not provide. A public installed `CMPCT.read_range` now **always passes** a same-Reader physical-size callback, and its nonmode2 skipped streams are guarded without decoding. The scientific claim and six frozen signed archive mutations concern that installed Reader only. Mode2 remains independently guarded when the callback is absent or present. The inherited no-regeneration test remains unchanged.

The initially proposed "stand-alone safe decoding fallback" is **not** promoted. Treat this as a negative discovery about the helper API's missing physical metadata, not as an excuse to weaken an external evaluator. A future safe stand-alone explicit strict mode would need to receive a bound physical-size oracle or pay decoding cost and be separately reviewed.

## Required checks
- Keep original J24K06 no-regeneration test green.
- Preserve six J24K07 signed wrong-byte mutations, modified only in the new *candidate* test to expect rejection.
- Verify same-Reader callback truly runs; do not permit an alternate public range path without it.
- Report standalone helper without callback as legacy not independently authenticated.
- Source-custody guard must prove all other parent Reader/codec bytes unchanged.
