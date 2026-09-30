from __future__ import annotations

"""Diverse complete-artifact hostile for the G04 cross-level screen-order guard.

This is an adversarial generalization instrument, not a prevalence estimate. It fixes a small parameter
grid around the already-committed printable structure and includes every grid point rather than selecting
only observed losers. Guarded and exact-top-three control complete artifacts still run in separate
interpreters through the sibling fresh-process harness.
"""

import hashlib
import json
from pathlib import Path
import shutil

from benchmarks.v030_g04_screen_order_complete_artifact_falsifier_fresh_process import run_arm


BASES = [
    bytes.fromhex("3f472e7d535e342c2923546746283d63"),
    bytes.fromhex("654f44372e423c247342433936484671"),
    bytes.fromhex("7e502c6e4c7652614037405d442c6747"),
    bytes.fromhex("21466a7b48623955576d45585a353e48"),
    bytes.fromhex("42262b265c71446365735d7a4c33773a"),
    bytes.fromhex("29553a72715944384e586c4a72683a4a"),
    bytes.fromhex("2d287b3e446b6f3f304b37465b24264e"),
    bytes.fromhex("7a2b45774a234a454a34745570782a46"),
]
MULTIPLIERS = (2654435761, 2246822519, 3266489917)
OFFSETS = (97531, 65537, 131071)
GROUP_DIVISORS = (7, 9, 11)
ROWS = 160


def enc94(value: int, width: int) -> bytes:
    out = bytearray(width)
    for index in range(width - 1, -1, -1):
        out[index] = 33 + (value % 94)
        value //= 94
    return bytes(out)


def variant(multiplier: int, offset: int, group_divisor: int) -> bytes:
    rows = []
    for row in range(ROWS):
        fields = []
        for column in range(8):
            value = (row * multiplier + column * offset) & 0xFFFFFFFF
            fields.append(BASES[column][:6] + enc94(value, 6) + enc94(row // group_divisor, 4))
        rows.append(b"|".join(fields))
    return b"\n".join(rows)


def source_identity(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode()
        raw = path.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
    return h.hexdigest()


def main() -> None:
    work = Path("benchmark-artifacts/g04-screen-order-diverse").resolve()
    shutil.rmtree(work, ignore_errors=True)
    root = work / "root"
    root.mkdir(parents=True)

    cases = []
    case_id = 0
    for multiplier in MULTIPLIERS:
        for offset in OFFSETS:
            for group_divisor in GROUP_DIVISORS:
                raw = variant(multiplier, offset, group_divisor)
                name = f"case-{case_id:02d}.bin"
                (root / name).write_bytes(raw)
                cases.append(
                    {
                        "file": name,
                        "multiplier": multiplier,
                        "offset": offset,
                        "group_divisor": group_divisor,
                        "raw_bytes": len(raw),
                        "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
                case_id += 1

    guarded = run_arm("guarded", root, work / "guarded.cmpct")
    control = run_arm("control", root, work / "exact-top3-control.cmpct")
    if guarded["tree_sha256"] != control["tree_sha256"]:
        raise RuntimeError("diverse hostile arm tree identity mismatch")

    final_delta = int(guarded["archive_bytes"]) - int(control["archive_bytes"])
    overlay_delta = int(guarded["overlay_bytes"]) - int(control["overlay_bytes"])
    result = {
        "schema": "cmpct-v030-g04-screen-order-diverse-bundle-v1",
        "source_tree_sha256": source_identity(root),
        "case_count": len(cases),
        "logical_bytes": sum(int(row["raw_bytes"]) for row in cases),
        "cases": cases,
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
        "selection_note": "all 3x3x3 preregistered perturbation cells included; no post-measurement loser filtering",
    }
    out = Path("benchmark-artifacts/g04-screen-order-diverse-bundle.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
