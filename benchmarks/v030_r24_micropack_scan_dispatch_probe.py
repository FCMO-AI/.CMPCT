from __future__ import annotations

"""Isolate why a zero-group LocalityDerivedBuilder changes deflate-family scan state.

A class x micro_pack_max_file matrix separates constructor/policy state from dynamic
dispatch.  The probe also seals the actually loaded builder source path+hash so an
editable-install/source leak cannot masquerade as product evidence.
"""

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import shutil

from benchmarks import resemblance_hostile_corpus_v1 as RESEMBLANCE
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from cmpct import builder as BUILDER
from experiments import entropygraph_v030_release_product as PRODUCT


def snapshot(b: BUILDER.Builder) -> dict:
    return {
        "candidate_count": len(b.cands),
        "candidates": [
            {
                "sha256": bytes(h).hex(),
                "raw_bytes": len(c.raw),
                "hints": sorted(str(x) for x in c.hints),
                "deflates": len(c.deflates),
            }
            for h, c in sorted(b.cands.items())
        ],
        "storage_counts": {
            str(tag): sum(1 for row in b.files if (("none" if not row[6] else str(int(row[6][0]))) == str(tag)))
            for tag in sorted({"none" if not row[6] else str(int(row[6][0])) for row in b.files})
        },
        "file_rows": len(b.files),
    }


def one(source: Path, cls, micro_max: int) -> dict:
    b = cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(micro_max)
    b.scan()
    return snapshot(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-scan-dispatch-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-scan-dispatch.json"))
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    root = args.work_root / "corpus"
    manifest = RESEMBLANCE.build(root)
    source = root / "04_deflate_family"
    release_max = int(PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)

    builder_path = Path(inspect.getsourcefile(BUILDER) or BUILDER.__file__).resolve()
    loaded_hash = hashlib.sha256(builder_path.read_bytes()).hexdigest()
    cases = {
        "base_zero": one(source, BUILDER.Builder, 0),
        "base_release": one(source, BUILDER.Builder, release_max),
        "derived_zero": one(source, BASE.LocalityDerivedBuilder, 0),
        "derived_release": one(source, BASE.LocalityDerivedBuilder, release_max),
    }
    sigs = {k: [(x["sha256"], x["raw_bytes"], tuple(x["hints"])) for x in v["candidates"]] for k, v in cases.items()}
    result = {
        "schema": "cmpct-v030-r24-scan-dispatch-probe-v1",
        "release_credit": False,
        "builder_source_path": str(builder_path),
        "builder_source_sha256": loaded_hash,
        "builder_scan_owner": BUILDER.Builder.scan.__qualname__,
        "derived_scan_owner": BASE.LocalityDerivedBuilder.scan.__qualname__,
        "release_micro_max_file": release_max,
        "identity": next(x for x in manifest["workloads"] if x["name"] == "04_deflate_family"),
        "cases": cases,
        "same_base_across_max": sigs["base_zero"] == sigs["base_release"],
        "same_derived_across_max": sigs["derived_zero"] == sigs["derived_release"],
        "same_class_at_zero": sigs["base_zero"] == sigs["derived_zero"],
        "same_class_at_release": sigs["base_release"] == sigs["derived_release"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
