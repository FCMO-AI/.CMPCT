"""CMPCT v0.30 child research — schema-blind Bitplane Algebra (BPA1).

This experiment extends Geometry below the byte-lane level without trusting a file type or schema.  For a
bounded byte node it may hypothesize a word width/alignment, apply one reversible sequence predictor, apply a
small invertible intra-word GF(2) change of basis, transpose the result into bit planes, and finally ask the
same Zstd-19 physical codec whether the representation beats the *existing* G0/G1/G2 Geometry incumbent.

Prior art is explicit: Bitshuffle establishes bit-plane transpose; Gorilla/related floating-point codecs use
previous-value XOR; columnar formats use delta transforms.  The research question here is narrower and new to
CMPCT: can a bounded arbitrary-byte compiler infer alignment and a tiny reversible binary algebra that beats
our already-adaptive byte Geometry without importing semantic type metadata?

Footnote: BPA1 is a transform/oracle, not a canonical archive grammar.  The 8-byte BPA1 descriptor is embedded
inside the candidate bytes so the size oracle conservatively pays for width/alignment/predictor/basis state.
Any later GIR integration may move that descriptor to authenticated node metadata, but it may not pretend the
state was free during discovery.
"""
from __future__ import annotations

from collections import Counter
import math

# Import the safety facade first.  It patches the shared Geometry module object so this child experiment can
# never accidentally benchmark against an unsafe G2 incumbent merely because import order changed.
from experiments import entropygraph_v030_geometry_safe as _GEOMETRY_SAFE  # noqa: F401
from experiments import entropygraph_v030_geometry as G

MAGIC = b"BPA1"
MAX_NODE_BYTES = G.MAX_CHUNK
WORD_WIDTHS = (2, 4, 8)
PREDICTORS = ("identity", "xor-prev", "sub-prev")
SCREEN_LEVEL = 6
EXACT_LEVEL = 19
SCREEN_SAMPLE_BYTES = 64 * 1024
MAX_ALIGNMENTS_PER_WIDTH = 2
MAX_EXACT_FINALISTS = 4
MIN_PAYLOAD_SAVING = 64

PREDICTOR_TAG = {"identity": 0, "xor-prev": 1, "sub-prev": 2}
TAG_PREDICTOR = {value: key for key, value in PREDICTOR_TAG.items()}


def _basis_options(bits: int) -> tuple[tuple[str, int], ...]:
    shifts = tuple(shift for shift in (1, 2, 4, 8, 16, 32) if shift < bits)
    return (("none", 0),) + tuple(("right", shift) for shift in shifts) + tuple(("left", shift) for shift in shifts)


def _basis_tag(direction: str, shift: int) -> int:
    if direction == "none":
        return 0
    if shift not in (1, 2, 4, 8, 16, 32):
        raise ValueError("unsupported BPA basis shift")
    slot = {1: 1, 2: 2, 4: 3, 8: 4, 16: 5, 32: 6}[shift]
    return slot if direction == "right" else 0x80 | slot


def _tag_basis(tag: int, bits: int) -> tuple[str, int]:
    if tag == 0:
        return "none", 0
    direction = "left" if tag & 0x80 else "right"
    slot = tag & 0x7F
    shifts = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32}
    shift = shifts.get(slot)
    if shift is None or shift >= bits:
        raise RuntimeError("invalid BPA basis descriptor")
    return direction, shift


def _xor_shift_forward(value: int, bits: int, direction: str, shift: int) -> int:
    mask = (1 << bits) - 1
    if direction == "none":
        return value & mask
    if direction == "right":
        return (value ^ (value >> shift)) & mask
    if direction == "left":
        return (value ^ ((value << shift) & mask)) & mask
    raise ValueError("unknown BPA basis direction")


def _xor_shift_inverse(value: int, bits: int, direction: str, shift: int) -> int:
    """Invert one triangular GF(2) xor-shift exactly.

    Footnote: `x -> x XOR (x >> s)` and its left-shift analogue are triangular linear maps over GF(2), so
    their inverse is a finite XOR series.  This keeps the basis descriptor tiny and avoids storing a general
    matrix whose parser/memory surface would be much harder to bound.
    """
    mask = (1 << bits) - 1
    if direction == "none":
        return value & mask
    result = value & mask
    offset = shift
    while offset < bits:
        if direction == "right":
            result ^= value >> offset
        elif direction == "left":
            result ^= (value << offset) & mask
        else:
            raise ValueError("unknown BPA basis direction")
        offset += shift
    return result & mask


def _predict_forward(body: bytes, width: int, predictor: str) -> bytes:
    if len(body) % width:
        raise ValueError("BPA predictor body is not word aligned")
    if predictor == "identity":
        return body
    mask = (1 << (8 * width)) - 1
    out = bytearray(len(body))
    previous = 0
    for offset in range(0, len(body), width):
        current = int.from_bytes(body[offset:offset + width], "little")
        if offset == 0:
            encoded = current
        elif predictor == "xor-prev":
            encoded = current ^ previous
        elif predictor == "sub-prev":
            encoded = (current - previous) & mask
        else:
            raise ValueError("unknown BPA predictor")
        out[offset:offset + width] = encoded.to_bytes(width, "little")
        previous = current
    return bytes(out)


