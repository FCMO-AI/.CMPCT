"""Reference ONE block Statistical Law + Surprise realization.

This is deliberately a small scalar semantic authority, not a production coder.
It realizes a previous-byte adaptive KT Law with an exact deterministic 32-bit
integer arithmetic bitstream. Learned model state is reconstructed by the
reader and is never serialized.

The reader performs no discovery. It is given a block length and coded payload
and executes the same bounded Law.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

ALPHABET = 256
MAX_BLOCK_BYTES = 65_536
SAMPLE_BYTES = 4_096
SAMPLE_REJECT_RATIO = 0.97
BLOCK_FIXED_CHARGE_BYTES = 49
TOP = (1 << 32) - 1
HALF = 1 << 31
FIRST_QTR = 1 << 30
THIRD_QTR = FIRST_QTR * 3


class StatisticalLawError(ValueError):
    """Malformed/resource-invalid reference Statistical Law payload."""


@dataclass(frozen=True)
class BlockChoice:
    kind: str
    payload: bytes
    sample_bytes: int
    sample_kt_bits: float
    sample_payload_bytes: int
    sample_ratio: float
    stat_attempted: bool
    fixed_charge_bytes: int
    diagnostic_wire_bytes: int


class _BitWriter:
    __slots__ = ("buf", "acc", "nbits")

    def __init__(self) -> None:
        self.buf = bytearray()
        self.acc = 0
        self.nbits = 0

    def write(self, bit: int) -> None:
        self.acc = (self.acc << 1) | (bit & 1)
        self.nbits += 1
        if self.nbits == 8:
            self.buf.append(self.acc)
            self.acc = 0
            self.nbits = 0

    def finish(self) -> bytes:
        if self.nbits:
            self.acc <<= 8 - self.nbits
            self.buf.append(self.acc)
            self.acc = 0
            self.nbits = 0
        return bytes(self.buf)


class _BitReader:
    __slots__ = ("data", "byte_pos", "bit_pos")n
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.byte_pos = 0
        self.bit_pos = 0

    def read(self) -> int:
        # Arithmetic decoding convention: absent tail bits are zero. The
        # authenticated outer envelope separately binds declared payload
        # length, so truncation is rejected before/after semantic decode.
        if self.byte_pos >= len(self.data):
            return 0
        bit = (self.data[self.byte_pos] >> (7 - self.bit_pos)) & 1
        self.bit_pos += 1
        if self.bit_pos == 8:
            self.byte_pos += 1
            self.bit_pos = 0
        return bit


def _validate_length(length: int) -> None:
    if not 1 <= length <= MAX_BLOCK_BYTES:
        raise StatisticalLawError(
            f"block length {length} outside 1..{MAX_BLOCK_BYTES}"
        )


def kt_prequential_bits(source: bytes) -> float:
    """Exact KT-model codelength for analysis only, never an admission decision."""

    _validate_length(len(source))
    counts = [[0] * ALPHABET for _ in range(ALPHABET)]
    totals = [0] * ALPHABET
    bits = 8.0
    previous = source[0]
    for symbol in source[1:]:
        bits -= math.log2(
            (counts[previous][symbol] + 0.5) / (totals[previous] + 128.0)
        )
        counts[previous][symbol] += 1
        totals[previous] += 1
        previous = symbol
    return bits


def encode_block(block: bytes) -> bytes:
    """Encode one independently restartable non-empty block.

    Byte 0 is bootstrap Surprise. Remaining bytes are arithmetic-coded under
    the adaptive previous-byte KT Law. For symbol count n, integer weight is
    exactly ``2*n + 1``; total context weight is ``2*N + 256``.
    """

    _validate_length(len(block))
    first = block[0]
    if len(block) == 1:
        return bytes((first,))

    counts = [[0] * ALPHABET for _ in range(ALPHABET)]
    writer = _BitWriter()
    low = 0
    high = TOP
    pending = 0
    previous = first

    def emit(bit: int) -> None:
        nonlocal pending
        writer.write(bit)
        complement = 1 - bit
        while pending:
            writer.write(complement)
            pending -= 1

    for symbol in block[1:]:
        row = counts[previous]
        cumulative_low = symbol + 2 * sum(row[:symbol])
        symbol_weight = 2 * row[symbol] + 1
        total_weight = ALPHABET + 2 * sum(row)

        width = high - low + 1
        high = low + (width * (cumulative_low + symbol_weight) // total_weight) - 1
        low = low + (width * cumulative_low // total_weight)

        while True:
            if high < HALF:
                emit(0)
            elif low >= HALF:
                emit(1)
                low -= HALF
                high -= HALF
            elif low >= FIRST_QTR and high < THIRD_QTR:
                pending += 1
                low -= FIRST_QTR
                high -= FIRST_QTR
            else:
                break
            low = (low << 1) & TOP
            high = ((high << 1) | 1) & TOP

        row[symbol] += 1
        previous = symbol

    pending += 1
    emit(0 if low < FIRST_QTR else 1)
    return bytes((first,)) + writer.finish()


def choose_block_payload(block: bytes) -> BlockChoice:
    """Apply the preregistered deterministic gate and exact byte comparison."""

    _validate_length(len(block))
    sample = block[:SAMPLE_BYTES]
    # Admission uses the exact finalized integer bitstream, never float
    # codelength. kt_prequential_bits remains diagnostic information only.
    sample_payload = encode_block(sample)
    sample_bits = kt_prequential_bits(sample)
    sample_ratio = len(sample_payload) / len(sample)
    if sample_ratio >= SAMPLE_REJECT_RATIO:
        return BlockChoice(
            kind="surprise_raw",
            payload=block,
            sample_bytes=len(sample),
            sample_kt_bits=sample_bits,
            sample_payload_bytes=len(sample_payload),
            sample_ratio=sample_ratio,
            stat_attempted=False,
            fixed_charge_bytes=BLOCK_FIXED_CHARGE_BYTES,
            diagnostic_wire_bytes=BLOCK_FIXED_CHARGE_BYTES + len(block),
        )

    candidate = encode_block(block)
    if len(candidate) < len(block):
        kind = "stat_h1"
        payload = candidate
    else:
        kind = "surprise_raw"
        payload = block
    return BlockChoice(
        kind=kind,
        payload=payload,
        sample_bytes=len(sample),
        sample_kt_bits=sample_bits,
        sample_payload_bytes=len(sample_payload),
        sample_ratio=sample_ratio,
        stat_attempted=True,
        fixed_charge_bytes=BLOCK_FIXED_CHARGE_BYTES,
        diagnostic_wire_bytes=BLOCK_FIXED_CHARGE_BYTES + len(payload),
    )


def decode_block(payload: bytes, output_length: int) -> bytes:
    """Decode one block using only explicit payload + bounded Law state."""

    _validate_length(output_length)
    if not payload:
        raise StatisticalLawError("missing bootstrap byte")
    first = payload[0]
    if output_length == 1:
        return bytes((first,))

    reader = _BitReader(payload[1:])
    low = 0
    high = TOP
    code = 0
    for _ in range(32):
        code = ((code << 1) | reader.read()) & TOP

    counts = [[0] * ALPHABET for _ in range(ALPHABET)]
    out = bytearray((first,))
    previous = first

    for _ in range(output_length - 1):
        row = counts[previous]
        total_weight = ALPHABET + 2 * sum(row)
        width = high - low + 1
        scaled = ((code - low + 1) * total_weight - 1) // width

        cumulative = 0
        symbol = -1
        cumulative_high = 0
        for candidate, count in enumerate(row):
            weight = 2 * count + 1
            if scaled < cumulative + weight:
                symbol = candidate
                cumulative_high = cumulative + weight
                break
            cumulative += weight
        if symbol < 0:
            raise StatisticalLawError("arithmetic state outside model")

        high = low + (width * cumulative_high // total_weight) - 1
        low = low + (width * cumulative // total_weight)
        while True:
            if high < HALF:
                pass
            elif low >= HALF:
                code -= HALF
                low -= HALF
                high -= HALF
            elif low >= FIRST_QTR and high < THIRD_QTR:
                code -= FIRST_QTR
                low -= FIRST_QTR
                high -= FIRST_QTR
            else:
                break
            low = (low << 1) & TOP
            high = ((high << 1) | 1) & TOP
            code = ((code << 1) | reader.read()) & TOP

        row[symbol] += 1
        out.append(symbol)
        previous = symbol

    return bytes(out)


def decode_verified_block(
    payload: bytes,
    output_length: int,
    expected_sha256: bytes,
    *,
    declared_payload_length: int,
) -> bytes:
    """Envelope-level bounded decode with physical-length + logical digest checks."""

    if len(expected_sha256) != 32:
        raise StatisticalLawError("expected SHA-256 must be 32 bytes")
    if declared_payload_length != len(payload):
        raise StatisticalLawError("physical payload length mismatch")
    block = decode_block(payload, output_length)
    if hashlib.sha256(block).digest() != expected_sha256:
        raise StatisticalLawError("decoded block digest mismatch")
    return block
