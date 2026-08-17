"""CMPCT v0.30 child research — Latent-Type / Residualized Sequence Microprograms (LTM1).

LTM1 starts *after* Hierarchical Geometry has already discovered a useful pair of byte separators.  It does
not trust a schema or filename.  Instead, each synthetic field column may be represented by a tiny reversible
microprogram chosen from generic byte/sequence hypotheses: raw values, exact periods, dictionaries, restricted
alphabets, or lexical-integer sequences whose integer stream is modeled with FOR/delta/delta2/affine/sawtooth
codelets.  Affine/sawtooth programs may carry sparse explicit exceptions, so useful structure is not discarded
merely because real data contains a few anomalies.

A latent type is only a compression hypothesis.  Its renderer must reproduce every original byte exactly,
including prefixes/suffixes and zero padding, before the candidate is even priced.  The final LTM1 transform
then competes against the *actual G3/G4 Zstd-19 payload* on the same node.  This isolates incremental value
beyond Hierarchical Geometry rather than comparing a new toy to raw bytes.

Footnote: LTM1 is detached transform research, not a canonical CMPCT grammar.  The representation is self-
describing enough for independent inverse tests and explicitly bounded, but archive authentication/recovery
belongs to a later GIR integration only if this mechanism clears its causal gate.
"""
from __future__ import annotations

from collections import Counter

from experiments import entropygraph_v030_hierarchical_geometry as HG
from experiments import entropygraph_v030_geometry as G

MAGIC = b"LTM1"
MAX_NODE_BYTES = G.MAX_CHUNK
MAX_COLUMNS = 64
MAX_DICTIONARY_VALUES = 512
MAX_ALPHABET = 64
MAX_PERIOD = 4096
MAX_PERIOD_CANDIDATES = 32
MAX_EXCEPTIONS = 2048
MAX_EXCEPTION_FRACTION_NUM = 1
MAX_EXCEPTION_FRACTION_DEN = 16
SCREEN_LEVEL = 6
EXACT_LEVEL = 19
MIN_PAYLOAD_SAVING = 64

TAG_RAW = 0
TAG_PERIOD = 1
TAG_DICTIONARY = 2
TAG_ALPHABET = 3
TAG_LEXINT = 4

