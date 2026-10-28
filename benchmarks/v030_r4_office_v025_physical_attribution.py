from __future__ import annotations

"""Source-sealed physical attribution of the inherited v0.25 Office floor.

Mission lock
============
Page-seed materialization proved that the SFV4 Office representation can satisfy the
fixed 4 KiB / 8x selective-read law (1800/1800 exact, 0 locality violations, 2.162x
worst charged amplification), but the complete diagnostic candidate remains 676,891 B
larger than frozen v0.29.  The seed frames themselves cost only 38,402 B, so locality
metadata cannot explain the underlying 638,489 B pre-locality SFV4 deficit.

Falsifiable hypothesis H-ATTR: on the *same repaired Office tree*, exact physical
accounting of the inherited frozen v0.25 archive and current SFV4 bundle will localize
most of that pre-locality deficit to one bounded representation family (stream slabs,
non-stream packing/base, ZIP skeleton/residual, or control/auth metadata).  Disprove if
physical roles do not sum byte-exactly to their archives, the frozen source seal fails,
tree identity/reconstruction differs, or no role-level concentration is visible.

This is a referee only.  It changes no archive selector, format, thresholds or release
surface.  The historical contender executes its own frozen experiment source, and the
worker fails closed on checkout SHA and module provenance.
"""

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