def _predict_inverse(body: bytes, width: int, predictor: str) -> bytes:
    if len(body) % width:
        raise RuntimeError("BPA inverse body is not word aligned")
    if predictor == "identity":
        return body
    mask = (1 << (8 * width)) - 1
    out = bytearray(len(body))
    previous = 0
    for offset in range(0, len(body), width):
        encoded = int.from_bytes(body[offset:offset + width], "little")
        if offset == 0:
            current = encoded
        elif predictor == "xor-prev":
            current = encoded ^ previous
        elif predictor == "sub-prev":
            current = (previous + encoded) & mask
        else:
            raise RuntimeError("unknown BPA predictor")
        out[offset:offset + width] = current.to_bytes(width, "little")
        previous = current
    return bytes(out)


def _basis_forward(body: bytes, width: int, direction: str, shift: int) -> bytes:
    if direction == "none":
        return body
    bits = width * 8
    out = bytearray(len(body))
    for offset in range(0, len(body), width):
        value = int.from_bytes(body[offset:offset + width], "little")
        transformed = _xor_shift_forward(value, bits, direction, shift)
        out[offset:offset + width] = transformed.to_bytes(width, "little")
    return bytes(out)


def _basis_inverse(body: bytes, width: int, direction: str, shift: int) -> bytes:
    if direction == "none":
        return body
    bits = width * 8
    out = bytearray(len(body))
    for offset in range(0, len(body), width):
        value = int.from_bytes(body[offset:offset + width], "little")
        restored = _xor_shift_inverse(value, bits, direction, shift)
        out[offset:offset + width] = restored.to_bytes(width, "little")
    return bytes(out)


def _bitshuffle_body(body: bytes, width: int) -> bytes:
    """Transpose complete groups of eight words into bit planes without changing byte count."""
    words = len(body) // width
    if len(body) % width or words % 8:
        raise ValueError("BPA bitshuffle body must contain a multiple of eight complete words")
    bits = width * 8
    plane_bytes = words // 8
    out = bytearray(len(body))
    for bit in range(bits):
        plane_start = bit * plane_bytes
        byte_index = bit // 8
        bit_mask = 1 << (bit % 8)
        for group in range(plane_bytes):
            packed = 0
            word_base = group * 8
            for lane in range(8):
                src = (word_base + lane) * width + byte_index
                if body[src] & bit_mask:
                    packed |= 1 << lane
            out[plane_start + group] = packed
    return bytes(out)


def _bitunshuffle_body(shuffled: bytes, width: int) -> bytes:
    words = len(shuffled) // width
    if len(shuffled) % width or words % 8:
        raise RuntimeError("BPA bitunshuffle body must contain a multiple of eight complete words")
    bits = width * 8
    plane_bytes = words // 8
    out = bytearray(len(shuffled))
    for bit in range(bits):
        plane_start = bit * plane_bytes
        byte_index = bit // 8
        bit_mask = 1 << (bit % 8)
        for group in range(plane_bytes):
            packed = shuffled[plane_start + group]
            word_base = group * 8
            for lane in range(8):
                if packed & (1 << lane):
                    out[(word_base + lane) * width + byte_index] |= bit_mask
    return bytes(out)