INT_VARINT = 0
INT_FOR = 1
INT_DELTA = 2
INT_DELTA2 = 3
INT_AFFINE = 4
INT_SAWTOOTH = 5


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative LTM varint")
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    for _ in range(10):
        if pos >= len(buf):
            raise RuntimeError("short LTM varint")
        byte = buf[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise RuntimeError("overlong LTM varint")


def _zigzag(value: int) -> int:
    return value * 2 if value >= 0 else (-value * 2) - 1


def _unzigzag(value: int) -> int:
    return value // 2 if value % 2 == 0 else -((value + 1) // 2)


def _bits_required(value: int) -> int:
    return max(0, int(value).bit_length())


def _pack_fixed(values: list[int], width: int) -> bytes:
    if width < 0 or width > 64:
        raise ValueError("LTM bit width out of bounds")
    if width == 0:
        if any(values):
            raise ValueError("non-zero value in zero-width LTM pack")
        return b""
    limit = 1 << width
    out = bytearray()
    accumulator = 0
    bits = 0
    for value in values:
        if not 0 <= value < limit:
            raise ValueError("LTM fixed-width value overflow")
        accumulator |= value << bits
        bits += width
        while bits >= 8:
            out.append(accumulator & 0xFF)
            accumulator >>= 8
            bits -= 8
    if bits:
        out.append(accumulator & 0xFF)
    return bytes(out)


def _unpack_fixed(buf: bytes, count: int, width: int) -> list[int]:
    if count < 0 or width < 0 or width > 64:
        raise RuntimeError("invalid LTM fixed pack declaration")
    needed = (count * width + 7) // 8
    if len(buf) != needed:
        raise RuntimeError("LTM fixed pack length mismatch")
    if width == 0:
        return [0] * count
    mask = (1 << width) - 1
    out: list[int] = []
    accumulator = 0
    bits = 0
    cursor = 0
    for _ in range(count):
        while bits < width:
            accumulator |= buf[cursor] << bits
            cursor += 1
            bits += 8
        out.append(accumulator & mask)
        accumulator >>= width
        bits -= width
    return out


def _encode_raw_sequence(values: list[bytes]) -> bytes:
    out = bytearray()
    for value in values:
        _put_varint(out, len(value))
    for value in values:
        out.extend(value)
    return bytes(out)


def _decode_raw_sequence(payload: bytes, count: int) -> list[bytes]:
    pos = 0
    lengths: list[int] = []
    total = 0
    for _ in range(count):
        length, pos = _get_varint(payload, pos)
        if length > MAX_NODE_BYTES or total + length > MAX_NODE_BYTES:
            raise RuntimeError("LTM raw sequence length budget exceeded")
        lengths.append(length)
        total += length
    if len(payload) - pos != total:
        raise RuntimeError("LTM raw sequence payload length mismatch")
    out = []
    for length in lengths:
        out.append(payload[pos:pos + length])
        pos += length
    return out


def _period(values: list[bytes]) -> int | None:
    if len(values) < 4:
        return None
    candidates: list[int] = []
    upper = min(MAX_PERIOD, len(values) - 1)
    for index in range(1, upper + 1):
        if values[index] == values[0]:
            candidates.append(index)
            if len(candidates) >= MAX_PERIOD_CANDIDATES:
                break
    for period in candidates:
        if all(value == values[index % period] for index, value in enumerate(values)):
            return period
    return None


def _encode_period(values: list[bytes]) -> bytes | None:
    period = _period(values)
    if period is None:
        return None
    out = bytearray()
    _put_varint(out, period)
    seed = _encode_raw_sequence(values[:period])
    out.extend(seed)
    return bytes(out)


def _decode_period(payload: bytes, count: int) -> list[bytes]:
    period, pos = _get_varint(payload, 0)
    if not 1 <= period <= min(MAX_PERIOD, count):
        raise RuntimeError("LTM period out of bounds")
    seed = _decode_raw_sequence(payload[pos:], period)
    return [seed[index % period] for index in range(count)]


def _encode_dictionary(values: list[bytes]) -> bytes | None:
    dictionary: list[bytes] = []
    index_by_value: dict[bytes, int] = {}
    indices: list[int] = []
    for value in values:
        index = index_by_value.get(value)
        if index is None:
            if len(dictionary) >= MAX_DICTIONARY_VALUES:
                return None
            index = len(dictionary)
            dictionary.append(value)
            index_by_value[value] = index
        indices.append(index)
    if len(dictionary) >= len(values):
        return None
    width = _bits_required(len(dictionary) - 1)
    out = bytearray()
    _put_varint(out, len(dictionary))
    encoded_dict = _encode_raw_sequence(dictionary)
    _put_varint(out, len(encoded_dict))
    out.extend(encoded_dict)
    out.append(width)
    out.extend(_pack_fixed(indices, width))
    return bytes(out)


def _decode_dictionary(payload: bytes, count: int) -> list[bytes]:
    dictionary_count, pos = _get_varint(payload, 0)
    if not 1 <= dictionary_count <= min(MAX_DICTIONARY_VALUES, count):
        raise RuntimeError("LTM dictionary count out of bounds")
    dictionary_bytes, pos = _get_varint(payload, pos)
    end = pos + dictionary_bytes
    if end >= len(payload):
        raise RuntimeError("short LTM dictionary payload")
    dictionary = _decode_raw_sequence(payload[pos:end], dictionary_count)
    width = payload[end]
    indices = _unpack_fixed(payload[end + 1:], count, width)
    if any(index >= dictionary_count for index in indices):
        raise RuntimeError("LTM dictionary index out of bounds")
    return [dictionary[index] for index in indices]


def _encode_alphabet(values: list[bytes]) -> bytes | None:
    alphabet = sorted(set(b"".join(values)))
    if not 2 <= len(alphabet) <= MAX_ALPHABET:
        return None
    width = _bits_required(len(alphabet) - 1)
    mapping = {byte: index for index, byte in enumerate(alphabet)}
    symbols = [mapping[byte] for value in values for byte in value]
    out = bytearray()
    _put_varint(out, len(alphabet))
    out.extend(alphabet)
    for value in values:
        _put_varint(out, len(value))
    out.append(width)
    out.extend(_pack_fixed(symbols, width))
    return bytes(out)


def _decode_alphabet(payload: bytes, count: int) -> list[bytes]:
    alphabet_count, pos = _get_varint(payload, 0)
    if not 2 <= alphabet_count <= MAX_ALPHABET or pos + alphabet_count > len(payload):
        raise RuntimeError("LTM alphabet declaration out of bounds")
    alphabet = payload[pos:pos + alphabet_count]
    pos += alphabet_count
    lengths: list[int] = []
    total = 0
    for _ in range(count):
        length, pos = _get_varint(payload, pos)
        if length > MAX_NODE_BYTES or total + length > MAX_NODE_BYTES:
            raise RuntimeError("LTM alphabet length budget exceeded")
        lengths.append(length)
        total += length
    if pos >= len(payload):
        raise RuntimeError("short LTM alphabet bit width")
    width = payload[pos]
    pos += 1
    symbols = _unpack_fixed(payload[pos:], total, width)
    if any(symbol >= alphabet_count for symbol in symbols):
        raise RuntimeError("LTM alphabet symbol out of bounds")
    out: list[bytes] = []
    cursor = 0
    for length in lengths:
        out.append(bytes(alphabet[symbol] for symbol in symbols[cursor:cursor + length]))
        cursor += length
    return out


def _common_prefix(values: list[bytes]) -> bytes:
    if not values:
        return b""
    limit = min(map(len, values))
    index = 0
    while index < limit:
        byte = values[0][index]
        if any(value[index] != byte for value in values[1:]):
            break
        index += 1
    return values[0][:index]


def _common_suffix(values: list[bytes], prefix_len: int) -> bytes:
    if not values:
        return b""
    limit = min(len(value) - prefix_len for value in values)
    count = 0
    while count < limit:
        byte = values[0][len(values[0]) - 1 - count]
        if any(value[len(value) - 1 - count] != byte for value in values[1:]):
            break
        count += 1
    return values[0][len(values[0]) - count:] if count else b""


def _encode_exceptions(exceptions: list[tuple[int, int]]) -> bytes:
    out = bytearray()
    _put_varint(out, len(exceptions))
    previous = -1
    for index, value in exceptions:
        if index <= previous:
            raise ValueError("LTM exceptions are not strictly ordered")
        _put_varint(out, index - previous - 1)
        _put_varint(out, _zigzag(value))
        previous = index
    return bytes(out)


def _decode_exceptions(payload: bytes, pos: int, count: int) -> tuple[dict[int, int], int]:
    exception_count, pos = _get_varint(payload, pos)
    if exception_count > min(MAX_EXCEPTIONS, count):
        raise RuntimeError("LTM exception count out of bounds")
    exceptions: dict[int, int] = {}
    previous = -1
    for _ in range(exception_count):
        delta, pos = _get_varint(payload, pos)
        index = previous + 1 + delta
        encoded, pos = _get_varint(payload, pos)
        if not 0 <= index < count or index in exceptions:
            raise RuntimeError("LTM exception index out of bounds")
        exceptions[index] = _unzigzag(encoded)
        previous = index
    return exceptions, pos


def _exception_budget(count: int) -> int:
    return min(MAX_EXCEPTIONS, (count * MAX_EXCEPTION_FRACTION_NUM) // MAX_EXCEPTION_FRACTION_DEN)


def _pack_model_values(values: list[int], kind: int) -> bytes | None:
    count = len(values)
    if count == 0:
        return None
    out = bytearray((kind,))
    if kind == INT_VARINT:
        for value in values:
            _put_varint(out, _zigzag(value))
        return bytes(out)
    if kind == INT_FOR:
        minimum = min(values)
        residuals = [value - minimum for value in values]
        width = _bits_required(max(residuals, default=0))
        _put_varint(out, _zigzag(minimum))
        out.append(width)
        out.extend(_pack_fixed(residuals, width))
        return bytes(out)
    if kind == INT_DELTA:
        _put_varint(out, _zigzag(values[0]))
        deltas = [_zigzag(values[index] - values[index - 1]) for index in range(1, count)]
        width = _bits_required(max(deltas, default=0))
        out.append(width)
        out.extend(_pack_fixed(deltas, width))
        return bytes(out)
    if kind == INT_DELTA2:
        _put_varint(out, _zigzag(values[0]))
        if count == 1:
            _put_varint(out, 0)
            out.append(0)
            return bytes(out)
        first_delta = values[1] - values[0]
        _put_varint(out, _zigzag(first_delta))
        dd = [_zigzag((values[index] - values[index - 1]) - (values[index - 1] - values[index - 2])) for index in range(2, count)]
        width = _bits_required(max(dd, default=0))
        out.append(width)
        out.extend(_pack_fixed(dd, width))
        return bytes(out)
    return None


def _affine_model(values: list[int]) -> bytes | None:
    if len(values) < 4:
        return None
    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    step, _ = Counter(deltas).most_common(1)[0]
    predicted = [values[0] + step * index for index in range(len(values))]
    exceptions = [(index, value) for index, value in enumerate(values) if value != predicted[index]]
    if len(exceptions) > _exception_budget(len(values)):
        return None
    out = bytearray((INT_AFFINE,))
    _put_varint(out, _zigzag(values[0]))
    _put_varint(out, _zigzag(step))
    out.extend(_encode_exceptions(exceptions))
    return bytes(out)


def _sawtooth_model(values: list[int]) -> bytes | None:
    if len(values) < 8:
        return None
    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    counts = Counter(deltas)
    positive = [(count, delta) for delta, count in counts.items() if delta > 0]
    negative = [(count, delta) for delta, count in counts.items() if delta < 0]
    if not positive or not negative:
        return None
    _, step = max(positive)
    _, wrap_delta = max(negative)
    modulus = step - wrap_delta
    offset = min(values)
    start = values[0] - offset
    if modulus <= 1 or not 0 <= start < modulus:
        return None
    predicted = [offset + ((start + step * index) % modulus) for index in range(len(values))]
    exceptions = [(index, value) for index, value in enumerate(values) if value != predicted[index]]
    if len(exceptions) > _exception_budget(len(values)):
        return None
    out = bytearray((INT_SAWTOOTH,))
    _put_varint(out, _zigzag(offset))
    _put_varint(out, start)
    _put_varint(out, step)
    _put_varint(out, modulus)
    out.extend(_encode_exceptions(exceptions))
    return bytes(out)


def _encode_int_model(values: list[int]) -> bytes:
    candidates = [
        _pack_model_values(values, INT_VARINT),
        _pack_model_values(values, INT_FOR),
        _pack_model_values(values, INT_DELTA),
        _pack_model_values(values, INT_DELTA2),
        _affine_model(values),
        _sawtooth_model(values),
    ]
    viable = [candidate for candidate in candidates if candidate is not None]
    return min(viable, key=lambda payload: (len(payload), payload[0]))


def _decode_int_model(payload: bytes, count: int) -> list[int]:
    if not payload:
        raise RuntimeError("empty LTM integer model")
    kind = payload[0]
    pos = 1
    if kind == INT_VARINT:
        out = []
        for _ in range(count):
            value, pos = _get_varint(payload, pos)
            out.append(_unzigzag(value))
    elif kind == INT_FOR:
        minimum, pos = _get_varint(payload, pos)
        minimum = _unzigzag(minimum)
        if pos >= len(payload):
            raise RuntimeError("short LTM FOR width")
        width = payload[pos]
        pos += 1
        residuals = _unpack_fixed(payload[pos:], count, width)
        pos = len(payload)
        out = [minimum + residual for residual in residuals]
    elif kind == INT_DELTA:
        first, pos = _get_varint(payload, pos)
        first = _unzigzag(first)
        if pos >= len(payload):
            raise RuntimeError("short LTM delta width")
        width = payload[pos]
        pos += 1
        encoded = _unpack_fixed(payload[pos:], max(0, count - 1), width)
        pos = len(payload)
        out = [first]
        for delta in encoded:
            out.append(out[-1] + _unzigzag(delta))
    elif kind == INT_DELTA2:
        first, pos = _get_varint(payload, pos)
        first = _unzigzag(first)
        first_delta, pos = _get_varint(payload, pos)
        first_delta = _unzigzag(first_delta)
        if pos >= len(payload):
            raise RuntimeError("short LTM delta2 width")
        width = payload[pos]
        pos += 1
        encoded = _unpack_fixed(payload[pos:], max(0, count - 2), width)
        pos = len(payload)
        out = [first]
        if count > 1:
            out.append(first + first_delta)
            delta = first_delta
            for dd in encoded:
                delta += _unzigzag(dd)
                out.append(out[-1] + delta)
    elif kind == INT_AFFINE:
        base, pos = _get_varint(payload, pos)
        step, pos = _get_varint(payload, pos)
        base = _unzigzag(base)
        step = _unzigzag(step)
        exceptions, pos = _decode_exceptions(payload, pos, count)
        out = [exceptions.get(index, base + step * index) for index in range(count)]
    elif kind == INT_SAWTOOTH:
        offset, pos = _get_varint(payload, pos)
        offset = _unzigzag(offset)
        start, pos = _get_varint(payload, pos)
        step, pos = _get_varint(payload, pos)
        modulus, pos = _get_varint(payload, pos)
        if modulus <= 1 or start >= modulus:
            raise RuntimeError("invalid LTM sawtooth model")
        exceptions, pos = _decode_exceptions(payload, pos, count)
        out = [exceptions.get(index, offset + ((start + step * index) % modulus)) for index in range(count)]
    else:
        raise RuntimeError("unknown LTM integer model")
    if len(out) != count or pos != len(payload):
        raise RuntimeError("LTM integer model length mismatch")
    return out


def _encode_lexint(values: list[bytes]) -> bytes | None:
    if len(values) < 4:
        return None
    prefix = _common_prefix(values)
    suffix = _common_suffix(values, len(prefix))
    suffix_len = len(suffix)
    cores = [value[len(prefix): len(value) - suffix_len if suffix_len else len(value)] for value in values]
    if any(not core for core in cores):
        return None

    mode: int
    width = 0
    if all(core.isdigit() for core in cores) and len({len(core) for core in cores}) == 1:
        mode = 0  # fixed-width zero-preserving decimal core
        width = len(cores[0])
        integers = [int(core) for core in cores]
        rendered = [prefix + f"{value:0{width}d}".encode() + suffix for value in integers]
    else:
        try:
            integers = [int(core.decode("ascii")) for core in cores]
        except (UnicodeDecodeError, ValueError):
            return None
        if any(str(value).encode() != core for value, core in zip(integers, cores)):
            return None
        mode = 1  # canonical signed decimal core
        rendered = [prefix + str(value).encode() + suffix for value in integers]
    if rendered != values:
        return None

    model = _encode_int_model(integers)
    out = bytearray((mode,))
    _put_varint(out, len(prefix)); out.extend(prefix)
    _put_varint(out, len(suffix)); out.extend(suffix)
    _put_varint(out, width)
    _put_varint(out, len(model)); out.extend(model)
    return bytes(out)


def _decode_lexint(payload: bytes, count: int) -> list[bytes]:
    if not payload:
        raise RuntimeError("empty LTM lexint payload")
    mode = payload[0]
    pos = 1
    prefix_len, pos = _get_varint(payload, pos)
    if pos + prefix_len > len(payload):
        raise RuntimeError("short LTM lexint prefix")
    prefix = payload[pos:pos + prefix_len]; pos += prefix_len
    suffix_len, pos = _get_varint(payload, pos)
    if pos + suffix_len > len(payload):
        raise RuntimeError("short LTM lexint suffix")
    suffix = payload[pos:pos + suffix_len]; pos += suffix_len
    width, pos = _get_varint(payload, pos)
    model_len, pos = _get_varint(payload, pos)
    end = pos + model_len
    if end != len(payload):
        raise RuntimeError("LTM lexint model framing mismatch")
    integers = _decode_int_model(payload[pos:end], count)
    if mode == 0:
        if not 1 <= width <= MAX_NODE_BYTES:
            raise RuntimeError("invalid LTM fixed lexical width")
        return [prefix + f"{value:0{width}d}".encode() + suffix for value in integers]
    if mode == 1:
        if width != 0:
            raise RuntimeError("canonical LTM integer unexpectedly declares width")
        return [prefix + str(value).encode() + suffix for value in integers]
    raise RuntimeError("unknown LTM lexint mode")


def _candidate_score(tag: int, payload: bytes) -> tuple[int, int, int]:
    framed = bytes((tag,)) + payload
    compressed = G.zc(framed, SCREEN_LEVEL)
    return min(len(framed), len(compressed)), len(framed), tag


def _encode_column(values: list[bytes]) -> tuple[int, bytes]:
    candidates: list[tuple[int, bytes]] = [(TAG_RAW, _encode_raw_sequence(values))]
    period = _encode_period(values)
    if period is not None:
        candidates.append((TAG_PERIOD, period))
    dictionary = _encode_dictionary(values)
    if dictionary is not None:
        candidates.append((TAG_DICTIONARY, dictionary))
    alphabet = _encode_alphabet(values)
    if alphabet is not None:
        candidates.append((TAG_ALPHABET, alphabet))
    lexint = _encode_lexint(values)
    if lexint is not None:
        candidates.append((TAG_LEXINT, lexint))
    tag, payload = min(candidates, key=lambda item: _candidate_score(*item))
    return tag, payload


def _decode_column(tag: int, payload: bytes, count: int) -> list[bytes]:
    if tag == TAG_RAW:
        return _decode_raw_sequence(payload, count)
    if tag == TAG_PERIOD:
        return _decode_period(payload, count)
    if tag == TAG_DICTIONARY:
        return _decode_dictionary(payload, count)
    if tag == TAG_ALPHABET:
        return _decode_alphabet(payload, count)
    if tag == TAG_LEXINT:
        return _decode_lexint(payload, count)
    raise RuntimeError("unknown LTM column codelet")


def build_transform(raw: bytes, primary: int, secondary: int) -> tuple[bytes, dict]:
    fields, max_fields, descriptors = HG._parse_shape(raw, primary, secondary)
    if max_fields > MAX_COLUMNS:
        raise ValueError("LTM inferred-column ceiling exceeded")
    out = bytearray(MAGIC)
    out.extend((primary, secondary))
    _put_varint(out, len(fields))
    for row in fields:
        _put_varint(out, len(row))
    _put_varint(out, max_fields)

    codelet_counts = {"raw": 0, "period": 0, "dictionary": 0, "alphabet": 0, "lexint": 0}
    names = {TAG_RAW: "raw", TAG_PERIOD: "period", TAG_DICTIONARY: "dictionary", TAG_ALPHABET: "alphabet", TAG_LEXINT: "lexint"}
    for column in range(max_fields):
        values = [row[column] for row in fields if column < len(row)]
        tag, payload = _encode_column(values)
        codelet_counts[names[tag]] += 1
        out.append(tag)
        _put_varint(out, len(payload))
        out.extend(payload)
    if len(out) > G.MAX_DECODE_UNIT:
        raise ValueError("LTM transformed stream exceeds decode ceiling")
    return bytes(out), {
        "rows": len(fields),
        "max_fields": max_fields,
        "field_descriptors": descriptors,
        "codelet_counts": codelet_counts,
    }


def inverse(encoded: bytes, logical_size: int) -> bytes:
    if len(encoded) < 8 or encoded[:4] != MAGIC:
        raise RuntimeError("invalid LTM magic")
    primary, secondary = encoded[4], encoded[5]
    if primary == secondary:
        raise RuntimeError("LTM separators alias")
    row_count, pos = _get_varint(encoded, 6)
    if not 1 <= row_count <= HG.MAX_ROWS:
        raise RuntimeError("LTM row count out of bounds")
    field_counts: list[int] = []
    total_fields = 0
    max_fields_seen = 0
    for _ in range(row_count):
        count, pos = _get_varint(encoded, pos)
        if not 1 <= count <= HG.MAX_FIELDS_PER_ROW:
            raise RuntimeError("LTM row field count out of bounds")
        total_fields += count
        if total_fields > HG.MAX_FIELD_DESCRIPTORS:
            raise RuntimeError("LTM field descriptor budget exceeded")
        field_counts.append(count)
        max_fields_seen = max(max_fields_seen, count)
    max_fields, pos = _get_varint(encoded, pos)
    if max_fields != max_fields_seen or max_fields > MAX_COLUMNS:
        raise RuntimeError("LTM inferred-column declaration mismatch")
    if row_count * max_fields > HG.MAX_CELL_SCANS:
        raise RuntimeError("LTM cell-work budget exceeded")

    columns: list[list[bytes]] = []
    total_value_bytes = 0
    for column in range(max_fields):
        if pos >= len(encoded):
            raise RuntimeError("short LTM column tag")
        tag = encoded[pos]; pos += 1
        payload_len, pos = _get_varint(encoded, pos)
        end = pos + payload_len
        if end > len(encoded) or payload_len > G.MAX_DECODE_UNIT:
            raise RuntimeError("short or oversized LTM column payload")
        count = sum(field_count > column for field_count in field_counts)
        values = _decode_column(tag, encoded[pos:end], count)
        total_value_bytes += sum(map(len, values))
        if total_value_bytes > logical_size:
            raise RuntimeError("LTM decoded field bytes exceed logical size")
        columns.append(values)
        pos = end
    if pos != len(encoded):
        raise RuntimeError("trailing LTM payload")

    cursors = [0] * max_fields
    rows: list[bytes] = []
    for field_count in field_counts:
        values: list[bytes] = []
        for column in range(field_count):
            cursor = cursors[column]
            if cursor >= len(columns[column]):
                raise RuntimeError("LTM column underflow")
            values.append(columns[column][cursor])
            cursors[column] += 1
        rows.append(bytes((secondary,)).join(values))
    if any(cursors[column] != len(columns[column]) for column in range(max_fields)):
        raise RuntimeError("LTM column overflow")
    raw = bytes((primary,)).join(rows)
    if len(raw) != logical_size:
        raise RuntimeError("LTM inverse logical-size mismatch")
    return raw


def audition(raw: bytes) -> dict:
    base = HG.audition(raw)
    result = {
        "kind": "hierarchical-incumbent" if base["kind"] == "hierarchical" else "geometry-incumbent",
        "payload": base["payload"],
        "payload_bytes": int(base["payload_bytes"]),
        "physical": base["physical"],
        "saving_vs_hierarchical_bytes": 0,
        "primary": base.get("primary"),
        "secondary": base.get("secondary"),
        "prefix_planes": bool(base.get("prefix_planes", False)),
        "microprogram_stats": None,
    }
    if base["kind"] != "hierarchical" or len(raw) > MAX_NODE_BYTES:
        return result
    primary = int(base["primary"])
    secondary = int(base["secondary"])
    try:
        transformed, stats = build_transform(raw, primary, secondary)
    except ValueError:
        return result
    if inverse(transformed, len(raw)) != raw:
        raise RuntimeError("LTM candidate failed exact inverse")
    payload = G.zc(transformed, EXACT_LEVEL)
    if len(payload) >= len(transformed):
        payload = transformed
    saving = int(base["payload_bytes"]) - len(payload)
    if saving < MIN_PAYLOAD_SAVING:
        return result
    return {
        "kind": "latent-microprogram",
        "payload": payload,
        "payload_bytes": len(payload),
        "physical": transformed,
        "saving_vs_hierarchical_bytes": saving,
        "primary": primary,
        "secondary": secondary,
        "prefix_planes": bool(base.get("prefix_planes", False)),
        "microprogram_stats": stats,
    }


RESOURCE_LIMITS = {
    "max_node_bytes": MAX_NODE_BYTES,
    "max_columns": MAX_COLUMNS,
    "max_dictionary_values": MAX_DICTIONARY_VALUES,
    "max_alphabet": MAX_ALPHABET,
    "max_period": MAX_PERIOD,
    "max_period_candidates": MAX_PERIOD_CANDIDATES,
    "max_exceptions": MAX_EXCEPTIONS,
    "max_exception_fraction_num": MAX_EXCEPTION_FRACTION_NUM,
    "max_exception_fraction_den": MAX_EXCEPTION_FRACTION_DEN,
    "screen_level": SCREEN_LEVEL,
    "exact_level": EXACT_LEVEL,
}