SCHEMA = "cmpct-v030-r4-office-v025-physical-attribution-v1"
FROZEN_V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
ACCEPTED_V029_OFFICE = 5_954_026


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _git_head(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def _ref_pack_ids(refs: list) -> set[int]:
    out: set[int] = set()
    for r in refs:
        if not isinstance(r, (list, tuple)) or len(r) < 2 or r[0] not in ("slice", "whole"):
            raise RuntimeError(f"unexpected v0.25 object reference: {r!r}")
        out.add(int(r[1]))
    return out


def _frozen_worker(checkout: Path, source: Path, archive: Path, output: Path) -> None:
    checkout = checkout.resolve()
    source = source.resolve()
    archive = archive.resolve()
    if _git_head(checkout) != FROZEN_V029_SHA:
        raise RuntimeError("frozen v0.29 checkout SHA mismatch")
    module_path = (checkout / "experiments" / "entropygraph_v025.py").resolve()
    if not module_path.is_file() or not _within(module_path, checkout):
        raise RuntimeError("frozen v0.25 module missing or escaped checkout")

    # Seal sibling/source imports before loading historical code.  v0.25 is intentionally
    # self-contained, but fail closed if it ever starts resolving cmpct from elsewhere.
    sys.path.insert(0, str(checkout / "src"))
    sys.path.insert(0, str(checkout / "experiments"))
    sys.path.insert(0, str(checkout))
    name = f"cmpct_v025_frozen_{FROZEN_V029_SHA[:12]}"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v0.25 source")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    if not _within(Path(mod.__file__).resolve(), checkout):
        raise RuntimeError("frozen v0.25 module provenance escaped checkout")
    escaped = {}
    frozen_pkg = (checkout / "src" / "cmpct").resolve()
    for mn, m in sorted(sys.modules.items()):
        if mn != "cmpct" and not mn.startswith("cmpct."):
            continue
        raw = getattr(m, "__file__", None)
        if raw and not _within(Path(raw), frozen_pkg):
            escaped[mn] = str(Path(raw).resolve())
    if escaped:
        raise RuntimeError("historical contender imported cmpct outside frozen checkout: " + json.dumps(escaped, sort_keys=True))

    mod.ROOT = source
    mod.OUT = archive
    stats = dict(mod.build())
    verified = dict(mod.strong_verify())
    if not archive.is_file():
        raise RuntimeError("frozen v0.25 build produced no archive")

    f, meta, po = mod.open_ar()
    try:
        raw_header = archive.read_bytes()[:mod.HDR.size]
        magic, meta_comp, meta_raw, pack_count, meta_hash = mod.HDR.unpack(raw_header)
        if magic != mod.MAG or int(pack_count) != len(po):
            raise RuntimeError("v0.25 header/accounting mismatch")

        roles: dict[str, set[int]] = {
            "stream_pool": {int(pi) for _so, pi, _sn in meta.get("stream_packs", [])},
            "zip_skeleton": set(),
            "splice_residual": set(),
            "direct_plain": set(),
            "micro_pack": {int(pi) for pi, _ents in meta.get("micro", [])},
        }
        logical = {
            "special_container_logical_bytes": 0,
            "derived_view_logical_bytes": 0,
            "decode_derived_logical_bytes": 0,
            "splice_logical_bytes": 0,
            "plain_descriptor_logical_bytes": 0,
            "micro_logical_bytes": 0,
            "stream_pool_logical_bytes": sum(int(sn) for _so, _pi, sn in meta.get("stream_packs", [])),
        }
        for _path, d in meta.get("files", []):
            typ = d[0]
            if typ == "zipstreams":
                roles["zip_skeleton"].update(_ref_pack_ids(d[1])); logical["special_container_logical_bytes"] += int(d[4])
            elif typ == "inflate_stream":
                logical["derived_view_logical_bytes"] += int(d[4])
            elif typ == "decode_file":
                logical["decode_derived_logical_bytes"] += int(d[3])
            elif typ == "splice":
                roles["splice_residual"].update(_ref_pack_ids(d[1])); logical["splice_logical_bytes"] += int(d[4])
            elif typ == "plain":
                roles["direct_plain"].update(_ref_pack_ids(d[1])); logical["plain_descriptor_logical_bytes"] += int(d[2])
            else:
                raise RuntimeError(f"unexpected v0.25 descriptor type: {typ}")
        logical["micro_logical_bytes"] = sum(int(n) for _pi, ents in meta.get("micro", []) for _path, n in ents)

        # Micro entries are removed from files metadata, so role overlap should be impossible.
        owners: dict[int, list[str]] = {}
        for role, ids in roles.items():
            for pi in ids:
                owners.setdefault(pi, []).append(role)
        overlap = {pi: rs for pi, rs in owners.items() if len(rs) != 1}
        if overlap:
            raise RuntimeError("pack role overlap: " + json.dumps(overlap, sort_keys=True))
        unknown = sorted(set(range(len(po))) - set(owners))
        if unknown:
            raise RuntimeError(f"unattributed v0.25 packs: {unknown[:20]}")

        physical: dict[str, int] = {}
        for role, ids in roles.items():
            physical[role] = sum(int(mod.PH.size) + int(po[pi][3]) for pi in ids)
        physical["metadata_recovery"] = int(mod.HDR.size) + 2 * int(meta_comp) + int(mod.FTR.size)
        physical_sum = sum(physical.values())
        archive_bytes = archive.stat().st_size
        if physical_sum != archive_bytes:
            raise RuntimeError(f"v0.25 physical accounting mismatch: {physical_sum} != {archive_bytes}")

        result = {
            "frozen_source_sha": FROZEN_V029_SHA,
            "frozen_module": str(module_path),
            "source_sealed": True,
            "archive_bytes": archive_bytes,
            "archive_sha256": sha256(archive.read_bytes()).hexdigest(),
            "tree_sha256": str(stats.get("tree_sha256") or verified.get("tree_sha256")),
            "strong_verify": verified,
            "writer_stats": stats,
            "metadata": {"raw_bytes": int(meta_raw), "compressed_bytes": int(meta_comp), "pack_count": len(po)},
            "physical_bytes_by_role": physical,
            "physical_bytes_sum": physical_sum,
            "logical_coverage": logical,
            "pack_counts_by_role": {k: len(v) for k, v in roles.items()},
        }
    finally:
        f.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str) + "\n")


