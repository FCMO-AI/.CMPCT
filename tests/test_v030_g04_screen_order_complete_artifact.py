from __future__ import annotations

from experiments import entropygraph_v030_geometry_overlay_g04_publish as G04
from experiments import v030_hierarchical_bounded_screen_probe as PROBE


def _hostile() -> bytes:
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


def test_zero_threshold_guard_does_not_regress_complete_artifact(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "payload").write_bytes(_hostile())

    guarded_path = tmp_path / "guarded.cmpct"
    control_path = tmp_path / "exact-top3-control.cmpct"
    original = G04.G.HG.audition

    guarded = G04.build(root, guarded_path)
    try:
        G04.G.HG.audition = PROBE.audition
        control = G04.build(root, control_path)
    finally:
        G04.G.HG.audition = original

    expected_tree = G04.treehash(root)
    assert G04.strong_verify(guarded_path)["tree_sha256"] == expected_tree
    assert G04.strong_verify(control_path)["tree_sha256"] == expected_tree
    assert int(guarded["archive_bytes"]) <= int(control["archive_bytes"])
