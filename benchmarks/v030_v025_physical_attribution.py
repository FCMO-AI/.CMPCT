from __future__ import annotations

"""Read-only physical attribution for the EntropyGraph-v0.25 gap behind v0.30.

Mission lock
------------
Genesis showed that the shipping v0.30 product is still materially larger than
v0.29 on office and analytics.  The current causal lead is not a missing Mosaic
selector but the research-only v0.25 representation to which the older research
portfolio fell back on those workloads.

This diagnostic does *not* change v0.25, v0.30, a format, or a selector.  It asks
one falsifiable question before any productization work:

    Is stream-backed reconstruction the dominant logical representation on both
    office and analytics, while being absent from a known non-stream control?

"Dominant" is intentionally structural rather than tuned: conservatively
stream-dependent recipes must cover a strict majority of logical file bytes.
The developer-repository control must use zero physical stream packs and zero
conservatively stream-dependent logical bytes.  A red hypothesis result is a
useful negative result, not a benchmark failure.

The tool rebuilds the frozen neutral corpus, normalizes each selected source,
builds the unchanged CMPNX5/v0.25 artifact, strong-verifies it, extracts it, and
then accounts every stored byte from the authenticated archive itself.  Physical
accounting is exact; logical stream coverage is conservative (splice hybrids are
not credited as stream bytes merely because one child may use a stream).
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25


TARGETS = ("02_office_workspace", "04_analytics_and_database")
NEGATIVE_CONTROL = "01_developer_repository"
WORKLOADS = (*TARGETS, NEGATIVE_CONTROL)


def _logical_len(desc: list) -> int:
    typ = desc[0]
    if typ == "plain":
        return int(desc[2])
    if typ == "zipstreams":
        return int(desc[4])
    if typ == "inflate_stream":
        return int(desc[4])
    if typ == "decode_file":
        return int(desc[3])
    if typ == "splice":
        return int(desc[4])
    raise ValueError(f"unknown v0.25 file recipe: {typ!r}")


def _pack_index_from_ref(ref: list) -> int:
    # Both current object reference forms carry pack index at position 1:
    # ["slice", pack_i, offset, length] or [kind, pack_i, length].
    return int(ref[1])


def _physical_attribution(archive: Path) -> dict:
    V25.OUT = archive
    f, meta, pack_offsets = V25.open_ar()
    try:
        # Read the primary compressed-metadata length directly from the physical
        # header.  open_ar() has already authenticated and decoded it.
        f.seek(0)
        header = f.read(V25.HDR.size)
        magic, primary_meta_cbytes, primary_meta_ubytes, pack_count, _ = V25.HDR.unpack(header)
        if magic != V25.MAG:
            raise RuntimeError("v0.25 attribution observed wrong physical magic")
        if int(pack_count) != len(pack_offsets):
            raise RuntimeError("v0.25 attribution pack-count drift")

        stream_pack_indices = {int(row[1]) for row in meta.get("stream_packs", [])}
        if len(stream_pack_indices) != len(meta.get("stream_packs", [])):
            raise RuntimeError("duplicate physical stream-pack index")

        pack_rows = []
        for index, (_off, codec, usize, csize, _crc, _sha) in enumerate(pack_offsets):
            payload = int(csize)
            physical = int(V25.PH.size) + payload
            pack_rows.append(
                {
                    "index": index,
                    "kind": "stream" if index in stream_pack_indices else "ordinary",
                    "codec": int(codec),
                    "uncompressed_bytes": int(usize),
                    "payload_bytes": payload,
                    "header_bytes": int(V25.PH.size),
                    "physical_bytes": physical,
                }
            )

        stream_physical = sum(row["physical_bytes"] for row in pack_rows if row["kind"] == "stream")
        ordinary_physical = sum(row["physical_bytes"] for row in pack_rows if row["kind"] == "ordinary")
        metadata_recovery_physical = (
            int(V25.HDR.size)
            + int(primary_meta_cbytes)
            + int(primary_meta_cbytes)
            + int(V25.FTR.size)
        )
        archive_bytes = archive.stat().st_size
        accounted = stream_physical + ordinary_physical + metadata_recovery_physical
        if accounted != archive_bytes:
            raise RuntimeError(f"physical-byte accounting mismatch: {accounted} != {archive_bytes}")

        # Rehydrate implicit micro-pack entries exactly as the reader does, but
        # remember their role before expansion so ordinary-pack attribution is
        # not flattened into an unhelpful single bucket.
        file_desc = dict(meta["files"])
        pack_roles: dict[int, set[str]] = defaultdict(set)
        for pack_i, entries in meta.get("micro", []):
            pi = int(pack_i)
            pack_roles[pi].add("micro")
            off = 0
            for path, n in entries:
                file_desc[path] = ["plain", [["slice", pi, off, int(n)]], int(n)]
                off += int(n)

        for _path, desc in file_desc.items():
            typ = desc[0]
            refs = None
            role = None
            if typ == "plain":
                refs, role = desc[1], "plain"
            elif typ == "zipstreams":
                refs, role = desc[1], "zip_skeleton"
            elif typ == "splice":
                refs, role = desc[1], "splice_residual"
            if refs is not None:
                for ref in refs:
                    pack_roles[_pack_index_from_ref(ref)].add(role)

        role_physical = Counter()
        role_pack_count = Counter()
        for row in pack_rows:
            if row["kind"] == "stream":
                continue
            roles = sorted(pack_roles.get(row["index"], {"unreferenced_or_internal"}))
            key = "+".join(roles)
            role_physical[key] += int(row["physical_bytes"])
            role_pack_count[key] += 1

        # Conservative logical attribution.  zipstreams and inflate_stream are
        # directly stream-backed.  decode_file inherits stream dependence from
        # its source.  splice recipes are deliberately *not* credited, because
        # only a child region may be stream-derived and full-file credit would
        # overstate the mechanism.
        memo_stream: dict[str, bool] = {}
        visiting: set[str] = set()

        def stream_dependent(path: str) -> bool:
            if path in memo_stream:
                return memo_stream[path]
            if path in visiting:
                raise RuntimeError("cycle while attributing v0.25 recipes")
            visiting.add(path)
            desc = file_desc[path]
            typ = desc[0]
            if typ in ("zipstreams", "inflate_stream"):
                value = True
            elif typ == "decode_file":
                value = stream_dependent(str(desc[1]))
            else:
                value = False
            visiting.remove(path)
            memo_stream[path] = value
            return value

        logical_by_recipe = Counter()
        stream_logical_bytes = 0
        stream_logical_files = 0
        for path, desc in file_desc.items():
            n = _logical_len(desc)
            logical_by_recipe[str(desc[0])] += n
            if stream_dependent(path):
                stream_logical_bytes += n
                stream_logical_files += 1

        logical_total = sum(_logical_len(desc) for desc in file_desc.values())
        if logical_total <= 0:
            stream_fraction = 0.0
        else:
            stream_fraction = stream_logical_bytes / logical_total

        # Slab dependency fan-out is informative for candidate locality.  This
        # reports dependent *file* bytes, not byte provenance, and is named that
        # way to prevent double-counting shared logical coverage as compression.
        stream_slabs = []
        for stream_offset, pack_i, stream_n in meta.get("stream_packs", []):
            pi = int(pack_i)
            row = pack_rows[pi]
            so, sn = int(stream_offset), int(stream_n)
            se = so + sn
            dependent_paths = []
            dependent_file_bytes = 0
            for path, desc in file_desc.items():
                ranges = []
                if desc[0] == "zipstreams":
                    ranges = [(int(o), int(n)) for o, n in desc[3]]
                elif desc[0] == "inflate_stream":
                    ranges = [(int(desc[1]), int(desc[2]))]
                if any(max(so, o) < min(se, o + n) for o, n in ranges):
                    dependent_paths.append(path)
                    dependent_file_bytes += _logical_len(desc)
            stream_slabs.append(
                {
                    "stream_offset": so,
                    "stream_uncompressed_bytes": sn,
                    "pack_index": pi,
                    "pack_physical_bytes": int(row["physical_bytes"]),
                    "dependent_file_count": len(dependent_paths),
                    "dependent_file_logical_bytes": dependent_file_bytes,
                }
            )

        recipe_counts = Counter(desc[0] for desc in file_desc.values())
        return {
            "archive_bytes": archive_bytes,
            "physical": {
                "stream_pack_bytes": stream_physical,
                "ordinary_pack_bytes": ordinary_physical,
                "metadata_recovery_framing_bytes": metadata_recovery_physical,
                "stream_pack_count": len(stream_pack_indices),
                "ordinary_pack_count": len(pack_rows) - len(stream_pack_indices),
                "primary_metadata_compressed_bytes": int(primary_meta_cbytes),
                "primary_metadata_uncompressed_bytes": int(primary_meta_ubytes),
                "ordinary_pack_role_physical_bytes": dict(sorted(role_physical.items())),
                "ordinary_pack_role_counts": dict(sorted(role_pack_count.items())),
                "accounting_exact": accounted == archive_bytes,
            },
            "logical": {
                "recipe_file_counts": dict(sorted(recipe_counts.items())),
                "recipe_logical_bytes": dict(sorted(logical_by_recipe.items())),
                "conservative_stream_dependent_files": stream_logical_files,
                "conservative_stream_dependent_logical_bytes": stream_logical_bytes,
                "represented_logical_bytes": logical_total,
                "conservative_stream_logical_fraction": stream_fraction,
            },
            "stream_slabs": stream_slabs,
            "metadata_version": int(meta["v"]),
            "authenticated_tree_sha256": str(meta["tree_sha256"]),
        }
    finally:
        f.close()


def _measure_one(name: str, source: Path, work_root: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"cmpct-v025-attribution-{name}-", dir=work_root) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized-root")
        expected_tree = V25.treehash(stage)
        logical_bytes = sum(p.stat().st_size for p in stage.rglob("*") if p.is_file())
        file_count = sum(1 for p in stage.rglob("*") if p.is_file())
        archive = root / "candidate.cmpnx5"

        V25.ROOT = stage
        V25.OUT = archive
        started = time.perf_counter()
        build_stats = dict(V25.build())
        build_wall_s = time.perf_counter() - started

        started = time.perf_counter()
        verified = dict(V25.strong_verify())
        strong_verify_wall_s = time.perf_counter() - started
        if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
            raise RuntimeError(f"v0.25 strong verification mismatch for {name}: {verified!r}")

        extracted = root / "out"
        started = time.perf_counter()
        V25.extract(extracted)
        extract_wall_s = time.perf_counter() - started
        extracted_tree = V25.treehash(extracted)
        if extracted_tree != expected_tree:
            raise RuntimeError(f"v0.25 extracted tree mismatch for {name}: {extracted_tree} != {expected_tree}")

        attribution = _physical_attribution(archive)
        if attribution["authenticated_tree_sha256"] != expected_tree:
            raise RuntimeError("attribution metadata tree identity drift")

        return {
            "workload": name,
            "file_count": file_count,
            "logical_bytes": logical_bytes,
            "tree_sha256": expected_tree,
            "archive_bytes": archive.stat().st_size,
            "build_wall_s": build_wall_s,
            "build_reported_create_s": float(build_stats["create_s"]),
            "strong_verify_wall_s": strong_verify_wall_s,
            "extract_wall_s": extract_wall_s,
            "build_stats": build_stats,
            "attribution": attribution,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_v025_physical_attribution_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_v025_physical_attribution_repair",
    )
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    rows = []
    for name in WORKLOADS:
        source = corpus / name
        if not source.is_dir():
            raise RuntimeError(f"missing frozen workload {name}")
        row = _measure_one(name, source, work_root)
        rows.append(row)
        print(
            json.dumps(
                {
                    "workload": name,
                    "archive_bytes": row["archive_bytes"],
                    "stream_pack_bytes": row["attribution"]["physical"]["stream_pack_bytes"],
                    "stream_logical_fraction": row["attribution"]["logical"]["conservative_stream_logical_fraction"],
                },
                separators=(",", ":"),
            ),
            flush=True,
        )

    by_name = {row["workload"]: row for row in rows}
    target_majority = {
        name: by_name[name]["attribution"]["logical"]["conservative_stream_logical_fraction"] > 0.5
        for name in TARGETS
    }
    control = by_name[NEGATIVE_CONTROL]
    control_stream_free = (
        control["attribution"]["physical"]["stream_pack_bytes"] == 0
        and control["attribution"]["logical"]["conservative_stream_dependent_logical_bytes"] == 0
    )
    accounting_exact = all(row["attribution"]["physical"]["accounting_exact"] for row in rows)
    hypothesis = {
        "office_stream_logical_majority": target_majority[TARGETS[0]],
        "analytics_stream_logical_majority": target_majority[TARGETS[1]],
        "developer_control_stream_free": control_stream_free,
        "physical_accounting_exact_all_rows": accounting_exact,
    }
    hypothesis["supported"] = all(hypothesis.values())

    return {
        "schema": "cmpct-v030-v025-physical-attribution-v1",
        "workloads": list(WORKLOADS),
        "rows": rows,
        "hypothesis": hypothesis,
        "claim_boundary": (
            "diagnostic attribution only; no release, selector, canonical-format, or shipping-v0.30 credit. "
            "Physical archive bytes are exact. Conservative stream logical coverage intentionally does not credit "
            "splice hybrids as wholly stream-derived. A red hypothesis is retained as a causal negative result."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-physical-attribution-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-v025-physical-attribution.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"hypothesis": result["hypothesis"]}, indent=2), flush=True)
    # Measurement integrity is fail-closed; the research hypothesis itself may
    # legitimately be false and must not turn the CI lane red.
    if not result["hypothesis"]["physical_accounting_exact_all_rows"]:
        raise SystemExit("v0.25 physical attribution accounting was not exact")


if __name__ == "__main__":
    main()