def _orchestrate(work: Path, frozen_checkout: Path) -> dict[str, Any]:
    # Current-line imports are deliberately delayed until after worker-mode dispatch so
    # the historical worker process cannot inherit modern cmpct modules.
    from benchmarks import mosaic_v029_generalization_bench as V029
    from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
    from experiments import entropygraph_v030_release_product as PRODUCT

    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_v025_attr_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_v025_attr_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    tree_sha = PRODUCT.treehash(source)

    sfv4 = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")
    sfv4_sizes = dict(sfv4["component_bytes"])
    if sum(sfv4_sizes.values()) != int(sfv4["stored_bytes"]):
        raise RuntimeError("SFV4 component accounting mismatch")

    worker_json = work / "v025-attribution.json"
    archive = work / "frozen-v025.cmpct"
    env = os.environ.copy()
    cmd = [sys.executable, str(Path(__file__).resolve()), "--frozen-worker", "--frozen-checkout", str(frozen_checkout),
           "--source", str(source), "--archive", str(archive), "--output", str(worker_json)]
    subprocess.run(cmd, check=True, env=env)
    hist = json.loads(worker_json.read_text())
    if hist["tree_sha256"] != tree_sha:
        raise RuntimeError(f"tree identity mismatch: frozen={hist['tree_sha256']} current={tree_sha}")

    v025_phys = hist["physical_bytes_by_role"]
    v025_stream = int(v025_phys["stream_pool"])
    v025_nonstream = int(hist["archive_bytes"]) - v025_stream
    sfv4_stream = int(sfv4_sizes.get("streams.bin", 0))
    sfv4_nonstream = int(sfv4["stored_bytes"]) - sfv4_stream
    total_gap = int(sfv4["stored_bytes"]) - int(hist["archive_bytes"])
    stream_delta = sfv4_stream - v025_stream
    nonstream_delta = sfv4_nonstream - v025_nonstream
    if stream_delta + nonstream_delta != total_gap:
        raise RuntimeError("coarse role delta does not close")
    dominant = "stream_path" if abs(stream_delta) >= abs(nonstream_delta) else "nonstream_path"
    dominant_delta = stream_delta if dominant == "stream_path" else nonstream_delta
    concentration = abs(dominant_delta) / max(1, abs(total_gap))

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": tree_sha,
        "sfv4": {"stored_bytes": int(sfv4["stored_bytes"]), "component_bytes": sfv4_sizes,
                 "all_member_stream_bytes": int(sfv4["all_member_stream_bytes"]), "literal_skeleton_bytes": int(sfv4["literal_skeleton_bytes"]),
                 "derived_file_count": int(sfv4["derived_file_count"]), "derived_logical_bytes": int(sfv4["derived_logical_bytes"])},
        "frozen_v025": hist,
        "comparison": {
            "same_tree": True,
            "accepted_v029_office_bytes": ACCEPTED_V029_OFFICE,
            "frozen_v025_same_tree_bytes": int(hist["archive_bytes"]),
            "frozen_v025_delta_vs_accepted_v029_bytes": int(hist["archive_bytes"]) - ACCEPTED_V029_OFFICE,
            "sfv4_minus_frozen_v025_bytes": total_gap,
            "stream_path_delta_bytes": stream_delta,
            "nonstream_path_delta_bytes": nonstream_delta,
            "dominant_coarse_role": dominant,
            "dominant_delta_bytes": dominant_delta,
            "dominant_abs_fraction_of_gap": concentration,
        },
        "hypothesis": {
            "physical_accounting_exact": int(hist["physical_bytes_sum"]) == int(hist["archive_bytes"]),
            "source_sealed": bool(hist["source_sealed"]),
            "same_tree": True,
            "role_concentration_ge_50pct": concentration >= 0.5,
        },
        "contract": {
            "diagnostic_only": True, "release_credit": False, "selector_changed": False, "format_changed": False,
            "thresholds_changed": False, "frozen_contender_executes_frozen_source": True,
            "note": "coarse stream/nonstream deltas are causal attribution guides, not interchangeable-format byte claims",
        },
        "next_if_stream_dominant": "measure v0.25 hot/cold stream-slab codec/framing economics against SFV4/page-seed streams, then prototype only the bounded winning slab primitive",
        "next_if_nonstream_dominant": "split v0.25 direct/micro/skeleton/control bytes against SFV4 base/control bytes and isolate the bounded packing/control primitive before any selector change",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-v025-attribution-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-v025-attribution.json"))
    p.add_argument("--frozen-checkout", type=Path, required=True)
    p.add_argument("--frozen-worker", action="store_true")
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.frozen_worker:
        if a.source is None or a.archive is None:
            p.error("--frozen-worker requires --source and --archive")
        _frozen_worker(a.frozen_checkout, a.source, a.archive, a.output); return
    d = _orchestrate(a.work_root, a.frozen_checkout)
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"comparison": d["comparison"], "v025_roles": d["frozen_v025"]["physical_bytes_by_role"], "sfv4_components": d["sfv4"]["component_bytes"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
