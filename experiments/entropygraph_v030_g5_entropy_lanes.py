"""CMPCT v0.30 production-candidate transform — G5 adaptive lane ordering.

G5 keeps the already-proven fixed byte-lane geometry but allows a content-nominated permutation of the
lane blocks before entropy coding.  The reader contract remains deliberately tiny: ``width`` plus a
bijective permutation and the logical size are sufficient to invert the transform.  File extension,
dtype, MIME, alignment folklore and semantic parsers never participate.

The writer may nominate at most two deterministic orders per existing lane width:

* entropy order: low empirical byte entropy first;
* histogram chain: start at the lowest-entropy lane, then greedily place the most byte-distribution-similar
  remaining lane next.

Footnote: the second nomination is writer-only search leverage, not a new grammar feature.  Both strategies
serialize to the same ``(width, permutation)`` descriptor; exact compressed bytes decide admission later.
Keeping search policy out of the reader lets future writers improve nomination without changing archives.
"""
from __future__ import annotations

from collections import Counter
import math

from experiments import entropygraph_v030_geometry as G

LANE_WIDTHS = tuple(G.LANE_WIDTHS)
MAX_WIDTH = max(LANE_WIDTHS)
MAX_NOMINATED_ORDERS_PER_WIDTH = 2


def _validate(width: int, permutation: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    if width not in LANE_WIDTHS:
        raise ValueError("unsupported G5 lane width")
    order = tuple(int(value) for value in permutation)
    if len(order) != width or sorted(order) != list(range(width)):
        raise ValueError("G5 lane permutation is not bijective")
    return order


def _lane_blocks(raw: bytes, width: int) -> tuple[list[bytes], bytes]:
    if width not in LANE_WIDTHS:
        raise ValueError("unsupported G5 lane width")
    full = len(raw) - (len(raw) % width)
    body = raw[:full]
    rows = full // width
    blocks = [body[lane:full:width] for lane in range(width)]
    if any(len(block) != rows for block in blocks):  # pragma: no cover - arithmetic invariant.
        raise RuntimeError("G5 lane block shape mismatch")
    return blocks, raw[full:]


def _entropy(block: bytes) -> float:
    if not block:
        return 0.0
    counts = Counter(block)
    total = len(block)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def entropy_order(raw: bytes, width: int) -> tuple[int, ...]:
    blocks, _ = _lane_blocks(raw, width)
    return tuple(sorted(range(width), key=lambda lane: (_entropy(blocks[lane]), lane)))


def _histogram(block: bytes) -> tuple[int, ...]:
    counts = [0] * 256
    for byte in block:
        counts[byte] += 1
    return tuple(counts)


def histogram_chain_order(raw: bytes, width: int) -> tuple[int, ...]:
    """Nominate one lane chain with similar byte distributions adjacent.

    Footnote: every complete lane has the same number of bytes, so raw L1 histogram distance is already
    normalized for this comparison.  The O(width^2 * 256) search is bounded by width<=16 and never appears
    in the decoder.  Stable lane-id tie breaks make the result deterministic across platforms.
    """
    blocks, _ = _lane_blocks(raw, width)
    hist = [_histogram(block) for block in blocks]
    entropies = [_entropy(block) for block in blocks]
    start = min(range(width), key=lambda lane: (entropies[lane], lane))
    order = [start]
    remaining = set(range(width)) - {start}
    while remaining:
        previous = order[-1]
        nxt = min(
            remaining,
            key=lambda lane: (
                sum(abs(left - right) for left, right in zip(hist[previous], hist[lane])),
                entropies[lane],
                lane,
            ),
        )
        order.append(nxt)
        remaining.remove(nxt)
    return tuple(order)


def nominated_orders(raw: bytes, width: int) -> tuple[tuple[int, ...], ...]:
    fixed = tuple(range(width))
    candidates = [entropy_order(raw, width), histogram_chain_order(raw, width)]
    unique: list[tuple[int, ...]] = []
    for order in candidates:
        _validate(width, order)
        if order == fixed or order in unique:
            continue
        unique.append(order)
        if len(unique) >= MAX_NOMINATED_ORDERS_PER_WIDTH:
            break
    return tuple(unique)


def forward(raw: bytes, width: int, permutation: tuple[int, ...] | list[int]) -> bytes:
    order = _validate(width, permutation)
    blocks, tail = _lane_blocks(raw, width)
    return b"".join(blocks[lane] for lane in order) + tail


def inverse(stored: bytes, width: int, permutation: tuple[int, ...] | list[int], logical_size: int) -> bytes:
    order = _validate(width, permutation)
    if logical_size < 0 or logical_size > G.MAX_CHUNK or len(stored) != logical_size:
        raise ValueError("invalid G5 logical-size descriptor")
    full = logical_size - (logical_size % width)
    rows = full // width
    body = stored[:full]
    tail = stored[full:]
    canonical = [b""] * width
    for physical_slot, lane in enumerate(order):
        start = physical_slot * rows
        end = start + rows
        canonical[lane] = body[start:end]
    out = bytearray(full)
    for lane, block in enumerate(canonical):
        if len(block) != rows:
            raise RuntimeError("G5 lane body shape mismatch")
        out[lane:full:width] = block
    out.extend(tail)
    return bytes(out)


RESOURCE_LIMITS = {
    "lane_widths": LANE_WIDTHS,
    "max_width": MAX_WIDTH,
    "max_nominated_orders_per_width": MAX_NOMINATED_ORDERS_PER_WIDTH,
    "max_logical_node_bytes": G.MAX_CHUNK,
}
