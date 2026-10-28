from __future__ import annotations

"""Freeze the actual C25EG01 reader grammar used by the office/analytics winners.

A native reader should implement evidence, not a guessed superset.  This harness builds the exact dedicated
candidate on the two proven workloads, inventories every physical codec / reconstruction recipe / reference type /
inverse codec actually emitted, and then reads every public regular member through the bounded Python public
reader.  It also proves the internal filesystem manifest never leaks through the public namespace.

The output is a portability handoff, not native parity.  Production native/Android dispatch remains closed until a
Rust reader reproduces these bytes and passes hostile/recovery/platform gates.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_federated_candidate as CAND
from experiments import entropygraph_v030_federated_public as PUBLIC

TARGETS = ("02_office_workspace", "04_analytics_and_database")
KNOWN_RECIPES = {"plain", "zipstreams", "inflate_stream", "decode_file", "splice"}
KNOWN_REFS = {"slice", "whole"}
KNOWN_PACK_CODECS = {0, 1}


def _inventory(archive: Path) -> dict:
    with CAND._engine(Path(archive).resolve()):
        handle, meta, offsets = CAND.V25.open_ar()
        try:
            recipe_kinds = set()
            reference_kinds = set()
            inverse_codecs = set()
            inflate_methods = set()

            def refs(rows: list) -> None:
                for ref in rows:
                    if isinstance(ref, list) and ref:
                        reference_kinds.add(str(ref[0]))

            for _path, desc in meta.get("files", []):
                kind = str(desc[0])
                recipe_kinds.add(kind)
                if kind == "plain":
                    refs(desc[1])
                elif kind == "zipstreams":
                    refs(desc[1])
                elif kind == "inflate_stream":
                    inflate_methods.add(int(desc[3]))
                elif kind == "decode_file":
                    inverse_codecs.add(str(desc[2]))
                elif kind == "splice":
                    refs(desc[1])
            if meta.get("micro"):
                recipe_kinds.add("plain")
                reference_kinds.add("slice")

            pack_codecs = {int(row[1]) for row in offsets}
            pack_sizes = [int(row[2]) for row in offsets]
            return {
                "metadata_version": int(meta.get("v", -1)),
                "pack_count": len(offsets),
                "max_pack_uncompressed_bytes": max(pack_sizes, default=0),
                "pack_codecs": sorted(pack_codecs),
                "recipe_kinds": sorted(recipe_kinds),
                "reference_kinds": sorted(reference_kinds),
                "inverse_codecs": sorted(inverse_codecs),
                "inflate_methods": sorted(inflate_methods),
                "stream_slab_count": len(meta.get("stream_packs", [])),
                "micro_group_count": len(meta.get("micro", [])),
                "graph_file_rows": len(meta.get("files", [])),
                "authenticated_tree_sha256": str(meta.get("tree_sha256", "")),
            }
        finally:
            handle.close()


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg01-portability-", dir=work) as td:
        root = Path(td)
        archive = root / "candidate.cmpct"
        built = CAND.build(source, archive)
        grammar = _inventory(archive)
        public = PUBLIC.list_members(archive)
        public_paths = {row["path"] for row in public}
        if CAND.FS.FILESYSTEM_MANIFEST in public_paths:
            raise RuntimeError("federated internal filesystem manifest leaked into public listing")

        source_files = sorted(path for path in source.rglob("*") if path.is_file() and not path.is_symlink())
        checked = []
        max_amp = 1.0
        max_context = 0
        for path in source_files:
            rel = path.relative_to(source).as_posix()
            value, stats = PUBLIC.read_member_with_stats(archive, rel)
            expected = path.read_bytes()
            if value != expected or hashlib.sha256(value).digest() != hashlib.sha256(expected).digest():
                raise RuntimeError(f"federated public reader mismatch: {label}/{rel}")
            max_amp = max(max_amp, float(stats["amplification"]))
            max_context = max(max_context, int(stats["decoded_context_bytes"]))
            checked.append(rel)

        restored = root / "restored"
        PUBLIC.extract(archive, restored)
        if CAND._treehash(restored) != CAND._treehash(source):
            raise RuntimeError(f"federated public extraction tree mismatch: {label}")

        return {
            "label": label,
            "archive_bytes": int(built["archive_bytes"]),
            "canonical_user_tree_sha256": str(built["verified"]["canonical_user_tree_sha256"]),
            "grammar": grammar,
            "public_members": len(public),
            "regular_members_checked": len(checked),
            "max_observed_public_read_amplification": max_amp,
            "max_observed_public_read_context_bytes": max_context,
            "public_reader_exact": True,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg01_portability_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg01_portability_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    rows = [_one(f"neutral_hostile_v1/{name}", corpus / name, work_root) for name in TARGETS]
    recipes = sorted({value for row in rows for value in row["grammar"]["recipe_kinds"]})
    refs = sorted({value for row in rows for value in row["grammar"]["reference_kinds"]})
    inverse = sorted({value for row in rows for value in row["grammar"]["inverse_codecs"]})
    inflate = sorted({value for row in rows for value in row["grammar"]["inflate_methods"]})
    pack_codecs = sorted({value for row in rows for value in row["grammar"]["pack_codecs"]})

    gate = {
        "exact_target_count": len(rows) == 2,
        "metadata_v4_only": all(row["grammar"]["metadata_version"] == 4 for row in rows),
        "known_recipe_subset": set(recipes) <= KNOWN_RECIPES,
        "known_reference_subset": set(refs) <= KNOWN_REFS,
        "known_pack_codec_subset": set(pack_codecs) <= KNOWN_PACK_CODECS,
        "all_public_reads_exact": all(row["public_reader_exact"] for row in rows),
        "all_public_reads_le_8x": all(
            row["max_observed_public_read_amplification"] <= CAND.MAX_MEMBER_AMPLIFICATION for row in rows
        ),
        "all_physical_packs_le_8mib": all(
            row["grammar"]["max_pack_uncompressed_bytes"] <= CAND.MAX_DECODE_UNIT for row in rows
        ),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-federated-eg01-portability-inventory-v1",
        "rows": rows,
        "combined_inventory": {
            "recipe_kinds": recipes,
            "reference_kinds": refs,
            "inverse_codecs": inverse,
            "inflate_methods": inflate,
            "pack_codecs": pack_codecs,
        },
        "gate": gate,
        "claim_boundary": "Python public-reader + emitted-grammar inventory only; no native/Android/selector/release credit",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-portability-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-portability.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"combined_inventory": result["combined_inventory"], "gate": result["gate"]}, indent=2))
    if not result["gate"]["passed"]:
        raise SystemExit("federated C25EG01 portability inventory failed")


if __name__ == "__main__":
    main()
