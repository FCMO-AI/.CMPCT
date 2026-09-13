from __future__ import annotations

"""Causal Office attribution referee for the reactivated v0.30 frontier.

Mission lock: docs/V030_OFFICE_PHYSICAL_ECONOMICS_MISSION_LOCK_2026-09-13.md

B and C are deliberately built from one immutable physical archive.  They therefore
share byte-identical physical packs and reconstruction membership; only the
filesystem-control bytes embedded in authenticated primary/tail metadata differ.
If that invariant does not hold the experiment is invalid, not a product loss.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import shutil
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_current15_stable_corpus as CORPUS
from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07
from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS

V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
CONTROL_KEY = EG05.EMBEDDED_FS_KEY


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rss_kib() -> int:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def tree_bytes(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())


def timed(fn):
    c0 = time.process_time(); w0 = time.perf_counter()
    value = fn()
    return value, time.process_time() - c0, time.perf_counter() - w0


def profile_controls(source: Path, profile: Path) -> tuple[bytes, bytes, dict]:
    v1_raw, regular_sources, stats = FS.capture_filesystem_manifest(
        source,
        max_path_bytes=EG05.MAX_PATH_BYTES,
        max_profile_files=EG05.MAX_PROFILE_FILES,
        max_profile_logical_bytes=EG05.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=EG05.MAX_MANIFEST_ENTRIES,
    )
    implicit = IFS4.encode_v1(v1_raw, max_path_bytes=EG05.MAX_PATH_BYTES, max_entries=EG05.MAX_MANIFEST_ENTRIES)
    if not IFS4.semantics_equal(v1_raw, implicit, max_path_bytes=EG05.MAX_PATH_BYTES, max_entries=EG05.MAX_MANIFEST_ENTRIES):
        raise RuntimeError("implicit-v4 changed canonical filesystem semantics")
    profile.mkdir(parents=True, exist_ok=True)
    for src, rel in regular_sources:
        dst = profile.joinpath(*PurePosixPath(rel).parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dst, follow_symlinks=False)
        except OSError:
            shutil.copyfile(src, dst)
    return v1_raw, implicit, stats


def physical_base(profile: Path, archive: Path) -> dict:
    with EG05._engine(archive, profile):
        return dict(EG05.V25.build())


def embedded_copy(base: Path, out: Path, control: bytes) -> dict:
    shutil.copyfile(base, out)
    return EG05._embed_control(out, control)


def parsed(archive: Path) -> dict:
    raw = archive.read_bytes()
    meta, physical = EG05._parse_physical_region(raw)
    control = meta.get(CONTROL_KEY)
    if not isinstance(control, bytes):
        raise RuntimeError("missing embedded control")
    reduced = dict(meta); reduced.pop(CONTROL_KEY, None)
    mcs = int(EG05.V25.HDR.unpack_from(raw, 0)[1])
    mus = int(EG05.V25.HDR.unpack_from(raw, 0)[2])
    return {
        "physical_sha256": sha(physical),
        "physical_region_bytes": len(physical),
        "membership_sha256": sha(EG05.msgpack.packb(reduced, use_bin_type=True)),
        "control_raw_bytes": len(control),
        "metadata_raw_bytes": mus,
        "metadata_compressed_bytes": mcs,
        "metadata_recovery_copy_bytes": mcs,
        "framing_header_footer_bytes": EG05.V25.HDR.size + EG05.V25.FTR.size,
        "archive_bytes": len(raw),
    }


def explicit_control(archive: Path) -> bytes:
    with EG05._engine(archive.resolve()):
        stream, meta, _ = EG05.V25.open_ar()
        try:
            raw = meta.get(CONTROL_KEY)
        finally:
            stream.close()
    if not isinstance(raw, bytes):
        raise RuntimeError("explicit control missing")
    return raw


def restore_explicit(profile: Path, raw: bytes) -> dict:
    decoded = FS.decode_manifest(raw, max_path_bytes=EG05.MAX_PATH_BYTES, max_entries=EG05.MAX_MANIFEST_ENTRIES)
    FS.restore_manifest_tree(profile, decoded)
    return decoded


def extract_explicit(archive: Path, dest: Path) -> None:
    control = explicit_control(archive)
    with EG05._engine(archive.resolve()):
        EG05.V25.extract(dest)
    restore_explicit(dest, control)


def fidelity_raw(root: Path) -> bytes:
    raw, _regular, _stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=EG05.MAX_PATH_BYTES,
        max_profile_files=EG05.MAX_PROFILE_FILES,
        max_profile_logical_bytes=EG05.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=EG05.MAX_MANIFEST_ENTRIES,
    )
    return raw


def verify_controlled(label: str, archive: Path, source: Path, v1_raw: bytes, *, implicit: bool) -> dict:
    expected_tree = EG05._treehash(source)
    if implicit:
        verify = EG05.strong_verify(archive, expected_tree=expected_tree)
        extractor = EG05.extract
    else:
        with EG05._engine(archive.resolve()):
            inner = dict(EG05.V25.strong_verify())
        with tempfile.TemporaryDirectory(prefix="office-explicit-verify-") as td:
            restored = Path(td) / "restored"
            extract_explicit(archive, restored)
            if EG05._treehash(restored) != expected_tree:
                raise RuntimeError("explicit-control canonical tree mismatch")
        verify = {"ok": True, "inner": inner, "canonical_user_tree_sha256": expected_tree}
        extractor = extract_explicit

    locality = EG05.locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError(f"{label} violates frozen locality bounds")

    with tempfile.TemporaryDirectory(prefix=f"office-{label}-extract-") as td:
        restored = Path(td) / "restored"
        _, cpu, wall = timed(lambda: extractor(archive, restored))
        fidelity = fidelity_raw(restored) == v1_raw
        if not fidelity:
            raise RuntimeError(f"{label} filesystem fidelity mismatch")

    corrupt = archive.with_name(archive.stem + "-primary-corrupt" + archive.suffix)
    shutil.copyfile(archive, corrupt)
    raw = bytearray(corrupt.read_bytes())
    if len(raw) <= EG05.V25.HDR.size:
        raise RuntimeError("archive too short for recovery mutation")
    raw[EG05.V25.HDR.size] ^= 0x01
    corrupt.write_bytes(raw)
    try:
        if implicit:
            recovery = EG05.strong_verify(corrupt, expected_tree=expected_tree)["ok"]
        else:
            with tempfile.TemporaryDirectory(prefix="office-explicit-recovery-") as td:
                restored = Path(td) / "restored"
                extract_explicit(corrupt, restored)
                recovery = EG05._treehash(restored) == expected_tree and fidelity_raw(restored) == v1_raw
    finally:
        corrupt.unlink(missing_ok=True)
    if not recovery:
        raise RuntimeError(f"{label} tail recovery failed")

    rows = locality.get("members", [])
    amps = sorted(float(r["amplification"]) for r in rows)
    total_logical = sum(int(r["logical_bytes"]) for r in rows)
    total_decoded = sum(int(r["decoded_context_bytes"]) for r in rows)
    return {
        "verify": verify,
        "filesystem_fidelity": fidelity,
        "tail_recovery": recovery,
        "extract_cpu_s": cpu,
        "extract_wall_s": wall,
        "extract_throughput_mib_s": (tree_bytes(source) / (1024 * 1024)) / max(wall, 1e-9),
        "max_member_read_amplification": float(locality["max_member_read_amplification"]),
        "mean_selective_amplification": total_decoded / max(1, total_logical),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "member_count": len(rows),
        "p95_member_amplification": amps[min(len(amps)-1, int(0.95 * len(amps)))] if amps else 0.0,
    }


def build_stage(module, source: Path, archive: Path) -> dict:
    before = rss_kib()
    result, cpu, wall = timed(lambda: module.build(source, archive))
    return {
        "archive_bytes": archive.stat().st_size,
        "create_cpu_s": cpu,
        "create_wall_s": wall,
        "rss_before_kib": before,
        "rss_after_kib": rss_kib(),
        "reported": result,
    }


def frozen_v029(source: Path, out: Path, checkout: Path) -> dict:
    checkout = checkout.resolve()
    srcdir = (checkout / "src").resolve()
    code = r'''
import hashlib,json,os,sys,time
from pathlib import Path
frozen=Path(sys.argv[1]).resolve(); source=Path(sys.argv[2]).resolve(); out=Path(sys.argv[3]).resolve()
sys.path.insert(0,str((frozen/'src').resolve()))
import cmpct
loaded=Path(cmpct.__file__).resolve()
if (frozen/'src').resolve() not in loaded.parents:
    raise SystemExit(f"SOURCE_SEAL_FAILURE:{loaded}")
from cmpct.builder import Builder
c0=time.process_time(); w0=time.perf_counter(); Builder(source).build(out); cpu=time.process_time()-c0; wall=time.perf_counter()-w0
print(json.dumps({'source_sha':os.environ.get('V029_SHA'),'cmpct_module':str(loaded),'archive_bytes':out.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall}))
'''
    env = dict(os.environ); env["V029_SHA"] = V029_SHA; env["PYTHONNOUSERSITE"] = "1"
    p = subprocess.run([sys.executable, "-c", code, str(checkout), str(source), str(out)], check=True, capture_output=True, text=True, env=env)
    row = json.loads(p.stdout.strip().splitlines()[-1])
    if not str(Path(row["cmpct_module"]).resolve()).startswith(str(srcdir) + os.sep):
        raise RuntimeError("frozen v0.29 source seal escaped checkout")
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("office-physical-economics.json"))
    ap.add_argument("--v029-checkout", type=Path, required=True)
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-office-economics-") as td:
        work = Path(td); corpus = work / "corpus"
        manifest = CORPUS.build(corpus)
        source = corpus / "02_office_workspace"
        if not source.is_dir():
            raise RuntimeError("stable current15 Office workload missing")
        office_manifest = next(x for x in manifest["corpora"] if x["name"] == source.name)
        v1_profile = work / "physical-profile"
        v1_raw, implicit_raw, fs_stats = profile_controls(source, v1_profile)

        base = work / "physical-base.cmpct"
        base_stats, base_cpu, base_wall = timed(lambda: physical_base(v1_profile, base))
        b = work / "B-explicit.cmpct"; c = work / "C-implicit.cmpct"
        b_frame = embedded_copy(base, b, v1_raw)
        c_frame = embedded_copy(base, c, implicit_raw)
        bp, cp = parsed(b), parsed(c)
        same_payload = bp["physical_sha256"] == cp["physical_sha256"] and bp["physical_region_bytes"] == cp["physical_region_bytes"]
        same_membership = bp["membership_sha256"] == cp["membership_sha256"]
        if not same_payload or not same_membership:
            verdict = "OFFICE_ATTRIBUTION_INVALID"
            raise RuntimeError(f"{verdict}: B/C physical identity failed")

        vb, vb_cpu, vb_wall = timed(lambda: verify_controlled("B", b, source, v1_raw, implicit=False))
        vc, vc_cpu, vc_wall = timed(lambda: verify_controlled("C", c, source, v1_raw, implicit=True))

        a = build_stage(EG01, source, work / "A-eg01.cmpct")
        d = build_stage(EG07, source, work / "D-eg07.cmpct")
        v029 = frozen_v029(source, work / "v029.cmpct", args.v029_checkout)

        regret_b = int(bp["archive_bytes"]) - int(v029["archive_bytes"])
        regret_c = int(cp["archive_bytes"]) - int(v029["archive_bytes"])
        recovered = int(bp["archive_bytes"]) - int(cp["archive_bytes"])
        recover_fraction = recovered / max(1, abs(regret_b)) if regret_b > 0 else 0.0
        if regret_b <= 0:
            verdict = "OFFICE_REGRET_MIXED"
        elif recover_fraction >= 0.10:
            verdict = "OFFICE_CONTROL_PLANE_DOMINATES_REGRET"
        elif recovered <= max(128, int(0.01 * regret_b)):
            verdict = "OFFICE_PHYSICAL_LOCALITY_DOMINATES_REGRET"
        else:
            verdict = "OFFICE_REGRET_MIXED"

        out = {
            "schema": "v030-office-physical-economics-v1",
            "verdict": verdict,
            "office_tree_sha256": office_manifest["tree_sha256"],
            "logical_bytes": office_manifest["logical_bytes"],
            "files": office_manifest["files"],
            "frozen_v029": v029,
            "A_federated_explicit_physical": a,
            "B_same_physical_explicit_control": {"components": bp, "framing": b_frame, "create_shared_base_cpu_s": base_cpu, "create_shared_base_wall_s": base_wall, "verification": vb, "verify_cpu_s": vb_cpu, "verify_wall_s": vb_wall},
            "C_same_physical_implicit_v4": {"components": cp, "framing": c_frame, "verification": vc, "verify_cpu_s": vc_cpu, "verify_wall_s": vc_wall},
            "D_product_valid_eg07": d,
            "bc_same_physical_payload": same_payload,
            "bc_same_membership": same_membership,
            "bc_control_only_total_delta_bytes": recovered,
            "b_regret_vs_v029_bytes": regret_b,
            "c_regret_vs_v029_bytes": regret_c,
            "control_recovery_fraction_of_b_regret": recover_fraction,
            "filesystem_v1_control_bytes": len(v1_raw),
            "filesystem_implicit_v4_control_bytes": len(implicit_raw),
            "filesystem_control_raw_saving_bytes": len(v1_raw) - len(implicit_raw),
            "filesystem_stats": fs_stats,
            "physical_base_build_stats": base_stats,
            "process_peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
