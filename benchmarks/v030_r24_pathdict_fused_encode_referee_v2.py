from __future__ import annotations

"""Harness-only correction for v030_r24_pathdict_fused_encode_referee.

The first hosted attempt died before a receipt because the referee looked for
TEXT_EXT on cmpct.builder and passed a set to str.endswith().  Canonical authority
keeps TEXT_EXT in cmpct.codec and candidate hints are extension tokens, so the
mature condition is membership in TEXT_EXT.  This wrapper changes only that replica
of the existing selector.  The hypothesis, contenders, codecs, thresholds, corpus,
identity gates and output schema are unchanged.
"""

import msgpack

from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT, TEXT_EXT, zcd
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1


class RecordingIndependentBuilder(V1.SAME.NoMicroPackBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._normal_encode_cache = {}

    def _encode_candidate(self, h, c):
        dictionary = self.dictionary
        self.dictionary = b''
        try:
            normal = super()._encode_candidate(h, c)
        finally:
            self.dictionary = dictionary
        self._normal_encode_cache[h] = normal
        if self.dict_hash is not None and h == self.dict_hash:
            return CODEC_RAW, c.raw, b''
        codec, comp, meta = normal
        if dictionary and any(hint.lower() in TEXT_EXT for hint in c.hints):
            dc = zcd(c.raw, dictionary, 12)
            dm = msgpack.packb([12], use_bin_type=True)
            if len(dc) + len(dm) < len(comp) + len(meta):
                return CODEC_ZSTDDICT, dc, dm
        return codec, comp, meta


# V1._one resolves this module global dynamically at execution time.
V1.RecordingIndependentBuilder = RecordingIndependentBuilder


def main():
    V1.main()


if __name__ == '__main__':
    main()
