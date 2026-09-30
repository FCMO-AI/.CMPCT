from __future__ import annotations

from experiments import entropygraph_v030_hierarchical_geometry as HG
from experiments import v030_hierarchical_bounded_screen_probe as PROBE


def _screen_order_reversal_hostile() -> bytes:
    """Held-out printable structure where level-6 and level-19 candidate ordering reverses."""
    bases = [
        bytes.fromhex("3f472e7d535e342c2923546746283d63"),
        bytes.fromhex("654f44372e423c247342433936484671"),
        bytes.fromhex("7e502c6e4c7652614037405d442c6747"),
        bytes.fromhex("21466a7b48623955576d45585a353e48"),
        bytes.fromhex("42262b265c71446365735d7a4c33773a"),
        bytes.fromhex("29553a72715944384e586c4a72683a4a"),
        bytes.fromhex("2d287b3e446b6f3f304b37465b24264e"),
        bytes.fromhex("7a2b45774a234a454a34745570782a46"),
    ]

    def enc94(value: int, width: int) -> bytes:
        out = bytearray(width)
        for index in range(width - 1, -1, -1):
            out[index] = 33 + (value % 94)
            value //= 94
        return bytes(out)

    rows = []
    for row in range(160):
        fields = []
        for column in range(8):
            value = (row * 2654435761 + column * 97531) & 0xFFFFFFFF
            fields.append(bases[column][:6] + enc94(value, 6) + enc94(row // 7, 4))
        rows.append(b"|".join(fields))
    return b"\n".join(rows)


def test_zero_threshold_guard_does_not_drop_exact_level19_winner() -> None:
    raw = _screen_order_reversal_hostile()
    assert len(raw) >= HG.MIN_NODE_BYTES

    incumbent = PROBE.audition(raw)
    assert incumbent["kind"] == "hierarchical"

    transformed = HG.hierarchy_forward(
        raw,
        int(incumbent["primary"]),
        int(incumbent["secondary"]),
        prefix_planes=bool(incumbent["prefix_planes"]),
    )

    assert HG._compressed_size(transformed, HG.SCREEN_LEVEL) >= HG._compressed_size(raw, HG.SCREEN_LEVEL)
    _base_codec, base_payload = HG.G._compress_physical(raw)
    assert len(base_payload) - int(incumbent["payload_bytes"]) >= HG.MIN_PAYLOAD_SAVING

    guarded = HG.audition(raw)
    assert guarded["payload_bytes"] <= incumbent["payload_bytes"]
