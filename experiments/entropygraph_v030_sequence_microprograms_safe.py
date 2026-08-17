"""Safety/portability facade for v0.30 Latent-Type Microprogram research.

The first LTM1 prototype intentionally optimized for mechanism discovery.  This facade closes several
representation-boundary ambiguities before benchmarking it:

* lexical integers are limited to signed 64-bit values and <=20 decimal digits;
* a FOR/delta candidate whose packed residual would exceed 64 bits simply loses instead of aborting the
  entire transform search;
* sparse exception streams must obey the same <=1/16 writer budget when decoded;
* dictionary/alphabet bit widths are canonical rather than merely parseable;
* lexical fixed-width reconstruction is preflighted before allocating rendered values;
* all decoded integer models and affine/sawtooth parameters stay inside the signed-64 portability contract;
* unused high bits in fixed-width packs must be zero, eliminating alternate encodings of the same stream.

Footnote: these checks are not compression heuristics.  They make the research grammar realistically portable
to a future native reader and prevent authenticated but adversarial descriptors from buying arbitrary-precision
CPU, huge lexical padding allocations, or non-canonical alternate encodings.  The original research module
remains preserved as derivation history.
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
_original_decode_int_model = LTM._decode_int_model
_original_affine_model = LTM._affine_model
_original_sawtooth_model = LTM._sawtooth_model
_original_unpack_fixed = LTM._unpack_fixed


def _signed64(value: int) -> bool:
    return SIGNED64_MIN <= value <= SIGNED64_MAX


def _portable_pack_model_values(values: list[int], kind: int) -> bytes | None:
    if any(not _signed64(value) for value in values):
        return None
    try:
        return _original_pack_model_values(values, kind)
    except ValueError as exc:
        # Footnote: an over-wide residual is a losing representation candidate, not invalid user data.  The
        # generic varint / another codelet / the inherited G3/G4 fallback must remain available.
        if "bit width" in str(exc) or "overflow" in str(exc):
            return None
        raise


def _portable_affine_model(values: list[int]) -> bytes | None:
    if any(not _signed64(value) for value in values):
        return None
    payload = _original_affine_model(values)
    if payload is None:
        return None
    base, pos = LTM._get_varint(payload, 1)
    step, _ = LTM._get_varint(payload, pos)
    if not _signed64(LTM._unzigzag(base)) or not _signed64(LTM._unzigzag(step)):
        return None
    return payload


def _portable_sawtooth_model(values: list[int]) -> bytes | None:
    if any(not _signed64(value) for value in values):
        return None
    payload = _original_sawtooth_model(values)
    if payload is None:
        return None
    offset, pos = LTM._get_varint(payload, 1)
    start, pos = LTM._get_varint(payload, pos)
    step, pos = LTM._get_varint(payload, pos)
    modulus, _ = LTM._get_varint(payload, pos)
    if not _signed64(LTM._unzigzag(offset)):
        return None
    if any(value > SIGNED64_MAX for value in (start, step, modulus)):
        return None
    return payload


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
    if any(not _signed64(value) for value in parsed):
        return None
    return _original_encode_lexint(values)


def _bounded_decode_exceptions(payload: bytes, pos: int, count: int) -> tuple[dict[int, int], int]:
    exceptions, end = _original_decode_exceptions(payload, pos, count)
    if len(exceptions) > LTM._exception_budget(count):
        raise RuntimeError("LTM exception fraction exceeds policy")
    if any(not _signed64(value) for value in exceptions.values()):
        raise RuntimeError("LTM exception value exceeds signed-64 policy")
    return exceptions, end


def _canonical_unpack_fixed(buf: bytes, count: int, width: int) -> list[int]:
    values = _original_unpack_fixed(buf, count, width)
    used_bits = count * width
    remainder = used_bits & 7
    if remainder and buf and (buf[-1] >> remainder):
        raise RuntimeError("non-canonical LTM fixed-pack padding bits")
    return values


def _canonical_decode_dictionary(payload: bytes, count: int) -> list[bytes]:
    dictionary_count, pos = LTM._get_varint(payload, 0)
    if not 1 <= dictionary_count <= min(LTM.MAX_DICTIONARY_VALUES, count):
        raise RuntimeError("LTM dictionary count out of bounds")
    dictionary_bytes, pos = LTM._get_varint(payload, pos)
    end = pos + dictionary_bytes
    if end >= len(payload):
        raise RuntimeError("short LTM dictionary payload")
    dictionary = LTM._decode_raw_sequence(payload[pos:end], dictionary_count)
    if len(set(dictionary)) != len(dictionary):
        raise RuntimeError("non-canonical LTM dictionary duplicates")
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


def _portable_decode_int_model(payload: bytes, count: int) -> list[int]:
    values = _original_decode_int_model(payload, count)
    if any(not _signed64(value) for value in values):
        raise RuntimeError("LTM decoded integer exceeds signed-64 policy")
    return values


def _portable_decode_lexint(payload: bytes, count: int) -> list[bytes]:
    """Preflight lexical widths before rendering any attacker-controlled amount of padding."""
    if not payload:
        raise RuntimeError("empty LTM lexint payload")
    mode = payload[0]
    pos = 1
    prefix_len, pos = LTM._get_varint(payload, pos)
    if prefix_len > LTM.MAX_NODE_BYTES or pos + prefix_len > len(payload):
        raise RuntimeError("short or oversized LTM lexint prefix")
    prefix = payload[pos:pos + prefix_len]
    pos += prefix_len
    suffix_len, pos = LTM._get_varint(payload, pos)
    if suffix_len > LTM.MAX_NODE_BYTES or prefix_len + suffix_len > LTM.MAX_NODE_BYTES or pos + suffix_len > len(payload):
        raise RuntimeError("short or oversized LTM lexint suffix")
    suffix = payload[pos:pos + suffix_len]
    pos += suffix_len
    width, pos = LTM._get_varint(payload, pos)
    model_len, pos = LTM._get_varint(payload, pos)
    end = pos + model_len
    if model_len > LTM.MAX_NODE_BYTES or end != len(payload):
        raise RuntimeError("LTM lexint model framing mismatch")
    integers = LTM._decode_int_model(payload[pos:end], count)
    if mode == 0:
        if not 1 <= width <= MAX_DECIMAL_DIGITS:
            raise RuntimeError("invalid LTM fixed lexical width")
        if any(value < 0 for value in integers):
            raise RuntimeError("negative value in fixed-width LTM decimal")
        # A value wider than its declared lexical field would make Python format a longer string and can
        # never be emitted by the writer's exact-render check. Reject it before constructing output bytes.
        if any(len(str(value)) > width for value in integers):
            raise RuntimeError("LTM fixed lexical value exceeds declared width")
        return [prefix + f"{value:0{width}d}".encode() + suffix for value in integers]
    if mode == 1:
        if width != 0:
            raise RuntimeError("canonical LTM integer unexpectedly declares width")
        return [prefix + str(value).encode() + suffix for value in integers]
    raise RuntimeError("unknown LTM lexint mode")


# Patch the shared research module object before exposing benchmark-facing entrypoints.  Its helpers resolve
# these names through module globals at runtime, so integer/codelet construction and inverse parsing both obey
# the hardened contract without forking the entire LTM1 grammar.
LTM._pack_model_values = _portable_pack_model_values
LTM._affine_model = _portable_affine_model
LTM._sawtooth_model = _portable_sawtooth_model
LTM._encode_lexint = _portable_encode_lexint
LTM._decode_exceptions = _bounded_decode_exceptions
LTM._unpack_fixed = _canonical_unpack_fixed
LTM._decode_dictionary = _canonical_decode_dictionary
LTM._decode_alphabet = _canonical_decode_alphabet
LTM._decode_int_model = _portable_decode_int_model
LTM._decode_lexint = _portable_decode_lexint

build_transform = LTM.build_transform
inverse = LTM.inverse
audition = LTM.audition
RESOURCE_LIMITS = {
    **LTM.RESOURCE_LIMITS,
    "signed_integer_bits": 64,
    "max_decimal_digits": MAX_DECIMAL_DIGITS,
    "canonical_fixed_pack_padding": True,
    "canonical_dictionary_values": True,
}
