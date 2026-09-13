from __future__ import annotations

"""Canonical-selector correction for fused pathdict encode attribution.

Mission lock
============
v5 proved the last Tiny Files identity mismatch is not caused by dictionary training:
clean and shared-scan branches have identical ordered training samples and identical
dictionary SHA-256.  Inspection then found a narrower harness defect in
``RecordingIndependentBuilder``.  Its manual dictionary replay compared only
``dict_total < normal_total``.  Canonical ``Builder._encode_candidate`` additionally
requires the winning compressed representation to beat RAW by more than 16 bytes
(``best_total + 16 < len(raw)``).  Tiny Files contains enough small candidates for
that missing RAW margin to change the archive by 123 bytes.

Falsifiable hypothesis
----------------------
If that selector mismatch is the complete remaining cause, restoring the exact
canonical RAW margin while preserving the existing normal-encode cache must yield
byte-identical independent and path-blind-dictionary artifacts on all five first-gate
workloads, with zero cache misses.  Any remaining mismatch disproves this diagnosis.

No product selector, threshold, codec, corpus, locality rule, format, canonical
Builder, comparator, Genesis score, or release state changes.  This restores the
harness to the product semantics it claims to measure.
"""

import msgpack

from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT, TEXT_EXT, zcd
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import (
    TimedFusedPathBlindDictionaryBuilder,
    TimedRecordingIndependentBuilder,
)


class CanonicalRecordingIndependentBuilder(TimedRecordingIndependentBuilder):
    def _encode_candidate(self, h, c):
        dictionary = self.dictionary
        self.dictionary = b''
        try:
            normal = super(TimedRecordingIndependentBuilder, self)._encode_candidate(h, c)
        finally:
            self.dictionary = dictionary

        self._normal_encode_cache[h] = normal

        # Mirror the canonical early exits before dictionary competition.
        if self.dict_hash is not None and h == self.dict_hash:
            return CODEC_RAW, c.raw, b''
        if h in self.secondary_stream_hashes:
            return CODEC_RAW, c.raw, b''
        if h in self.canonical_deflate:
            return normal

        codec, comp, meta = normal
        if dictionary and any(hint.lower() in TEXT_EXT for hint in c.hints):
            dc = zcd(c.raw, dictionary, 12)
            dm = msgpack.packb([12], use_bin_type=True)
            dtotal = len(dc) + len(dm)
            ntotal = len(comp) + len(meta)
            # Canonical Builder only emits a compressed winner when its total
            # physical bytes clear the fixed 16-byte RAW margin.
            if dtotal + 16 < len(c.raw) and (
                codec == CODEC_RAW or dtotal < ntotal
            ):
                return CODEC_ZSTDDICT, dc, dm
        return normal


def _one(source, root):
    # Reuse v4's order-preserving experiment, replacing only the independent
    # recording class with the selector-exact implementation above.
    from benchmarks import v030_r24_pathdict_fused_encode_referee_v4 as V4

    old = V4.TimedRecordingIndependentBuilder
    try:
        V4.TimedRecordingIndependentBuilder = CanonicalRecordingIndependentBuilder
        return V4._one(source, root)
    finally:
        V4.TimedRecordingIndependentBuilder = old


V1._one = _one


def main():
    V1.main()


if __name__ == '__main__':
    main()
