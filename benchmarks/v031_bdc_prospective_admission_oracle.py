#!/usr/bin/env python3
"""Research-only prospective BDC selector oracle, not a CMPCT storage grammar.

Decision boundary: can a cheap content-blind-to-names sample screen decline
independent/unhelpful source families before full BDC work, while preserving
noncanonical BDC headroom against authentic canonical r24 where applicable?
The selected output is NEVER published as canonical CMPCT. Every source still
gets an independently verified canonical r24 archive as the safe fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import resource
import stat
import tempfile
import time
import traceback
from pathlib import Path

from benchmarks import v031_bounded_drift_coordered_court as FROZEN
from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from cmpct.builder import Builder
from cmpct.reader import CMPCT

# Fixed before outcomes. These limits are not a proposed product admission law.
MIN_MEMBERS = 3
MAX_MEMBERS = 24
MAX_MEMBER_BYTES = 1024 * 1024
MAX_LOGICAL_BYTES = 8 * 1024 * 1024
WINDOW_BYTES = 4096
ANCHOR_BYTES = 48
ANCHOR_STRIDE = 128
MIN_SHARED_RATIO = 0.12
MIN_LINKED_PEERS = 2
NORMALIZED_MTIME = 315532800


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _paths(source: Path) -> tuple[list[Path], str | None]:
    regular = []
    for parent, dirs, files in os.walk(source, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(parent) / name
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                return regular, "symlink_requires_canonical_fallback"
            if stat.S_ISDIR(st.st_mode):
                continue
            if not stat.S_ISREG(st.st_mode):
                return regular, "special_file_requires_canonical_fallback"
            if st.st_nlink > 1:
                return regular, "hardlink_requires_canonical_fallback"
            if st.st_size and hasattr(st, "st_blocks") and st.st_blocks * 512 < st.st_size:
                return regular, "sparse_requires_canonical_fallback"
            regular.append(p)
    return sorted(regular), None


def _windows(path: Path, size: int) -> tuple[list[bytes], int]:
    starts = sorted(set(max(0, min(size - WINDOW_BYTES, off)) for off in
                        (0, (size - WINDOW_BYTES) // 2, size - WINDOW_BYTES)))
    windows = []
    charged = 0
    with path.open("rb", buffering=0) as inp:
        for off in starts:
            inp.seek(off)
            block = inp.read(WINDOW_BYTES)
            charged += len(block)
            windows.append(block)
    return windows, charged


def screen(source: Path) -> dict:
    files, reason = _paths(source)
    info = {"eligible": False, "reason": reason, "sample_bytes": 0,
            "regular_count": len(files), "anchor_peer_ratios": [],
            "max_member": max((p.stat().st_size for p in files), default=0)}
    if reason:
        return info
    sizes = [p.stat().st_size for p in files]
    if not MIN_MEMBERS <= len(files) <= MAX_MEMBERS:
        info["reason"] = "member_count"; return info
    if max(sizes) > MAX_MEMBER_BYTES or sum(sizes) > MAX_LOGICAL_BYTES:
        info["reason"] = "bounded_budget"; return info
    if min(sizes) < WINDOW_BYTES:
        info["reason"] = "too_small_for_cheap_anchor"; return info
    reference, others = _windows(files[0], sizes[0])
    # Pure byte structure: sample stable offset windows, then compare 48-byte
    # shingles across peers without using filename, extension or corpus identity.
    windows_by_file = [reference]
    info["sample_bytes"] += others
    for p, n in zip(files[1:], sizes[1:]):
        ws, b = _windows(p, n)
        windows_by_file.append(ws)
        info["sample_bytes"] += b
    anchors = set()
    for w in reference:
        for j in range(0, len(w) - ANCHOR_BYTES + 1, ANCHOR_STRIDE):
            anchors.add(w[j:j + ANCHOR_BYTES])
    if not anchors:
        info["reason"] = "no_reference_anchors"; return info
    hits = []
    for windows in windows_by_file[1:]:
        hits.append(sum(any(anchor in w for w in windows) for anchor in anchors) / len(anchors))
    info["anchor_peer_ratios"] = [round(v, 6) for v in hits]
    info["shared_peers"] = sum(v >= MIN_SHARED_RATIO for v in hits)
    info["eligible"] = info["shared_peers"] >= MIN_LINKED_PEERS
    info["reason"] = "prospective_shared_anchors" if info["eligible"] else "no_shared_anchors"
    return info


def _normalize(source: Path) -> None:
    for p in sorted(source.rglob("*")):
        if p.is_symlink():
            continue
        if p.is_file():
            p.chmod(0o644)
            os.utime(p, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    for p in sorted((p for p in source.rglob("*") if p.is_dir()), reverse=True):
        p.chmod(0o755)
        os.utime(p, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    os.utime(source, (NORMALIZED_MTIME, NORMALIZED_MTIME))


def _make_case(root: Path, family: str) -> Path:
    source = root / "source"
    source.mkdir()
    rng = random.Random(170423)
    if family in ("related_shift", "related_boundary"):
        base = rng.randbytes(72 * 1024)
        for i in range(6):
            if family == "related_shift":
                k = 1000 + i * 59
                raw = base[:k] + (b"x" * (i + 7)) + base[k:]
            else:
                k = len(base) - 1024 - i * 57
                raw = base[:k] + (b"z" * (11 + i)) + base[k:]
            (source / f"part{i:02d}.bin").write_bytes(raw)
    elif family == "independent_entropy":
        for i in range(6):
            (source / f"part{i:02d}.bin").write_bytes(rng.randbytes(72 * 1024))
    elif family == "duplicate_content":
        base = rng.randbytes(72 * 1024)
        for i in range(6):
            (source / f"part{i:02d}.bin").write_bytes(base)
    elif family == "tiny":
        for i in range(12):
            (source / f"part{i:02d}.bin").write_bytes((b"tiny|" + bytes([i])) * 8)
    elif family == "sparse":
        for i in range(4):
            with (source / f"part{i:02d}.bin").open("wb") as f:
                f.seek(1024 * 1024)
                f.write(bytes([i + 1]))
    elif family == "symlink":
        base = rng.randbytes(72 * 1024)
        for i in range(4):
            (source / f"part{i:02d}.bin").write_bytes(base)
        os.symlink("part00.bin", source / "alias")
    elif family == "hardlink":
        base = rng.randbytes(72 * 1024)
        (source / "part00.bin").write_bytes(base)
        os.link(source / "part00.bin", source / "part01.bin")
        for i in range(2, 5):
            (source / f"part{i:02d}.bin").write_bytes(base)
    else:
        raise KeyError(family)
    _normalize(source)
    return source



def _tree_signature(root: Path) -> dict:
    """Independent POSIX-level source/restore signature, no BDC/FS decoder."""
    rows = {}
    inode_groups = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        st = os.lstat(path)
        base = {"mode": stat.S_IMODE(st.st_mode), "mtime_ns": st.st_mtime_ns}
        if stat.S_ISLNK(st.st_mode):
            base["kind"] = "symlink"
            base["target"] = os.readlink(path)
        elif stat.S_ISDIR(st.st_mode):
            base["kind"] = "directory"
        elif stat.S_ISREG(st.st_mode):
            base["kind"] = "file"
            base["size"] = st.st_size
            base["sha256"] = sha(path.read_bytes())
            inode_groups.setdefault((st.st_dev, st.st_ino), []).append(rel)
        else:
            raise AssertionError("unsupported source object in test")
        rows[rel] = base
    shared = sorted(sorted(g) for g in inode_groups.values() if len(g) > 1)
    return {"rows": rows, "hardlink_groups": shared}


def run_one(root: Path, family: str) -> dict:
    source = _make_case(root, family)
    source_signature = _tree_signature(source)
    t0 = time.perf_counter()
    probe = screen(source)
    probe["wall_s"] = time.perf_counter() - t0
    archive = root / "r24.cmpct"
    t0 = time.perf_counter()
    cpu0 = time.process_time()
    Builder(source, workers=1, reproducible=False).build(archive)
    canonical_wall = time.perf_counter() - t0
    canonical_cpu = time.process_time() - cpu0
    restored = root / "r24_restored"
    with CMPCT(archive) as reader:
        reader.verify()
        reader.extractall(restored, metadata=True)
    if _tree_signature(restored) != source_signature:
        raise AssertionError(f"{family}: canonical r24 physical filesystem signature mismatch")
    row = {"family": family, "screen": probe, "canonical": {
        "complete_bytes": archive.stat().st_size,
        "physical_sha256": sha(archive.read_bytes()),
        "create_wall_s": canonical_wall, "create_cpu_s": canonical_cpu,
        "filesystem_exact": True}}
    if not probe["eligible"]:
        row["candidate"] = None
        row["decision"] = "GENUINE_R24_FALLBACK_NO_CANDIDATE"
        return row
    manifest, regular, _ = FROZEN._capture(source)
    t0 = time.perf_counter()
    cpu0 = time.process_time()
    sibling, measurements = FROZEN._encode_sibling(manifest, regular)
    measurements["create_wall_s"] = time.perf_counter() - t0
    measurements["create_cpu_s"] = time.process_time() - cpu0
    control, bdc, manifest_back = FROZEN._parse_sibling(sibling)
    if manifest_back != manifest:
        raise AssertionError(f"{family}: sibling logical manifest mismatch")
    materialized = root / "research_restored"
    recaptured = FROZEN._materialize_and_recapture(
        manifest_back, FROZEN._decoded_regular_map(control, bdc), materialized)
    if recaptured != manifest:
        raise AssertionError(f"{family}: research sibling filesystem mismatch")
    locality = FROZEN._candidate_locality(control, bdc)
    if not locality["passed"]:
        raise AssertionError(f"{family}: candidate locality exceeded prereg bounds")
    tampered = bytearray(sibling)
    tampered[len(tampered) // 2] ^= 1
    try:
        FROZEN._parse_sibling(bytes(tampered))
    except Exception:
        measurements["corruption_rejected"] = True
    else:
        raise AssertionError(f"{family}: corrupted sibling was accepted")
    measurements.update(locality)
    measurements["research_only"] = True
    row["candidate"] = measurements
    # This is the absolute uncharged-framing HEADROOM against the genuine
    # r24 floor. Reader grammar/admission overhead must be paid later; the
    # sibling is not a supported r24/r25 archive and cannot ship as-is.
    budget = archive.stat().st_size - len(sibling) - 1
    row["max_additional_bytes_for_strict_r24_win"] = budget
    row["decision"] = ("PROSPECTIVE_NONCANONICAL_HEADROOM" if budget >= 0
                       else "CANONICAL_R24_WINS_COMPLETE_BYTES")
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    families = ("related_shift", "related_boundary", "independent_entropy",
                "duplicate_content", "tiny", "sparse", "symlink", "hardlink")
    result = {"schema": "cmpct-v031-bdc-prospective-admission-oracle-v1",
              "hypothesis": "cheap generic shingle screen retains useful related-data headroom "
                            "and rejects unrelated or semantically costly sources",
              "scope": "research only; no actual CMPCT reader/format admission",
              "screen_constants": {"min_members": MIN_MEMBERS, "max_members": MAX_MEMBERS,
                  "max_member": MAX_MEMBER_BYTES, "max_logical": MAX_LOGICAL_BYTES,
                  "window": WINDOW_BYTES, "anchor": ANCHOR_BYTES,
                  "stride": ANCHOR_STRIDE, "threshold": MIN_SHARED_RATIO},
              "rows": [], "product_credit": False, "release_credit": False}
    for family in families:
        with tempfile.TemporaryDirectory(prefix="cmpct-bdc-admission-" + family + "-") as d:
            try:
                result["rows"].append(run_one(Path(d), family))
            except Exception:
                result["rows"].append({"family": family, "error": traceback.format_exc(),
                                       "decision": "INDETERMINATE_OR_FAIL"})
    positive = [r for r in result["rows"] if r["family"].startswith("related_")]
    controls = [r for r in result["rows"] if r["family"] in
                ("independent_entropy", "tiny", "sparse", "symlink", "hardlink")]
    result["oracle_positive"] = (
        any(r.get("decision") == "PROSPECTIVE_NONCANONICAL_HEADROOM" for r in positive)
        and all(r.get("decision") == "GENUINE_R24_FALLBACK_NO_CANDIDATE" for r in controls)
    )
    result["errors"] = [r["family"] for r in result["rows"] if "error" in r]
    result["process_peak_rss_kib_upper_bound"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["decision"] = ("PROSPECTIVE_ORACLE_POSITIVE" if result["oracle_positive"]
                          else "SCREEN_FALSIFIED_OR_NARROWED")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["errors"]:
        raise SystemExit("instrument or exactness failure; do not reinterpret as a negative screen result")


if __name__ == "__main__":
    main()
