from __future__ import annotations

"""Candidate-owned r24 prebuild worker for the compact-policy product replication.

The historical #209 launcher rebound the candidate only in its parent interpreter, while shipping
r24 bytes are produced by a fresh child that imported canonical product source. This worker makes
candidate identity explicit at that byte-owning boundary without changing canonical release code.
"""

import argparse
import json
from pathlib import Path


def _worker(root: Path, out: Path) -> None:
    from experiments import entropygraph_v030_release_product_compact_r24 as product

    stats = product._locality_bounded_r24_build(Path(root), Path(out))

    declared_policy = {
        "candidate": product.PRODUCT_CANDIDATE,
        "deflate_reuse_min_bytes": int(product.R24_COMPACT_DEFLATE_REUSE_MIN_BYTES),
        "medium_binary_packing": bool(product.R24_COMPACT_MEDIUM_BINARY_PACKING),
        "medium_terminal": bool(product.R24_COMPACT_MEDIUM_TERMINAL),
    }
    expected_declared = {
        "candidate": "v030-compact-r24-release-policy-v1",
        "deflate_reuse_min_bytes": 64 * 1024,
        "medium_binary_packing": False,
        "medium_terminal": False,
    }

    # Attest the actual release-base objects and build receipt that owned these bytes. Candidate
    # declarations alone are not sufficient custody: the fresh subprocess could otherwise report
    # intended metadata while Builder-visible globals/callables drift back to canonical policy.
    base = product._BASE
    hints = base.R24_BUILDER_MODULE.TEXT_EXT
    effective_policy = {
        "candidate": product.PRODUCT_CANDIDATE,
        "deflate_reuse_min_bytes": int(base.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES),
        "build_reported_deflate_reuse_min_bytes": int(stats["deflate_reuse_min_release_bytes"]),
        "micro_pack_max_file_release_bytes": int(stats["micro_pack_max_file_release_bytes"]),
        "builder_text_ext_is_release_view": isinstance(hints, base._ReleaseTextHints),
        "medium_binary_packing": base.R24_RELEASE_MEDIUM_BINARY_EXT in hints,
        "hints_equal_original": set(hints) == set(base._R24_ORIGINAL_TEXT_EXT),
        "medium_terminal_disabled": (
            base._build_medium_binary_terminal_if_eligible is product._no_medium_terminal
            and product._PRODUCT._build_medium_binary_terminal_if_eligible is product._no_medium_terminal
        ),
    }
    expected_effective = {
        "candidate": "v030-compact-r24-release-policy-v1",
        "deflate_reuse_min_bytes": 64 * 1024,
        "build_reported_deflate_reuse_min_bytes": 64 * 1024,
        "micro_pack_max_file_release_bytes": 256 * 1024,
        "builder_text_ext_is_release_view": True,
        "medium_binary_packing": False,
        "hints_equal_original": True,
        "medium_terminal_disabled": True,
    }
    if declared_policy != expected_declared or effective_policy != expected_effective:
        Path(out).unlink(missing_ok=True)
        raise RuntimeError(
            f"compact r24 child policy mismatch: declared={declared_policy!r} effective={effective_policy!r}"
        )

    print(
        json.dumps(
            {
                "schema": "cmpct-v030-r24-prebuild-process-v1",
                "stats": {
                    **dict(stats),
                    "r24_prebuild_candidate_policy": declared_policy,
                    "r24_prebuild_effective_policy": effective_policy,
                },
                "policy": declared_policy,
                "effective_policy": effective_policy,
            },
            separators=(",", ":"),
            default=str,
        )
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--root", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    if not a.worker or a.root is None or a.out is None:
        p.error("worker mode requires --root and --out")
    _worker(a.root, a.out)


if __name__ == "__main__":
    main()
