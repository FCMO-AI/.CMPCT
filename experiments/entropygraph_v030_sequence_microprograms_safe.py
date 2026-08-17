"""Safety/portability facade for v0.30 Latent-Type Microprogram research.

The first LTM1 prototype intentionally optimized for mechanism discovery.  This facade closes several
representation-boundary ambiguities before benchmarking it:

* lexical integers are limited to signed 64-bit values and <=20 decimal digits;
* a FOR/delta candidate whose packed residual would exceed 64 bits simply loses instead of aborting the
  entire transform search;
* sparse exception streams must obey the same <=1/16 writer budget when decoded;
* dictionary/alphabet bit widths are canonical rather than merely parseable.

Footnote: these checks are not compression heuristics.  They make the research grammar realistically portable
to a future native reader and prevent authenticated but adversarial descriptors from buying arbitrary-precision
CPU or non-canonical alternate encodings.  The original research module remains preserved as derivation history.
"""
from __future__ import annotations

from experiments import entropygraph_v030_sequence_microprograms as LTM

SIGNED64_MIN = -(1 << 63)
SIGNED64_MAX = (1 << 63) - 1
MAX_DECIMAL_DIGITS = 20

_original_pack_model_values = LTM._pack_model_values
_original_encode_lexint = LTM._encode_lexint
_original_decode_exceptions = LTM._decode_exceptions
_original_decode_dictionary = LTM._decode_dictionary
_original_decode_alphabet = LTM._decode_alphabet


def _portable_pack_model_values(values: list[int], kind: int) -> bytes | None:
    if any(value < SIGNED64_MIN or value > SIGNED64_MAX for value in values):
        return None
    try:
        return _original_pack_model_values(values, kind)
    except ValueError as exc:
        # Footnote: an over-wide residual is a losing representation candidate, not invalid user data.  The
        # generic varint / another codelet / the inherited G3/G4 fallback must remain available.
        if "bit width" in str(exc) or "overflow" in str(exc):
            return None
        raise


def _portable_encode_lexint(values: list[bytes]) -> bytes | None:
    if len(values) < 4:
        return None
    prefix = LTM._common_prefix(values)
    suffix = LTM._common_suffix(values, len(prefix))
    suffix_len = len(suffix)
    cores = [value[len(prefix): len(value) - suffix_len if suffix_len else len(value)] for value in values]
    if any(not core or len(core) > MAX_DECIMAL_DIGITS for core in cores):
        return None
    # Avoid invoking Python's arbitrary-precision parser on an unbounded attacker-controlled decimal string.
    # The original helper still owns lexical-form validation; this facade only establishes the native-width
    # resource contract first.
    try:
        parsed = [int(core.decode("ascii")) for core in cores]
    except (UnicodeDecodeError, ValueError):
        return None
    if any(value < SIGNED64_MIN or value > SIGNED64_MAX for value in parsed):
        return None
    return _original_encode_lexint(values)


def _bounded_decode_exceptions(payload: bytes, pos: int, count: int) -> tuple[dict[int, int], int]:
    exceptions, end = _original_decode_exceptions(payload, pos, count)
    if len(exceptions) > LTM._exception_budget(count):
        raise RuntimeError("LTM exception fraction exceeds policy")
    if any(value < SIGNED64_MIN or value > SIGNED64_MAX for value in exceptions.values()):
        raise RuntimeError("LTM exception value exceeds signed-64 policy")
    return exceptions, end


def _canonical_decode_dictionary(payload: bytes, count: int) -> list[bytes]:
    dictionary_count, pos = LTM._get_varint(payload, 0)
    if not 1 <= dictionary_count <= min(LTM.MAX_DICTIONARY_VALUES, count):
        raise RuntimeError("LTM dictionary count out of bounds")
    dictionary_bytes, pos = LTM._get_varint(payload, pos)
    end = pos + dictionary_bytes
    if end >= len(payload):
        raise RuntimeError("short LTM dictionary payload")
    dictionary = LTM._decode_raw_sequence(payload[pos:end], dictionary_count)
    width = payload[end]
    expected_width = LTM._bits_required(dictionary_count - 1)
    if width != expected_width:
        raise RuntimeError("non-canonical LTM dictionary bit width")
    indices = LTM._unpack_fixed(payload[end + 1:], count, width)
    if any(index >= dictionary_count for index in indices):
        raise RuntimeError("LTM dictionary index out of bounds")
    return [dictionary[index] for index in indices]


def _canonical_decode_alphabet(payload: bytes, count: int) -> list[bytes]:
    alphabet_count, pos = LTM._get_varint(payload, 0)
    if not 2 <= alphabet_count <= LTM.MAX_ALPHABET or pos + alphabet_count > len(payload):
        raise RuntimeError("LTM alphabet declaration out of bounds")
    alphabet = payload[pos:pos + alphabet_count]
    if bytes(sorted(set(alphabet))) != alphabet:
        raise RuntimeError("non-canonical LTM alphabet")
    pos += alphabet_count
    lengths: list[int] = []
    total = 0
    for _ in range(count):
        length, pos = LTM._get_varint(payload, pos)
        if length > LTM.MAX_NODE_BYTES or total + length > LTM.MAX_NODE_BYTES:
            raise RuntimeError("LTM alphabet length budget exceeded")
        lengths.append(length)
        total += length
    if pos >= len(payload):
        raise RuntimeError("short LTM alphabet bit width")
    width = payload[pos]
    pos += 1
    expected_width = LTM._bits_required(alphabet_count - 1)
    if width != expected_width:
        raise RuntimeError("non-canonical LTM alphabet bit width")
    symbols = LTM._unpack_fixed(payload[pos:], total, width)
    if any(symbol >= alphabet_count for symbol in symbols):
        raise RuntimeError("LTM alphabet symbol out of bounds")
    out: list[bytes] = []
    cursor = 0
    for length in lengths:
        out.append(bytes(alphabet[symbol] for symbol in symbols[cursor:cursor + length]))
        cursor += length
    return out


# Patch the shared research module object before exposing benchmark-facing entrypoints.  Its helpers resolve
# these names through module globals at runtime, so integer/codelet construction and inverse parsing both obey
# the hardened contract without forking the entire LTM1 grammar.
LTM._pack_model_values = _portable_pack_model_values
LTM._encode_lexint = _portable_encode_lexint
LTM._decode_exceptions = _bounded_decode_exceptions
LTM._decode_dictionary = _canonical_decode_dictionary
LTM._decode_alphabet = _canonical_decode_alphabet

build_transform = LTM.build_transform
inverse = LTM.inverse
audition = LTM.audition
RESOURCE_LIMITS = {
    **LTM.RESOURCE_LIMITS,
    "signed_integer_bits": 64,
    "max_decimal_digits": MAX_DECIMAL_DIGITS,
}
