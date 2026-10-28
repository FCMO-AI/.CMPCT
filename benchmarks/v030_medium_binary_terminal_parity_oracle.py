from __future__ import annotations

"""Exact frozen-row parity oracle for eliminating dominated r25 work on medium-binary families.

The r24-v4 S_PACK policy now makes the hostile false-neighbor and incompressible families both smaller and much
cheaper to build. The promoted product still constructs r25 before selecting r24 on those rows. This oracle does
*not* add a shortcut. It asks the prerequisite question with the full shipping implementations: for each target,
does direct locality-bounded r24 + mandatory strong verification publish exactly the same archive bytes and
logical tree as the complete release-product tournament?

A green result is evidence that the current r25 work is dominated on these frozen rows, not proof that every
future tree with a similar shape may skip r25. The output records only source-derived structural features so a
later admission rule can be tested against broader adversarial/generalization corpora without benchmark names.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from experiments import entropygraph_v030_release_product as P

TARGETS = ("02_false_neighbors", "05_incompressible")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _shape(root: Path) -> dict:
    sizes = []
    suffixes: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            st = os.lstat(path)
            if not stat.S_ISREG(st.st_mode):
                continue
            sizes.append(int(st.st_size))
            suffix = path.suffix.lower()
            suffixes[suffix] = suffixes.get(suffix, 0) + 1
    sizes.sort()
    return {
        "regular_files": len(sizes),
        "logical_bytes": sum(sizes),
        "min_regular_bytes": sizes[0] if sizes else 0,
        "max_regular_bytes": sizes[-1] if sizes else 0,
        "all_regular_at_most_256k": bool(sizes) and sizes[-1] <= 256 * 1024,
        "all_regular_at_least_32k": bool(sizes) and sizes[0] >= 32 * 1024,
        "suffix_counts": dict(sorted(suffixes.items())),
        "all_regular_bin": bool(sizes) and suffixes == {".bin": len(sizes)},
    }


def _verified_r24(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = P._locality_bounded_r24_build(root, out)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"direct r24 verification failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "build_s": build_s,
        "verify_s": verify_s,
        "complete_create_s": build_s + verify_s,
        "tree_sha256": verified.get("tree_sha256"),
        "release_byte_knobs": stats.get("release_byte_knobs"),
        "micro_pack_target_release_bytes": stats.get("micro_pack_target_release_bytes"),
        "micro_pack_max_file_release_bytes": stats.get("micro_pack_max_file_release_bytes"),
    }


def _verified_product(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = P.build(root, out)
    create_s = time.perf_counter() - started
    verified = P.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"release product verification failed: {verified!r}")
    return {
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "create_s": create_s,
        "tree_sha256": verified.get("tree_sha256"),
        "selected": stats.get("selected"),
        "format_profile": stats.get("format_profile"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "r25_attempted": stats.get("r25_attempted", True),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "hostile"
    HOSTILE.build(corpus)
    rows = []
    for name in TARGETS:
        root = corpus / name
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-medium-terminal-", dir=work_root) as td:
            work = Path(td)
            direct = _verified_r24(root, work / "direct-r24.cmpct")
            product = _verified_product(root, work / "product.cmpct")
        exact_archive_identity = (
            direct["archive_bytes"] == product["archive_bytes"]
            and direct["archive_sha256"] == product["archive_sha256"]
        )
        exact_tree_identity = direct["tree_sha256"] == product["tree_sha256"]
        row = {
            "label": f"resemblance_hostile_v1/{name}",
            "source_shape": _shape(root),
            "direct_verified_r24": direct,
            "full_release_product": product,
            "exact_archive_identity": exact_archive_identity,
            "exact_tree_identity": exact_tree_identity,
            "r25_wallclock_waste_s": max(0.0, float(product["create_s"]) - float(direct["complete_create_s"])),
            "full_product_selected_r24": str(product.get("selected", "")).startswith("r24"),
        }
        rows.append(row)
        print(json.dumps({"label": row["label"], "same_archive": exact_archive_identity, "waste_s": row["r25_wallclock_waste_s"]}, separators=(",", ":")), flush=True)

    gate = {
        "target_count": len(rows) == len(TARGETS),
        "all_exact_archive_identity": all(r["exact_archive_identity"] for r in rows),
        "all_exact_tree_identity": all(r["exact_tree_identity"] for r in rows),
        "all_full_product_selected_r24": all(r["full_product_selected_r24"] for r in rows),
        "all_shipping_r24_v4": all(r["direct_verified_r24"]["release_byte_knobs"] == "environment-independent-r24-v4" for r in rows),
    }
    gate["frozen_row_terminal_parity_proven"] = all(gate.values())
    return {
        "schema": "cmpct-v030-medium-binary-terminal-parity-oracle-v1",
        "contract": {
            "claim_boundary": "frozen-row exact parity only; does not authorize a generic terminal-r24 shortcut",
            "direct_boundary": "shipping locality-bounded r24 build + mandatory strong verification",
            "product_boundary": "complete promoted release-product build + strong verification",
            "required_identity": "archive bytes + archive sha256 + canonical semantic tree",
        },
        "rows": rows,
        "gate": gate,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-medium-terminal-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-medium-terminal-parity.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["gate"], indent=2), flush=True)
    if not result["gate"]["frozen_row_terminal_parity_proven"]:
        raise SystemExit("medium-binary terminal parity was not proven")


if __name__ == "__main__":
    main()
