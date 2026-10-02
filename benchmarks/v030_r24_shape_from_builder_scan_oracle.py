from __future__ import annotations

"""Research oracle: prove canonical-r24 shape facts are already recoverable from Builder.scan.

This is not product code. It attacks the assumption that a positive shape-prewalk attribution
must reuse parent-process preflight facts. Parent facts can age before the child scans a mutable
source tree. The stronger candidate is child-local: Builder.scan already materializes one row
for every regular path (K_FILE or K_HARDLINK), including exact source size. If those rows recover
the mature _regular_user_shape facts, micro-pack locality can be derived after scan without a
second full filesystem metadata walk. Wide-single-file admission remains a separate pre-scan
question because CDC policy must be fixed before scan.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

from experiments import entropygraph_v030_release_product_base as BASE

B = BASE.R24_BUILDER_MODULE


def _mature(root: Path) -> tuple[int, int]:
    count, largest = BASE._regular_user_shape(root)
    return int(count), int(largest)


def _from_builder_scan(root: Path) -> tuple[int, int]:
    builder = BASE.C.Builder(root, deflate_reuse_min=BASE.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.scan()
    regular_rows = [row for row in builder.files if row[1] in (B.K_FILE, B.K_HARDLINK)]
    return len(regular_rows), max((int(row[4]) for row in regular_rows), default=0)


def _fixture(root: Path) -> dict:
    (root / "nested").mkdir(parents=True)
    (root / "a.txt").write_bytes(b"a" * 17)
    (root / "nested" / "b.bin").write_bytes(b"b" * 4097)
    (root / "hard-source.dat").write_bytes(b"h" * 211)
    hardlink = root / "hard-alias.dat"
    hardlink_status = "created"
    try:
        os.link(root / "hard-source.dat", hardlink)
    except OSError as exc:
        hardlink_status = f"unsupported:{type(exc).__name__}"
    symlink_status = "created"
    try:
        os.symlink("a.txt", root / "file-link")
        os.symlink("nested", root / "dir-link")
    except OSError as exc:
        symlink_status = f"unsupported:{type(exc).__name__}"
    fifo_status = "created"
    if hasattr(os, "mkfifo"):
        try:
            os.mkfifo(root / "named-pipe")
        except OSError as exc:
            fifo_status = f"unsupported:{type(exc).__name__}"
    else:
        fifo_status = "unsupported:no-mkfifo"
    return {
        "hardlink": hardlink_status,
        "symlink": symlink_status,
        "fifo": fifo_status,
    }


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-r24-scan-shape-") as td:
        root = Path(td) / "tree"
        root.mkdir()
        fixture = _fixture(root)
        mature = _mature(root)
        scanned = _from_builder_scan(root)
        if mature != scanned:
            raise RuntimeError(f"scan-derived shape mismatch: mature={mature} scanned={scanned}")
        return {
            "schema": "cmpct-v030-r24-shape-from-builder-scan-oracle-v1",
            "authority_head": "496c96b40e09b6cd9a4eb81af2ec52db1caed354",
            "fixture": fixture,
            "mature_regular_user_shape": {
                "regular_files": mature[0],
                "largest_regular_bytes": mature[1],
            },
            "builder_scan_derived_shape": {
                "regular_files": scanned[0],
                "largest_regular_bytes": scanned[1],
            },
            "match": True,
            "implication": (
                "A positive prewalk attribution need not send stale parent-process shape scalars. "
                "The child can derive count/largest from its already-required Builder.scan rows. "
                "This proves information availability only; it does not yet solve pre-scan wide-single-file CDC admission."
            ),
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-shape-from-builder-scan-oracle.json"),
    )
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