def _body_span(logical_size: int, width: int, alignment: int) -> tuple[int, int]:
    if not 0 <= alignment < width or logical_size < alignment:
        raise ValueError("invalid BPA alignment")
    group = width * 8
    body_size = ((logical_size - alignment) // group) * group
    return alignment, alignment + body_size


def forward(raw: bytes, width: int, alignment: int, predictor: str, basis: tuple[str, int]) -> bytes:
    if len(raw) > MAX_NODE_BYTES:
        raise ValueError("BPA input exceeds inherited logical-node ceiling")
    if width not in WORD_WIDTHS or predictor not in PREDICTORS:
        raise ValueError("unsupported BPA transform")
    direction, shift = basis
    if basis not in _basis_options(width * 8):
        raise ValueError("unsupported BPA basis")
    start, end = _body_span(len(raw), width, alignment)
    body = raw[start:end]
    if not body:
        raise ValueError("BPA candidate has no complete eight-word body")
    predicted = _predict_forward(body, width, predictor)
    based = _basis_forward(predicted, width, direction, shift)
    shuffled = _bitshuffle_body(based, width)
    header = MAGIC + bytes((width, alignment, PREDICTOR_TAG[predictor], _basis_tag(direction, shift)))
    return header + raw[:start] + shuffled + raw[end:]


def inverse(encoded: bytes, logical_size: int) -> bytes:
    if len(encoded) != logical_size + 8 or encoded[:4] != MAGIC:
        raise RuntimeError("invalid BPA framing")
    width, alignment, predictor_tag, basis_tag = encoded[4:8]
    if width not in WORD_WIDTHS or predictor_tag not in TAG_PREDICTOR:
        raise RuntimeError("invalid BPA descriptor")
    predictor = TAG_PREDICTOR[predictor_tag]
    direction, shift = _tag_basis(basis_tag, width * 8)
    start, end = _body_span(logical_size, width, alignment)
    payload = encoded[8:]
    shuffled = payload[start:end]
    based = _bitunshuffle_body(shuffled, width)
    predicted = _basis_inverse(based, width, direction, shift)
    body = _predict_inverse(predicted, width, predictor)
    raw = payload[:start] + body + payload[end:]
    if len(raw) != logical_size:
        raise RuntimeError("BPA inverse length mismatch")
    return raw


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _alignment_score(raw: bytes, width: int, alignment: int) -> float:
    """Cheap schema-blind alignment sketch: lower summed lane entropy is preferred."""
    sample = raw[:SCREEN_SAMPLE_BYTES]
    if len(sample) <= alignment + width * 8:
        return float("inf")
    start, end = _body_span(len(sample), width, alignment)
    body = sample[start:end]
    if not body:
        return float("inf")
    return sum(_entropy(body[lane::width]) for lane in range(width))


def rank_alignments(raw: bytes, width: int) -> list[int]:
    scored = [(_alignment_score(raw, width, alignment), alignment) for alignment in range(width)]
    scored.sort()
    return [alignment for score, alignment in scored[:MAX_ALIGNMENTS_PER_WIDTH] if math.isfinite(score)]


def _screen_size(transformed: bytes) -> int:
    compressed = G.zc(transformed, SCREEN_LEVEL)
    return min(len(transformed), len(compressed))


def audition(raw: bytes) -> dict:
    """Tournament BPA against the existing safe G0/G1/G2 Geometry incumbent.

    Only a small screened frontier receives full-node Zstd-19 pricing.  This is deliberately a research
    superoptimizer pattern: cheap observations prune the representation space; exact stored bytes remain the
    admission authority for finalists.
    """
    incumbent = G._encode_node(raw)
    result = {
        "kind": "geometry-incumbent",
        "payload": incumbent["payload"],
        "payload_bytes": int(incumbent["payload_bytes"]),
        "physical": incumbent["physical"],
        "incumbent_kind": incumbent["kind"],
        "saving_vs_incumbent_bytes": 0,
        "width": None,
        "alignment": None,
        "predictor": None,
        "basis": None,
        "screened_candidates": 0,
        "exact_finalists": 0,
    }
    if len(raw) < 16 * 1024 or len(raw) > MAX_NODE_BYTES:
        return result

    sample = raw[:SCREEN_SAMPLE_BYTES]
    screened: list[tuple[int, int, int, int, str, tuple[str, int]]] = []
    ordinal = 0
    for width in WORD_WIDTHS:
        for alignment in rank_alignments(raw, width):
            for predictor in PREDICTORS:
                for basis in _basis_options(width * 8):
                    try:
                        transformed = forward(sample, width, min(alignment, width - 1), predictor, basis)
                    except ValueError:
                        continue
                    if inverse(transformed, len(sample)) != sample:
                        raise RuntimeError("BPA screen candidate failed exact inverse")
                    screened.append((_screen_size(transformed), ordinal, width, alignment, predictor, basis))
                    ordinal += 1

    screened.sort(key=lambda row: (row[0], row[2], row[3], row[4], row[5]))
    finalists = screened[:MAX_EXACT_FINALISTS]
    for _, _, width, alignment, predictor, basis in finalists:
        transformed = forward(raw, width, alignment, predictor, basis)
        if inverse(transformed, len(raw)) != raw:
            raise RuntimeError("BPA finalist failed exact inverse")
        payload = G.zc(transformed, EXACT_LEVEL)
        if len(payload) >= len(transformed):
            payload = transformed
        saving = result["payload_bytes"] - len(payload)
        if saving < MIN_PAYLOAD_SAVING:
            continue
        if (len(payload), width, alignment, predictor, basis) < (
            result["payload_bytes"],
            result["width"] if result["width"] is not None else 1 << 30,
            result["alignment"] if result["alignment"] is not None else 1 << 30,
            result["predictor"] or "~",
            result["basis"] or ("~", 1 << 30),
        ):
            result = {
                "kind": "bitplane-algebra",
                "payload": payload,
                "payload_bytes": len(payload),
                "physical": transformed,
                "incumbent_kind": incumbent["kind"],
                "saving_vs_incumbent_bytes": int(incumbent["payload_bytes"]) - len(payload),
                "width": width,
                "alignment": alignment,
                "predictor": predictor,
                "basis": basis,
                "screened_candidates": len(screened),
                "exact_finalists": len(finalists),
            }
    result["screened_candidates"] = len(screened)
    result["exact_finalists"] = len(finalists)
    return result


RESOURCE_LIMITS = {
    "max_node_bytes": MAX_NODE_BYTES,
    "max_alignments_per_width": MAX_ALIGNMENTS_PER_WIDTH,
    "max_exact_finalists": MAX_EXACT_FINALISTS,
    "screen_sample_bytes": SCREEN_SAMPLE_BYTES,
    "screen_level": SCREEN_LEVEL,
    "exact_level": EXACT_LEVEL,
}
