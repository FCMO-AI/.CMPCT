# O1b preregistration: control native-provider parity for feed-boundary effects

Date 2026-10-23. PR #282, O1 source exact `f945f5ae5e1162afe913b12450900c5ec4ef76eb`, hosted run 40018627548, artifact 12528599787.

## Prior locked observation, not prospective
O1 exact-head 84 comparisons found 78 C-libz vs Python single-call byte identities and six mismatches, **all** on level-0 input-feed chunk sizes 1 or 4096 with shifted_related_64k, structured_logs and json_rows. Level 0 chunk 65536 and all 1/6/9 levels matched on the original seven sources. Neither source nor immutable anchor may be changed.

## New prospectively answerable fork
Were the six differences caused by **C-vs-Python provider/ABI behavior** or by the **different input-feed schedule** (C fed fixed small chunks while Python fed its entire input in one call)?

The cheapest strong control: retain C native output and compare it to a **new Python zlib.compressobj(-15)** fed in exactly the same 1/4096/65536 input chunks with Z_NO_FLUSH and one final Z_FINISH. On all 84 original input/level/chunk tuples:
- compare C against chunk-matched Python,
- compare both against existing all-at-once Python reference,
- independently inflate the streams to the same source,
- retain SHA-256 and first difference for all mismatches.

**Prediction:** C vs Python feed-matched streams will be equal on 84/84 in same hosted linked libz environment, while the six Python feed-matched vs Python single-call differences replicate the observed six C vs Python single-call differences. Any other result **falsifies a pure feed-boundary attribution** and requires investigating C/provider settings or out-buffer effects. Never change compression level/corpus or alter the fixed golden anchor to improve equality.

## Value of information / limits
A positive isolates algorithm provider identity from **streaming call-boundary dependency**, changes the proposed native parity contract and blocks a false streaming-byte-guarantee even with identical libz. The next possible product route could buffer enough bytes, reproduce exact feed policy, or retain mode 1; do NOT tune a chunk threshold on this tiny corpus into general admission. Full source snapshots, compiler/libz version, source/metadata fingerprints, and negative outcomes remain raw archived. This is a scientific causal discriminator only, not a product change, benchmark victory, new format, or release.
