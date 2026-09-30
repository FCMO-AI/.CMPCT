from __future__ import annotations

"""Fresh-process complete-artifact A/B for the G04 screen-order reversal hostile.

This is a stricter evidence form of the committed in-process falsifier. Each arm imports and builds in
its own interpreter, so module mutation, cached compressor state, or build-order warmth cannot make the
byte/selection comparison look equal or different. It is research evidence only; it does not alter the
frozen product gate or grant release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

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


def run_arm(arm: str, root: Path, archive: Path) -> dict:
    code = r"""
import hashlib, json, sys
from pathlib import Path
from experiments import entropygraph_v030_geometry_overlay_g04_publish as G04
from experiments import v030_hierarchical_bounded_screen_probe as PROBE

arm, root_s, archive_s = sys.argv[1:4]
root = Path(root_s)
archive = Path(archive_s)
if arm == "control":
    G04.G.HG.audition = PROBE.audition
elif arm != "guarded":
    raise SystemExit(f"unknown arm {arm}")

stats = G04.build(root, archive)
verify = G04.strong_verify(archive)
expected_tree = G04.treehash(root)
if not verify.get("ok") or verify.get("tree_sha256") != expected_tree:
    raise RuntimeError(f"{arm} strong verification failed: {verify!r}")
keys = (
    "selected", "archive_bytes", "v029_bytes", "pre_overlay_graph_bytes", "overlay_bytes",
    "saving_vs_v029_bytes", "transformed_records", "lane_records", "delimiter_records",
    "hierarchical_records", "prefix_plane_records", "hierarchical_total_records",
    "hierarchical_incremental_saving_bytes", "tree_sha256",
)
out = {k: stats[k] for k in keys}
out["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
for k in keys:
    if k.endswith("bytes") or k.endswith("records"):
        out[k] = int(out[k])
print(json.dumps(out, sort_keys=True))
"""
    proc = subprocess.run(
        [sys.executable, "-c", code, arm, str(root), str(archive)],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = [line for line in proc.stdout.splitlines() if line.strip()]
    if not rows:
        raise RuntimeError(f"{arm} emitted no receipt")
    return json.loads(rows[-1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-screen-order-fresh-process"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-screen-order-fresh-process.json"))
    a = ap.parse_args()

    raw = hostile_bytes()
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != EXPECTED_RAW_SHA256:
        raise RuntimeError(f"hostile identity drift: {raw_sha}")

    work = a.work_root.resolve()
    shutil.rmtree(work, ignore_errors=True)
    root = work / "root"
    root.mkdir(parents=True)
    (root / "payload").write_bytes(raw)

    guarded = run_arm("guarded", root, work / "guarded.cmpct")
    control = run_arm("control", root, work / "exact-top3-control.cmpct")
    if guarded["tree_sha256"] != control["tree_sha256"]:
        raise RuntimeError("arm tree identity mismatch")

    final_delta = int(guarded["archive_bytes"]) - int(control["archive_bytes"])
    overlay_delta = int(guarded["overlay_bytes"]) - int(control["overlay_bytes"])
    result = {
        "schema": "cmpct-v030-g04-screen-order-complete-artifact-fresh-process-v2",
        "raw_bytes": len(raw),
        "raw_sha256": raw_sha,
        "guarded": guarded,
        "exact_top3_control": control,
        "final_archive_delta_guarded_minus_control": final_delta,
        "overlay_delta_guarded_minus_control": overlay_delta,
        "tree_identity_equal": True,
        "archive_identity_equal": guarded["archive_sha256"] == control["archive_sha256"],
        "decision": (
            "GUARD_COMPLETE_ARTIFACT_REGRESSION" if final_delta > 0
            else "FINAL_ARTIFACT_EQUAL_BUT_OVERLAY_HEADROOM_LOST" if final_delta == 0 and overlay_delta > 0
            else "NO_COMPLETE_OR_OVERLAY_REGRESSION_OBSERVED"
        ),
        "promotion_credit": False,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
