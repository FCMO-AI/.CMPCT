from __future__ import annotations

"""Adversarial generalization proof for a medium-binary terminal-r24 fast path.

The frozen false-neighbor and incompressible rows proved that direct shipping r24-v4 can be byte-identical to the
complete r24/r25 product winner while avoiding >130 s of dominated r25 construction.  That result is not enough
to authorize a generic shortcut.  This harness builds deterministic *new* medium-binary trees that share only the
source-shape envelope and deliberately vary cross-file redundancy, entropy and shifted resemblance.

The proposed admission signal is conservative and source/product-derived rather than benchmark-named:
  * all entries are regular .bin files;
  * every member is 32 KiB..256 KiB;
  * at least 32 members;
  * shipping r24-v4 complete bytes are >= 84% of logical bytes.

The compression-ratio floor intentionally targets the expensive low-gain/high-entropy region where speculative
structure search is most likely to be dominated.  The harness does NOT promote the shortcut.  Promotion requires
that every admitted adversarial case publish archive-identical r24 bytes under the full product tournament; any
counterexample is durable evidence that the predicate is insufficient and must be tightened instead of waived.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import tempfile
import time

from experiments import entropygraph_v030_release_product as P

MIN_FILE = 32 * 1024
MAX_FILE = 256 * 1024
MIN_FILES = 32
R24_RATIO_FLOOR = 0.84


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_case(root: Path, mode: str, count: int, size: int, seed: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    base = bytes(rng.getrandbits(8) for _ in range(size))
    for i in range(count):
        if mode == "random":
            raw = bytes(rng.getrandbits(8) for _ in range(size + (i % 17)))
        elif mode == "false-neighbor":
            b = bytearray(base)
            # Sparse deterministic edits keep broad resemblance but poison naive whole-file matching.
            for j in range(0, len(b), 4096):
                b[j] ^= (i * 29 + j // 4096) & 0xFF
            raw = bytes(b)
        elif mode == "shifted":
            shift = (i * 257) % len(base)
            raw = base[shift:] + base[:shift]
        elif mode == "half-shared":
            tail = bytes(rng.getrandbits(8) for _ in range(size // 2))
            raw = base[: size // 2] + tail
        elif mode == "compressible-noise":
            raw = (b"CMPCT-v030-generalization-" * ((size // 27) + 1))[:size]
            b = bytearray(raw)
            for j in range(0, len(b), 8192):
                b[j] ^= (i + j // 8192) & 0xFF
            raw = bytes(b)
        else:
            raise ValueError(mode)
        (root / f"member-{i:04d}.bin").write_bytes(raw)


def _shape(root: Path) -> dict:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    sizes = [p.stat().st_size for p in files]
    return {
        "regular_files": len(files),
        "logical_bytes": sum(sizes),
        "min_regular_bytes": min(sizes) if sizes else 0,
        "max_regular_bytes": max(sizes) if sizes else 0,
        "all_bin": bool(files) and all(p.suffix.lower() == ".bin" for p in files),
    }


def _direct(root: Path, out: Path) -> dict:
    t0 = time.perf_counter()
    stats = P._locality_bounded_r24_build(root, out)
    build_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - t0
    if not verified.get("ok"):
        raise RuntimeError(f"r24 verify failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "tree_sha256": verified["tree_sha256"],
        "complete_create_s": build_s + verify_s,
        "release_byte_knobs": stats.get("release_byte_knobs"),
    }


def _product(root: Path, out: Path) -> dict:
    t0 = time.perf_counter()
    stats = P.build(root, out)
    create_s = time.perf_counter() - t0
    verified = P.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"product verify failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "tree_sha256": verified["tree_sha256"],
        "create_s": create_s,
        "selected": stats.get("selected"),
        "r25_attempted": stats.get("r25_attempted", True),
    }


def _eligible(shape: dict, direct: dict) -> bool:
    logical = int(shape["logical_bytes"])
    ratio = float(direct["archive_bytes"]) / max(1, logical)
    return (
        shape["regular_files"] >= MIN_FILES
        and shape["all_bin"]
        and shape["min_regular_bytes"] >= MIN_FILE
        and shape["max_regular_bytes"] <= MAX_FILE
        and ratio >= R24_RATIO_FLOOR
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    specs = (
        ("random-64x64k", "random", 64, 64 * 1024, 1101),
        ("random-96x128k", "random", 96, 128 * 1024, 1102),
        ("false-neighbor-96x64k", "false-neighbor", 96, 64 * 1024, 1201),
        ("shifted-64x96k", "shifted", 64, 96 * 1024, 1301),
        ("half-shared-64x96k", "half-shared", 64, 96 * 1024, 1401),
        ("compressible-negative-control", "compressible-noise", 48, 64 * 1024, 1501),
    )
    rows = []
    for label, mode, count, size, seed in specs:
        root = work_root / label
        _write_case(root, mode, count, size, seed)
        shape = _shape(root)
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-medium-generalization-", dir=work_root) as td:
            td = Path(td)
            direct = _direct(root, td / "direct.cmpct")
            product = _product(root, td / "product.cmpct")
        ratio = float(direct["archive_bytes"]) / max(1, int(shape["logical_bytes"]))
        admitted = _eligible(shape, direct)
        same_archive = direct["archive_bytes"] == product["archive_bytes"] and direct["archive_sha256"] == product["archive_sha256"]
        same_tree = direct["tree_sha256"] == product["tree_sha256"]
        row = {
            "label": label,
            "mode": mode,
            "shape": shape,
            "r24_archive_to_logical_ratio": ratio,
            "predicate_admitted": admitted,
            "direct_r24": direct,
            "full_product": product,
            "exact_archive_identity": same_archive,
            "exact_tree_identity": same_tree,
            "dominated_r25_wallclock_s": max(0.0, float(product["create_s"]) - float(direct["complete_create_s"])),
        }
        rows.append(row)
        print(json.dumps({"label": label, "admitted": admitted, "same_archive": same_archive, "ratio": ratio}, separators=(",", ":")), flush=True)

    admitted_rows = [r for r in rows if r["predicate_admitted"]]
    rejected_rows = [r for r in rows if not r["predicate_admitted"]]
    gate = {
        "case_count": len(rows) == len(specs),
        "has_admitted_generalization_cases": len(admitted_rows) >= 3,
        "has_rejected_negative_control": len(rejected_rows) >= 1,
        "all_trees_equal": all(r["exact_tree_identity"] for r in rows),
        "all_admitted_archive_identical": bool(admitted_rows) and all(r["exact_archive_identity"] for r in admitted_rows),
        "all_admitted_full_product_selected_r24": bool(admitted_rows) and all(str(r["full_product"].get("selected", "")).startswith("r24") for r in admitted_rows),
        "shipping_r24_v4": all(r["direct_r24"].get("release_byte_knobs") == "environment-independent-r24-v4" for r in rows),
    }
    gate["predicate_generalization_proven"] = all(gate.values())
    return {
        "schema": "cmpct-v030-medium-binary-terminal-generalization-v1",
        "contract": {
            "claim_boundary": "adversarial structural-predicate proof only; promotion still requires explicit product integration and full release rerun",
            "predicate": {
                "min_files": MIN_FILES,
                "suffix": ".bin",
                "min_file_bytes": MIN_FILE,
                "max_file_bytes": MAX_FILE,
                "min_r24_archive_to_logical_ratio": R24_RATIO_FLOOR,
            },
            "identity_requirement": "admitted cases must be byte/SHA-identical to the complete product winner",
            "negative_control_requirement": "at least one more-compressible medium-binary case must be rejected by the predicate",
        },
        "rows": rows,
        "gate": gate,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-medium-terminal-generalization-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-medium-terminal-generalization.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2), flush=True)
    if not result["gate"]["predicate_generalization_proven"]:
        raise SystemExit("medium-binary terminal predicate did not generalize safely")


if __name__ == "__main__":
    main()
