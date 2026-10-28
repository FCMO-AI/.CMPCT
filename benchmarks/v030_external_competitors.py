from __future__ import annotations

"""Exact-tree external compression matrix for the authoritative CMPCT v0.30 candidate.

All 15 repaired public workload trees are measured.  An external archive is credited only after extracting back
to the exact same logical tree SHA-256.  Input filesystem metadata is normalized for tools that store timestamps
so a new runner does not gain/lose bytes merely because the corpus was regenerated later.

Formats:
- CMPCT v0.30 authoritative complete artifact;
- deterministic ZIP/Deflate-9;
- 7z/LZMA2 maximum solid mode when ``7z`` is installed;
- deterministic solid tar + Zstd-19 when ``zstd`` is installed;
- ZPAQ method 5 when ``zpaq`` is installed.

Frozen promotion comparisons:
- CMPCT aggregate <= ZIP and 7z aggregate when available;
- neutral aggregate <= solid tar+Zstd-19;
- resemblance-hostile aggregate must close the historical structural frontier: <= tar+Zstd-19 and, when ZPAQ
  is available, <= ZPAQ method 5.

Those last hostile gates are intentionally demanding.  v0.29 historically trailed solid Zstd/ZPAQ there by
~82-85 KiB; v0.30 does not get to call itself a frontier release merely by moving that deficit elsewhere.

Footnote: tar+Zstd and ZPAQ are not presented as symmetric selective-read formats.  This harness makes an exact
*size* comparison only.  Random/member-read performance is measured only where the format semantics support an
honest equivalent operation.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import zipfile

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_authoritative as CMPCT

NORMALIZED_MTIME = 315532800  # 1980-01-01 UTC; also legal for ZIP's timestamp floor.


def _files(root: Path) -> list[Path]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if any(path.is_symlink() for path in files):
        raise RuntimeError("external matrix currently requires regular-file-only workloads")
    return files


def _tree(root: Path) -> str:
    return CMPCT.treehash(root)


def _normalized_stage(source: Path, parent: Path) -> Path:
    stage = parent / "normalized"
    stage.mkdir(parents=True)
    for path in _files(source):
        rel = path.relative_to(source)
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        target.chmod(0o644)
        os.utime(target, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    for directory in sorted((p for p in stage.rglob("*") if p.is_dir()), reverse=True):
        directory.chmod(0o755)
        os.utime(directory, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    os.utime(stage, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    if _tree(stage) != _tree(source):
        raise RuntimeError("filesystem normalization changed logical tree identity")
    return stage


def _verify_extracted(extracted: Path, expected_tree: str, label: str) -> None:
    got = _tree(extracted)
    if got != expected_tree:
        raise RuntimeError(f"{label} extracted tree mismatch: {got} != {expected_tree}")


def _zip(stage: Path, archive: Path, extracted: Path) -> dict:
    started = time.perf_counter()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in _files(stage):
            rel = path.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    create_s = time.perf_counter() - started
    started = time.perf_counter()
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(extracted)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s}


def _seven_zip(stage: Path, archive: Path, extracted: Path) -> dict:
    exe = shutil.which("7z") or shutil.which("7zz")
    if exe is None:
        return {"available": False, "reason": "7z-not-installed"}
    started = time.perf_counter()
    subprocess.run(
        [exe, "a", "-t7z", "-m0=lzma2", "-mx=9", "-ms=on", str(archive), "."],
        cwd=stage,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    create_s = time.perf_counter() - started
    extracted.mkdir(parents=True)
    started = time.perf_counter()
    subprocess.run(
        [exe, "x", str(archive), f"-o{extracted}", "-y"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s, "tool": Path(exe).name}


def _tar_zstd(stage: Path, archive: Path, extracted: Path, work: Path) -> dict:
    exe = shutil.which("zstd")
    if exe is None:
        return {"available": False, "reason": "zstd-not-installed"}
    tar_path = work / "solid.tar"
    started = time.perf_counter()
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as tf:
        for path in _files(stage):
            rel = path.relative_to(stage).as_posix()
            info = tarfile.TarInfo(rel)
            raw = path.read_bytes()
            info.size = len(raw)
            info.mtime = NORMALIZED_MTIME
            info.mode = 0o644
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            import io
            tf.addfile(info, io.BytesIO(raw))
    subprocess.run([exe, "-19", "-f", str(tar_path), "-o", str(archive)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    create_s = time.perf_counter() - started

    decoded_tar = work / "decoded.tar"
    started = time.perf_counter()
    subprocess.run([exe, "-d", "-f", str(archive), "-o", str(decoded_tar)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    extracted.mkdir(parents=True)
    with tarfile.open(decoded_tar, "r") as tf:
        # Archive is generated locally from safe relative paths; still reject anything surprising before extract.
        for member in tf.getmembers():
            target = (extracted / member.name).resolve()
            if extracted.resolve() not in target.parents and target != extracted.resolve():
                raise RuntimeError("generated tar contains unsafe path")
        tf.extractall(extracted)
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s}


def _zpaq(stage: Path, archive: Path, extracted: Path) -> dict:
    exe = shutil.which("zpaq")
    if exe is None:
        return {"available": False, "reason": "zpaq-not-installed"}
    rels = [path.relative_to(stage).as_posix() for path in _files(stage)]
    started = time.perf_counter()
    subprocess.run(
        [exe, "a", str(archive), *rels, "-method", "5"],
        cwd=stage,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    create_s = time.perf_counter() - started
    extracted.mkdir(parents=True)
    started = time.perf_counter()
    subprocess.run(
        [exe, "x", str(archive), "-to", str(extracted)],
        cwd=stage,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    extract_s = time.perf_counter() - started
    return {"available": True, "archive_bytes": archive.stat().st_size, "create_s": create_s, "extract_s": extract_s}


def _cmpct(stage: Path, archive: Path, extracted: Path) -> dict:
    started = time.perf_counter()
    stats = CMPCT.build(stage, archive)
    create_s = time.perf_counter() - started
    verified = CMPCT.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"CMPCT v0.30 competitor artifact failed strong verification: {verified!r}")
    started = time.perf_counter()
    CMPCT.extract(archive, extracted)
    extract_s = time.perf_counter() - started
    return {
        "available": True,
        "archive_bytes": archive.stat().st_size,
        "create_s": create_s,
        "extract_s": extract_s,
        "selected": stats.get("selected"),
        "max_member_read_amplification": stats.get("max_selected_member_read_amplification"),
    }


def _one(label: str, source: Path, work: Path) -> dict:
    expected_tree = _tree(source)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-competitor-stage-", dir=work) as td:
        td_path = Path(td)
        stage = _normalized_stage(source, td_path)
        outputs = td_path / "outputs"
        outputs.mkdir()
        formats = {}
        specs = (
            ("cmpct_v030", _cmpct, outputs / "candidate.cmpct", outputs / "cmpct-out"),
            ("zip_deflate9", _zip, outputs / "archive.zip", outputs / "zip-out"),
            ("7z_lzma2_max_solid", _seven_zip, outputs / "archive.7z", outputs / "7z-out"),
            ("tar_zstd19_solid", lambda s, a, e: _tar_zstd(s, a, e, outputs), outputs / "archive.tar.zst", outputs / "zstd-out"),
            ("zpaq_method5", _zpaq, outputs / "archive.zpaq", outputs / "zpaq-out"),
        )
        for name, function, archive, extracted in specs:
            result = function(stage, archive, extracted)
            if result.get("available"):
                _verify_extracted(extracted, expected_tree, name)
                result["tree_verified"] = True
            formats[name] = result
        return {"label": label, "tree_sha256": expected_tree, "formats": formats}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_comp_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_comp_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_comp_repair")
    repair.install_generation_hooks(neutral)
    roots = (("neutral_hostile_v1", neutral, work_root / "neutral"), ("resemblance_hostile_v1", hostile, work_root / "resemblance"))
    rows = []
    for suite, builder, root in roots:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected_tree = accepted[key]["tree_sha256"]
            if _tree(workload) != expected_tree:
                raise RuntimeError(f"competitor source drift: {suite}/{workload.name}")
            row = _one(f"{suite}/{workload.name}", workload, work_root)
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(json.dumps({"label": row["label"], "sizes": {k: v.get("archive_bytes") for k, v in row["formats"].items()}}, separators=(",", ":")), flush=True)

    names = ("cmpct_v030", "zip_deflate9", "7z_lzma2_max_solid", "tar_zstd19_solid", "zpaq_method5")
    aggregates = {}
    for suite in ("neutral_hostile_v1", "resemblance_hostile_v1", "all"):
        selected = rows if suite == "all" else [row for row in rows if row["suite"] == suite]
        aggregate = {}
        for name in names:
            measured = [row["formats"][name] for row in selected if row["formats"][name].get("available")]
            aggregate[name] = {
                "available_rows": len(measured),
                "complete_for_suite": len(measured) == len(selected),
                "archive_bytes": sum(int(item["archive_bytes"]) for item in measured) if measured else None,
            }
        aggregates[suite] = aggregate

    all_cmpct = aggregates["all"]["cmpct_v030"]["archive_bytes"]
    neutral_cmpct = aggregates["neutral_hostile_v1"]["cmpct_v030"]["archive_bytes"]
    hostile_cmpct = aggregates["resemblance_hostile_v1"]["cmpct_v030"]["archive_bytes"]

    def _le(suite: str, competitor: str, *, optional: bool = False) -> bool:
        item = aggregates[suite][competitor]
        if not item["complete_for_suite"]:
            return optional
        cmpct_size = aggregates[suite]["cmpct_v030"]["archive_bytes"]
        return int(cmpct_size) <= int(item["archive_bytes"])

    gate = {
        "exact_workload_count": len(rows) == 15,
        "all_cmpct_trees_verified": all(row["formats"]["cmpct_v030"].get("tree_verified") for row in rows),
        "all_zip_trees_verified": all(row["formats"]["zip_deflate9"].get("tree_verified") for row in rows),
        "aggregate_beats_zip": _le("all", "zip_deflate9"),
        "aggregate_beats_7z_when_available": _le("all", "7z_lzma2_max_solid", optional=True),
        "neutral_beats_solid_zstd19": _le("neutral_hostile_v1", "tar_zstd19_solid"),
        "hostile_closes_solid_zstd19_frontier": _le("resemblance_hostile_v1", "tar_zstd19_solid"),
        "hostile_closes_zpaq5_frontier_when_available": _le("resemblance_hostile_v1", "zpaq_method5", optional=True),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-external-competitors-v1",
        "contract": {
            "workloads": 15,
            "source_identity": "exact repaired v0.29 15-workload frontier",
            "formats": list(names),
            "hostile_frontier_rule": "CMPCT v0.30 <= solid tar+Zstd-19 and <= ZPAQ m5 when available",
            "random_access_claim_boundary": "no selective-read equivalence claim for solid tar+Zstd or ZPAQ",
        },
        "rows": rows,
        "aggregates": aggregates,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-external-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-external-competitors.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"aggregates": result["aggregates"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 external competitor promotion gate failed")


if __name__ == "__main__":
    main()
