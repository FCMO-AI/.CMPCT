from __future__ import annotations

"""Focused causality proof for the v0.30 r24 nested-container locality repair.

The frozen deflate-family workload contains 14 nested ZIP bundles. Mature r24 deliberately stores 8+ nested
containers as slices of one solid ``S_PACK`` blob. That is excellent for size but causes one selected ZIP read to
decode the entire 14-ZIP cohort. v0.30 cannot publish such a representation because member-read amplification is
frozen at <=8x.

This oracle builds the exact same source twice:
- generic/historical Builder policy, which must remain unchanged and reproduce the oversized cohort;
- promoted shipping-r24 policy, which must use the same r24 grammar while splitting that cohort into bounded packs.

Both artifacts are strongly verified. Locality is measured through actual public ``CMPCT.read`` calls while
tracking every decoded physical blob. The result preserves the byte cost of the repair rather than hiding it.
"""

import argparse
import json
from pathlib import Path
import shutil

from cmpct.builder import Builder
from cmpct.codec import K_FILE, S_PACK
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product as PRODUCT
from benchmarks import resemblance_hostile_corpus_v1 as CORPUS


def _pack_count(archive: Path) -> int:
    with CMPCT(archive) as reader:
        return len({
            bytes(row[6][1])
            for row in reader.files
            if row[1] == K_FILE and row[6] and row[6][0] == S_PACK
        })


def _all_member_locality(archive: Path) -> dict:
    class Tracking(CMPCT):
        def __init__(self, path):
            super().__init__(path)
            self.observed: set[int] = set()
        def _blob(self, idx):
            self.observed.add(int(idx))
            return super()._blob(idx)

    rows = []
    with Tracking(archive) as reader:
        verified_files = reader.verify()
        for row in reader.files:
            if row[1] != K_FILE:
                continue
            rel, _kind, _mode, _mtime, size, _digest, _storage = row
            reader.observed.clear()
            raw = bytes(reader.read(rel))
            if len(raw) != int(size):
                raise RuntimeError(f"r24 read length drift for {rel!r}")
            decoded = sum(int(reader.blobs[idx][1]) for idx in reader.observed)
            amp = max(len(raw), decoded) / max(1, len(raw))
            rows.append({
                "path": rel,
                "logical_bytes": len(raw),
                "decoded_context_bytes": decoded,
                "amplification": amp,
            })
    return {
        "verified_files": verified_files,
        "rows": rows,
        "max_amplification": max((row["amplification"] for row in rows), default=0.0),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    historical_tree = CORPUS.tree_hash(source)

    historical = work_root / "historical-r24.cmpct"
    shipping = work_root / "shipping-r24.cmpct"

    Builder(source).build(historical)
    shipping_stats = PRODUCT._locality_bounded_r24_build(source, shipping)

    historical_locality = _all_member_locality(historical)
    shipping_locality = _all_member_locality(shipping)
    shipping_verify = PRODUCT.strong_verify(shipping)
    expected_product_tree = PRODUCT.treehash(source)

    result = {
        "schema": "cmpct-v030-r24-nested-container-locality-v1",
        "claim_boundary": "shipping r24 encoder grouping only; no grammar/reader/threshold change",
        "workload": "resemblance_hostile_v1/04_deflate_family",
        "historical_tree_sha256": historical_tree,
        "product_tree_sha256": expected_product_tree,
        "historical": {
            "archive_bytes": historical.stat().st_size,
            "pack_count": _pack_count(historical),
            **historical_locality,
        },
        "shipping": {
            "archive_bytes": shipping.stat().st_size,
            "pack_count": _pack_count(shipping),
            "release_byte_knobs": shipping_stats.get("release_byte_knobs"),
            **shipping_locality,
            "strong_verify": shipping_verify,
        },
    }
    result["byte_delta_shipping_vs_historical"] = result["shipping"]["archive_bytes"] - result["historical"]["archive_bytes"]
    result["gate"] = {
        "historical_reproduces_single_pack": result["historical"]["pack_count"] == 1,
        "historical_reproduces_over_8x": result["historical"]["max_amplification"] > 8.0,
        "shipping_splits_pack": result["shipping"]["pack_count"] >= 2,
        "shipping_all_members_le_8x": result["shipping"]["max_amplification"] <= 8.0,
        "shipping_strong_verify": bool(shipping_verify.get("ok")) and shipping_verify.get("tree_sha256") == expected_product_tree,
        "same_verified_file_count": result["shipping"]["verified_files"] == result["historical"]["verified_files"],
    }
    result["gate"]["passed"] = all(result["gate"].values())
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-container-locality-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-container-locality.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"historical": result["historical"], "shipping": result["shipping"], "byte_delta": result["byte_delta_shipping_vs_historical"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("r24 nested-container locality causality gate failed")


if __name__ == "__main__":
    main()
