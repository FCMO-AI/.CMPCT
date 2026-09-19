from __future__ import annotations

"""Cheap falsifier for complementary Analytics relations behind the v0.29 floor.

The integrated tabular owner removed 2.155 MB but remained 2.102 MB above accepted v0.29.
Independent v0.25 attribution shows a second exact relation on the same frozen Analytics tree:
``features_compressed.npz`` physically contains the exact bytes of external ``features.npy``.

This oracle asks the smallest causal question before any full-matrix work: if the tabular pair and
that exact container/member relation are represented once, does the complete authenticated research
bundle cross the source-sealed v0.29 Analytics floor (6,135,172 B)?

No shipping format/selector/version changes. No locality or release credit. If this fails, do not
turn it into a threshold sweep.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import tempfile
import time
import zipfile

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-analytics-dual-owner-v1"
ACCEPTED_V029_ANALYTICS = 6_135_172
GROUP_ROWS = I.GROUP_ROWS
MAGIC = b"R4D1\0\0\0\0"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cpu() -> tuple[float, float]:
    me = resource.getrusage(resource.RUSAGE_SELF)
    ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime + me.ru_stime), float(ch.ru_utime + ch.ru_stime)


def _delta(after: tuple[float, float], before: tuple[float, float]) -> dict:
    self_cpu = after[0] - before[0]
    child_cpu = after[1] - before[1]
    return {"self_cpu_s": self_cpu, "children_cpu_s": child_cpu, "tree_cpu_s": self_cpu + child_cpu}


def _npz_relation(root: Path) -> dict:
    npys = sorted(root.rglob("*.npy"))
    npzs = sorted(root.rglob("*.npz"))
    candidates = []
    observed = 0
    for npz in npzs:
        with zipfile.ZipFile(npz, "r") as zf:
            names = set(zf.namelist())
            observed += min(npz.stat().st_size, 65536)
            for npy in npys:
                member = npy.name
                if member not in names:
                    continue
                t0 = time.process_time(); w0 = time.perf_counter()
                internal = zf.read(member)
                proof_cpu = time.process_time() - t0; proof_wall = time.perf_counter() - w0
                external = npy.read_bytes()
                if internal == external:
                    candidates.append({
                        "npz_path": npz.relative_to(root).as_posix(),
                        "npy_path": npy.relative_to(root).as_posix(),
                        "member": member,
                        "npz_bytes": npz.stat().st_size,
                        "npy_bytes": npy.stat().st_size,
                        "proof_bytes": len(internal) + len(external),
                        "proof_cpu_s": proof_cpu,
                        "proof_wall_s": proof_wall,
                    })
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one exact NPY/NPZ relation, got {candidates!r}")
    return {"observed_bytes": observed, "accepted": candidates[0]}


def _write_bundle(out: Path, base: Path, tcol: bytes, npz_raw: bytes, manifest: dict) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(base, out / "base.cmpct")
    (out / "owner.tcol").write_bytes(tcol)
    (out / "owner.npz").write_bytes(npz_raw)
    mraw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    (out / "manifest.json").write_bytes(mraw)
    auth = MAGIC + b"".join(hashlib.sha256(x).digest() for x in (
        mraw, (out / "base.cmpct").read_bytes(), tcol, npz_raw
    ))
    (out / "auth.bin").write_bytes(auth)
    sizes = {p.name: p.stat().st_size for p in out.iterdir() if p.is_file()}
    return {"component_bytes": sizes, "stored_bytes": sum(sizes.values())}


def _open_bundle(bundle: Path) -> tuple[dict, Path, bytes, bytes]:
    mraw = (bundle / "manifest.json").read_bytes()
    base = bundle / "base.cmpct"; tcol = (bundle / "owner.tcol").read_bytes(); npz = (bundle / "owner.npz").read_bytes()
    auth = (bundle / "auth.bin").read_bytes()
    expected = MAGIC + b"".join(hashlib.sha256(x).digest() for x in (mraw, base.read_bytes(), tcol, npz))
    if auth != expected:
        raise ValueError("dual-owner authentication failed")
    return json.loads(mraw), base, tcol, npz


def _build_candidate(source: Path, out: Path, work: Path) -> dict:
    discovery = I._discover(source)
    if len(discovery["accepted"]) != 1:
        raise RuntimeError("tabular admission did not yield exactly one relation")
    tab = discovery["accepted"][0]
    npz_rel = _npz_relation(source)
    rel = npz_rel["accepted"]

    csvp = source.joinpath(*Path(tab["csv_path"]).parts)
    jsonp = source.joinpath(*Path(tab["jsonl_path"]).parts)
    npyp = source.joinpath(*Path(rel["npy_path"]).parts)
    npzp = source.joinpath(*Path(rel["npz_path"]).parts)

    csv_source = csvp.read_bytes(); json_source = jsonp.read_bytes()
    fields, csv_rows = OWNER._parse_csv(csv_source)
    jfields, json_rows = OWNER._parse_jsonl(json_source)
    if fields != jfields or not OWNER._semantic_equal(fields, csv_rows, json_rows):
        raise RuntimeError("accepted tabular relation failed semantic owner gate")
    csv_lengths = FAST._line_lengths(csv_source, len(json_rows), GROUP_ROWS, header=True)
    json_lengths = FAST._line_lengths(json_source, len(json_rows), GROUP_ROWS, header=False)
    tcol, tcol_stats = FAST._encode(fields, json_rows, GROUP_ROWS, csv_lengths, json_lengths)
    csv_raw, json_raw = I._owner_raw(tcol)
    if csv_raw != csv_source or json_raw != json_source:
        raise RuntimeError("tabular owner reconstruction mismatch")

    npz_raw = npzp.read_bytes()
    with zipfile.ZipFile(npzp, "r") as zf:
        npy_from_npz = zf.read(rel["member"])
    if npy_from_npz != npyp.read_bytes():
        raise RuntimeError("NPZ member is not exact external NPY")

    stripped = work / "stripped"
    remove = {tab["csv_path"], tab["jsonl_path"], rel["npy_path"], rel["npz_path"]}
    I._copy_without(source, stripped, remove)
    base = work / "base.cmpct"
    before = _cpu(); w0 = time.perf_counter(); base_stats = dict(PRODUCT.build(stripped, base)); base_wall = time.perf_counter() - w0; after = _cpu()

    manifest = {
        "schema": "cmpct-v030-r4-analytics-dual-owner-bundle-v1",
        "group_rows": GROUP_ROWS,
        "members": {
            "csv": {"path": tab["csv_path"], "sha256": _sha(csv_raw), **I._stat_record(csvp)},
            "jsonl": {"path": tab["jsonl_path"], "sha256": _sha(json_raw), **I._stat_record(jsonp)},
            "npy": {"path": rel["npy_path"], "sha256": _sha(npy_from_npz), **I._stat_record(npyp)},
            "npz": {"path": rel["npz_path"], "sha256": _sha(npz_raw), **I._stat_record(npzp)},
        },
        "tabular_discovery": discovery,
        "npz_relation": npz_rel,
    }
    bundle = _write_bundle(out, base, tcol, npz_raw, manifest)
    return {
        "stored_bytes": bundle["stored_bytes"], "bundle": bundle, "base_stats": base_stats,
        "base_build_wall_s": base_wall, "base_build_cpu": _delta(after, before), "tcol_stats": tcol_stats,
        "tabular_discovery": discovery, "npz_relation": npz_rel,
    }


def _extract_candidate(bundle: Path, out: Path) -> dict:
    manifest, base, tcol, npz_raw = _open_bundle(bundle)
    sv = dict(PRODUCT.strong_verify(base))
    if sv.get("ok") is False:
        raise RuntimeError("base strong verify failed")
    PRODUCT.extract(base, out)
    csv_raw, json_raw = I._owner_raw(tcol)
    with tempfile.TemporaryDirectory(prefix="cmpct-r4-dual-npz-") as td:
        zpath = Path(td) / "owner.npz"; zpath.write_bytes(npz_raw)
        with zipfile.ZipFile(zpath, "r") as zf:
            npy_raw = zf.read(Path(manifest["members"]["npy"]["path"]).name)
    payloads = {"csv": csv_raw, "jsonl": json_raw, "npy": npy_raw, "npz": npz_raw}
    for kind, raw in payloads.items():
        meta = manifest["members"][kind]
        if _sha(raw) != meta["sha256"]:
            raise RuntimeError(f"{kind} hash mismatch")
        p = out.joinpath(*Path(meta["path"]).parts); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)
        os.chmod(p, int(meta["mode"])); os.utime(p, ns=(int(meta["mtime_ns"]), int(meta["mtime_ns"])))
    return {"base_strong_verify": sv, "tree_sha256": PRODUCT.treehash(out)}


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_r4_dual_neutral")
    repair = V029._load(V029.REPAIR_PATH, "cmpct_r4_dual_repair"); repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"; expected = PRODUCT.treehash(source)

    baseline = work / "baseline.cmpct"
    before = _cpu(); w0 = time.perf_counter(); base_stats = dict(PRODUCT.build(source, baseline)); base_wall = time.perf_counter() - w0; after = _cpu()
    baseline_row = {"stored_bytes": baseline.stat().st_size, "wall_s": base_wall, "cpu": _delta(after, before), "stats": base_stats}
    sv = dict(PRODUCT.strong_verify(baseline))
    if sv.get("ok") is False:
        raise RuntimeError("baseline strong verify failed")

    candidate = work / "candidate"; candidate_work = work / "candidate-work"
    before = _cpu(); w0 = time.perf_counter(); cand = _build_candidate(source, candidate, candidate_work); cand_wall = time.perf_counter() - w0; after = _cpu()
    cand["complete_build_wall_s"] = cand_wall; cand["complete_build_cpu"] = _delta(after, before)
    extracted = work / "candidate-extract"; verify = _extract_candidate(candidate, extracted)
    if verify["tree_sha256"] != expected:
        raise RuntimeError("dual-owner tree mismatch")

    saving = baseline_row["stored_bytes"] - cand["stored_bytes"]
    margin = ACCEPTED_V029_ANALYTICS - cand["stored_bytes"]
    supported = cand["stored_bytes"] < ACCEPTED_V029_ANALYTICS
    return {
        "schema": SCHEMA, "source_commit": os.environ.get("EVIDENCE_HEAD"), "tree_sha256": expected,
        "logical_bytes": sum(p.stat().st_size for p in source.rglob("*") if p.is_file()),
        "accepted_v029_bytes": ACCEPTED_V029_ANALYTICS,
        "baseline": baseline_row, "candidate": cand, "candidate_verify": verify,
        "saving_vs_v030_bytes": saving, "margin_vs_v029_bytes": margin,
        "hypothesis": {
            "dual_owner_beats_v030": saving > 0,
            "dual_owner_beats_accepted_v029": supported,
            "supported_for_full_matrix_falsifier": supported,
        },
        "contract": {
            "diagnostic_only": True, "release_credit": False, "single_workload_causal_falsifier": True,
            "production_format_changed": False, "production_selector_changed": False,
            "same_semantic_tree_verified": True, "no_locality_claim": True,
            "no_threshold_sweep": True,
        },
        "next_if_supported": "run a full 15-workload admission/fallback falsifier before any shipping design",
        "next_if_falsified": "preserve negative and attribute remaining physical gap; do not tune thresholds",
    }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-dual-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-dual.json")); a = p.parse_args()
    d = run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({"baseline_bytes": d["baseline"]["stored_bytes"], "candidate_bytes": d["candidate"]["stored_bytes"], "accepted_v029_bytes": d["accepted_v029_bytes"], "saving_vs_v030_bytes": d["saving_vs_v030_bytes"], "margin_vs_v029_bytes": d["margin_vs_v029_bytes"], "hypothesis": d["hypothesis"], "components": d["candidate"]["bundle"]["component_bytes"], "candidate_wall_s": d["candidate"]["complete_build_wall_s"], "candidate_tree_cpu_s": d["candidate"]["complete_build_cpu"]["tree_cpu_s"]}, indent=2))


if __name__ == "__main__": main()
