from __future__ import annotations

"""Complete-artifact A/B for the G04 level-6 screen-order reversal hostile.

Research-only evidence instrument. It compares the current productized zero-threshold
HG audition against the historical exact-top-three bounded-screen control while holding
the complete G0-G4 builder, input tree, archive grammar, verification, and final v0.29
tournament constant.
"""

import hashlib
import json
from pathlib import Path
import tempfile

from experiments import entropygraph_v030_geometry_overlay_g04_publish as G04
from experiments import v030_hierarchical_bounded_screen_probe as PROBE


EXPECTED_RAW_SHA256 = "78909dd8934217ac33a2634d5f62a7f75b57e77860a888ccc61df5d2648457ec"


def hostile_bytes() -> bytes:
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


def _summary(stats: dict) -> dict:
    return {
        "selected": stats["selected"],
        "archive_bytes": int(stats["archive_bytes"]),
        "v029_bytes": int(stats["v029_bytes"]),
        "pre_overlay_graph_bytes": int(stats["pre_overlay_graph_bytes"]),
        "overlay_bytes": int(stats["overlay_bytes"]),
        "saving_vs_v029_bytes": int(stats["saving_vs_v029_bytes"]),
        "transformed_records": int(stats["transformed_records"]),
        "lane_records": int(stats["lane_records"]),
        "delimiter_records": int(stats["delimiter_records"]),
        "hierarchical_records": int(stats["hierarchical_records"]),
        "prefix_plane_records": int(stats["prefix_plane_records"]),
        "hierarchical_total_records": int(stats["hierarchical_total_records"]),
        "hierarchical_incremental_saving_bytes": int(stats["hierarchical_incremental_saving_bytes"]),
        "tree_sha256": stats["tree_sha256"],
    }


def main() -> None:
    raw = hostile_bytes()
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != EXPECTED_RAW_SHA256:
        raise RuntimeError(f"hostile identity drift: {raw_sha}")

    with tempfile.TemporaryDirectory(prefix="cmpct-g04-screen-order-complete-") as td:
        work = Path(td)
        root = work / "root"
        root.mkdir()
        (root / "payload").write_bytes(raw)

        guarded_path = work / "guarded.cmpct"
        control_path = work / "exact-top3-control.cmpct"

        original_audition = G04.G.HG.audition
        guarded_stats = G04.build(root, guarded_path)
        guarded_verify = G04.strong_verify(guarded_path)

        try:
            G04.G.HG.audition = PROBE.audition
            control_stats = G04.build(root, control_path)
            control_verify = G04.strong_verify(control_path)
        finally:
            G04.G.HG.audition = original_audition

        expected_tree = G04.treehash(root)
        for label, verify in (("guarded", guarded_verify), ("control", control_verify)):
            if not verify.get("ok") or verify.get("tree_sha256") != expected_tree:
                raise RuntimeError(f"{label} complete artifact failed strong verification")

        guarded = _summary(guarded_stats)
        control = _summary(control_stats)
        result = {
            "schema": "cmpct-v030-g04-screen-order-complete-artifact-v1",
            "raw_bytes": len(raw),
            "raw_sha256": raw_sha,
            "guarded": guarded,
            "exact_top3_control": control,
            "final_archive_delta_guarded_minus_control": guarded["archive_bytes"] - control["archive_bytes"],
            "overlay_delta_guarded_minus_control": guarded["overlay_bytes"] - control["overlay_bytes"],
            "tree_identity_equal": guarded["tree_sha256"] == control["tree_sha256"] == expected_tree,
            "decision": (
                "GUARD_COMPLETE_ARTIFACT_REGRESSION"
                if guarded["archive_bytes"] > control["archive_bytes"]
                else "FINAL_ARTIFACT_EQUAL_BUT_OVERLAY_HEADROOM_LOST"
                if guarded["archive_bytes"] == control["archive_bytes"] and guarded["overlay_bytes"] > control["overlay_bytes"]
                else "NO_COMPLETE_OR_OVERLAY_REGRESSION_OBSERVED"
            ),
        }
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
