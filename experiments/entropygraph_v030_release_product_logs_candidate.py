from __future__ import annotations

"""Promoted structural logs-inverse wrapper for the v0.30 release product.

This module wraps, rather than mutates, the mature v0.30 release-product implementation. A source is considered
only when it contains at least two compressed sidecars with an uncompressed sibling, then the real shipping r24
and canonical logs candidates are constructed. Logs terminates the expensive generic r25 search only when measured
candidate facts match the all-15 frozen admission proof: at least two proven inverse edges, >=1 MiB saving versus
r24, logs/r24 <=0.80, <=8x member-read amplification and <=8 MiB decode context. No benchmark name participates
in dispatch.

The frozen admission oracle separately proved that every admitted benchmark row is also strictly below accepted
v0.29, the predecessor product, ZIP and solid Zstd-19 in size and beats ZIP/Zstd-19 creation wall-clock. Native
production dispatch, Android/JNI parity and both all-15 selector shadow gates were green on the exact promotion
parent fingerprint. Non-admitted sources delegate byte-for-byte to the mature release product.

The wrapper imports the preserved mature implementation directly. This keeps direct candidate/oracle imports
acyclic after the public release-product module binds these promoted operations, while preserving the exact same
base Git blob for every non-logs path.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path, PurePosixPath
import tempfile
import time

import msgpack

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_logs_fused_extract as LOGS_FUSED
from experiments import entropygraph_v030_release_product_base as BASE

# Freeze mature delegates explicitly. They remain stable even after the public release-product facade is rebound.
_BASE_TREEHASH = BASE.treehash
_BASE_REVISION_FOR_ARCHIVE = BASE._revision_for_archive
_BASE_BUILD = BASE.build
_BASE_STRONG_VERIFY = BASE.strong_verify
_BASE_LIST_MEMBERS = BASE.list_members
_BASE_READ_MEMBER_WITH_STATS = BASE.read_member_with_stats
_BASE_EXTRACT = BASE.extract
_BASE_BUILD_ABLATION = BASE.build_ablation

REVISION = BASE.REVISION
G04_MAGIC = BASE.G04_MAGIC
G04_TAIL = BASE.G04_TAIL
PG_MAGIC = BASE.PG_MAGIC
PG_TAIL = BASE.PG_TAIL
R24_MAGIC = BASE.R24_MAGIC
POLICY = BASE.POLICY
FS = BASE.FS
CMPCT = BASE.CMPCT
R24_CODEC = BASE.R24_CODEC
C = BASE.C
ProfileNotEligible = BASE.ProfileNotEligible
UnsupportedArchiveProfile = BASE.UnsupportedArchiveProfile
MAX_MANIFEST_ENTRIES = BASE.MAX_MANIFEST_ENTRIES
MAX_PROFILE_FILES = BASE.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = BASE.MAX_PROFILE_LOGICAL_BYTES

LOGS_MAGIC = LOGS.V2.P.MAGIC
LOGS_TAIL = LOGS.V2.P.TAIL_MAGIC
LOGS_PROFILE = LOGS.PROFILE
MIN_SIDECAR_PAIRS = 2
MIN_INVERSE_EDGES = 2
MIN_SAVING_BYTES = 1024 * 1024
MAX_LOGS_TO_R24_RATIO = 0.80
MAX_MEMBER_AMPLIFICATION = 8.0
MAX_DECODE_UNIT_BYTES = 8 * 1024 * 1024


def treehash(root: Path) -> str:
    return _BASE_TREEHASH(root)


def _regular_paths(root: Path) -> set[str]:
    root = Path(root)
    out: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_file() and not path.is_symlink():
                out.add(path.relative_to(root).as_posix())
    return out


def logs_source_prefilter(root: Path) -> dict:
    """Prove the minimum sidecar shape without materializing the whole source-path set.

    Eligibility needs only two compressed sidecars whose uncompressed sibling exists in the same directory.
    The real candidate builder later performs exact edge discovery, so walking every remaining directory after
    those two witnesses are found is pure speculative work.  Deterministic ``scandir`` order keeps diagnostics
    stable while allowing the positive path to terminate as soon as the structural lower bound is proven.
    """
    root = Path(root)
    pairs: list[tuple[str, str]] = []
    stack: list[tuple[Path, str]] = [(root, "")]
    while stack:
        abs_dir, prefix = stack.pop()
        with os.scandir(abs_dir) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
        regular_names = {
            item.name
            for item in entries
            if item.is_file(follow_symlinks=False)
        }
        for name in sorted(regular_names):
            for suffix in (".gz", ".zst"):
                if not name.endswith(suffix):
                    continue
                sibling_name = name[: -len(suffix)]
                if sibling_name in regular_names:
                    rel = f"{prefix}/{name}" if prefix else name
                    sibling = f"{prefix}/{sibling_name}" if prefix else sibling_name
                    pairs.append((rel, sibling))
                    if len(pairs) >= MIN_SIDECAR_PAIRS:
                        return {
                            "sidecar_pairs": len(pairs),
                            "sidecar_pairs_exact": False,
                            "pair_examples": pairs[:8],
                            "eligible": True,
                            "scan_terminated_at_admission_floor": True,
                        }
                break
        for item in reversed(entries):
            if item.is_dir(follow_symlinks=False):
                child_prefix = f"{prefix}/{item.name}" if prefix else item.name
                stack.append((Path(item.path), child_prefix))
    return {
        "sidecar_pairs": len(pairs),
        "sidecar_pairs_exact": True,
        "pair_examples": pairs[:8],
        "eligible": False,
        "scan_terminated_at_admission_floor": False,
    }


def _logs_manifest(archive: Path) -> dict:
    raw = LOGS._manifest_from_archive(Path(archive))
    return FS.decode_manifest(
        raw,
        max_path_bytes=LOGS.MAX_PATH_BYTES,
        max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
    )


def _logs_semantic_tree(decoded: dict) -> str:
    """Project the authenticated logs filesystem manifest into the canonical user-tree hash grammar."""
    rows = []
    for row in sorted(decoded["manifest"]["entries"], key=lambda item: item[0]):
        rel, kind, _mode, _mtime, _uid, _gid, _xattrs, extra = row
        if kind == "f":
            size, digest = extra
            semantic = [rel, "f", int(size), bytes(digest)]
        elif kind == "d":
            semantic = [rel, "d"]
        elif kind == "l":
            semantic = [rel, "l", extra]
        elif kind == "h":
            semantic = [rel, "h", extra]
        else:
            raise RuntimeError(f"unknown logs filesystem entry kind {kind!r} for {rel!r}")
        rows.append(semantic)
    encoded = msgpack.packb(["cmpct-user-tree-v1", rows], use_bin_type=True)
    return hashlib.sha256(encoded).hexdigest()


def _is_logs_archive(archive: Path) -> bool:
    try:
        with Path(archive).open("rb") as handle:
            return handle.read(len(LOGS_MAGIC)) == LOGS_MAGIC
    except OSError:
        return False


def _revision_for_archive(archive: Path) -> tuple[int | None, str]:
    if _is_logs_archive(Path(archive)):
        return REVISION, LOGS_PROFILE
    return _BASE_REVISION_FOR_ARCHIVE(Path(archive))


def _build_r24(root: Path, archive: Path) -> dict:
    return dict(BASE._locality_bounded_r24_build(root, archive))


def _build_logs(root: Path, archive: Path) -> dict:
    stats = dict(LOGS.build(root, archive))
    if "max_member_read_amplification" not in stats or "max_decode_unit_bytes" not in stats:
        raise RuntimeError("logs candidate omitted required locality evidence")
    stats["archive_bytes"] = archive.stat().st_size
    return stats


def _parallel_candidates(root: Path, temp: Path) -> tuple[dict, dict, Path, Path, float]:
    r24_path = temp / "candidate-r24.cmpct"
    logs_path = temp / "candidate-logs.cmpct"
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="cmpct-v030-logs-selector") as pool:
        r24_future = pool.submit(_build_r24, root, r24_path)
        logs_future = pool.submit(_build_logs, root, logs_path)
        r24 = r24_future.result()
        logs = logs_future.result()
    return r24, logs, r24_path, logs_path, time.perf_counter() - started


def _admission(r24: dict, logs: dict) -> tuple[bool, dict]:
    r24_bytes = int(r24["archive_bytes"])
    logs_bytes = int(logs["archive_bytes"])
    saving = r24_bytes - logs_bytes
    ratio = logs_bytes / max(1, r24_bytes)
    edges = int(logs.get("edge_detection", {}).get("inverse_edges") or 0)
    amp = float(logs["max_member_read_amplification"])
    decode = int(logs["max_decode_unit_bytes"])
    facts = {
        "inverse_edges": edges,
        "saving_vs_r24_bytes": saving,
        "logs_to_r24_ratio": ratio,
        "max_member_read_amplification": amp,
        "max_decode_unit_bytes": decode,
    }
    admitted = (
        edges >= MIN_INVERSE_EDGES
        and saving >= MIN_SAVING_BYTES
        and ratio <= MAX_LOGS_TO_R24_RATIO
        and amp <= MAX_MEMBER_AMPLIFICATION
        and decode <= MAX_DECODE_UNIT_BYTES
    )
    return admitted, facts


def _build_logs_terminal_if_eligible(root: Path, out: Path) -> dict | None:
    prefilter = logs_source_prefilter(root)
    if not prefilter["eligible"]:
        return None

    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".cmpct-v030-logs-selector-", dir=out.parent) as td:
            temp = Path(td)
            r24, logs, _r24_path, logs_path, pair_create_s = _parallel_candidates(root, temp)
            admitted, admission = _admission(r24, logs)
            if not admitted:
                return None
            selected_bytes = logs_path.stat().st_size
            os.replace(logs_path, out)
    except (ProfileNotEligible, RuntimeError, OSError, ValueError):
        return None

    verified = strong_verify(out)
    if not verified.get("ok"):
        out.unlink(missing_ok=True)
        raise RuntimeError(f"terminal logs publication failed strong verification: {verified!r}")
    if int(verified.get("format_revision", -1)) != REVISION or verified.get("format_profile") != LOGS_PROFILE:
        out.unlink(missing_ok=True)
        raise RuntimeError("terminal logs publication profile identity drift")

    total_s = time.perf_counter() - started
    return {
        "selected": "logs-inverse",
        "archive_bytes": selected_bytes,
        "format_revision": REVISION,
        "format_profile": LOGS_PROFILE,
        "r24_product_bytes": int(r24["archive_bytes"]),
        "r25_product_bytes": selected_bytes,
        "r25_attempted": True,
        "r25_reject_reason": None,
        "r24": r24,
        "r25": {
            "selected": "logs-inverse",
            "archive_bytes": selected_bytes,
            "create_s": total_s,
            "portfolio_create_s": total_s,
            "g04_selected": "not-attempted",
            "g04_bytes": selected_bytes,
            "prefixgraph_contract_eligible": False,
            "prefixgraph_admitted": False,
            "prefixgraph_reject_reason": "terminal-logs-admission",
            "prefixgraph_bytes": None,
            "max_dependency_depth": 1,
            "max_selected_member_read_amplification": float(admission["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(admission["max_decode_unit_bytes"]),
            "logs": logs,
        },
        "final_strong_verify": verified,
        "portfolio_create_s": total_s,
        "logs_candidate_pair_create_s": pair_create_s,
        "selection_materialization": "same-filesystem-atomic-move",
        "selection_extra_payload_write_bytes": 0,
        "logs_terminal": True,
        "logs_terminal_prefilter": prefilter,
        "logs_terminal_admission": admission,
        "logs_terminal_contract": {
            "minimum_sidecar_pairs": MIN_SIDECAR_PAIRS,
            "minimum_inverse_edges": MIN_INVERSE_EDGES,
            "minimum_saving_vs_r24_bytes": MIN_SAVING_BYTES,
            "maximum_logs_to_r24_ratio": MAX_LOGS_TO_R24_RATIO,
            "maximum_member_read_amplification": MAX_MEMBER_AMPLIFICATION,
            "maximum_decode_unit_bytes": MAX_DECODE_UNIT_BYTES,
            "benchmark_name_dispatch": False,
        },
        "release_facade": "cmpct-v030-release-product-v1",
    }


def build(root: Path, out: Path) -> dict:
    root = Path(root)
    out = Path(out)
    terminal = _build_logs_terminal_if_eligible(root, out)
    if terminal is not None:
        return terminal
    stats = dict(_BASE_BUILD(root, out))
    stats["logs_terminal"] = False
    stats["logs_terminal_prefilter"] = logs_source_prefilter(root)
    stats["release_facade"] = "cmpct-v030-release-product-v1"
    return stats


def strong_verify(archive: Path) -> dict:
    archive = Path(archive)
    if not _is_logs_archive(archive):
        return _BASE_STRONG_VERIFY(archive)
    try:
        verified = dict(LOGS.strong_verify(archive))
        decoded = _logs_manifest(archive)
        user_tree = _logs_semantic_tree(decoded)
        if not verified.get("ok"):
            raise RuntimeError(f"logs verifier returned non-green result: {verified!r}")
        return {
            **verified,
            "tree_sha256": user_tree,
            "user_tree_sha256": user_tree,
            "format_revision": REVISION,
            "format_profile": LOGS_PROFILE,
            "filesystem_manifest_sha256": hashlib.sha256(decoded["raw"]).hexdigest(),
            "filesystem_entries": len(decoded["manifest"]["entries"]),
            "filesystem_semantics_verified": True,
            "reader": "cmpct-v030-logs-inverse-v3",
            "canonical_release_facade": "cmpct-v030-release-product-v1",
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "format_revision": REVISION,
            "format_profile": LOGS_PROFILE,
            "reader": "cmpct-v030-logs-inverse-v3",
        }


def _entry_rows(archive: Path) -> tuple[dict, dict[str, list]]:
    decoded = _logs_manifest(archive)
    return decoded, FS.entry_map(decoded)


def list_members(archive: Path) -> list[dict]:
    archive = Path(archive)
    if not _is_logs_archive(archive):
        return _BASE_LIST_MEMBERS(archive)
    decoded, rows = _entry_rows(archive)
    result = []
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    for rel in sorted(rows):
        row = rows[rel]
        kind = row[1]
        extra = row[7]
        if kind == "f":
            size = int(extra[0])
        elif kind == "h":
            size = int(decoded["regular"][extra][0])
        elif kind == "l":
            size = len(extra.encode("utf-8"))
        else:
            size = 0
        result.append({"path": rel, "kind": names[kind], "size": size})
    return result


def read_member_with_stats(archive: Path, rel: str) -> tuple[bytes, dict]:
    archive = Path(archive)
    if not _is_logs_archive(archive):
        return _BASE_READ_MEMBER_WITH_STATS(archive, rel)
    decoded, rows = _entry_rows(archive)
    if rel not in rows:
        raise KeyError(rel)
    row = rows[rel]
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        raw = row[7].encode("utf-8")
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": len(raw),
            "decoded_context_amplification": 1.0,
            "format_profile": LOGS_PROFILE,
        }
    owner = row[7] if kind == "h" else rel
    with LOGS.Archive(archive) as reader:
        paths = reader._paths()
        try:
            index = paths.index(owner)
        except ValueError as exc:
            raise RuntimeError(f"logs filesystem owner missing from content graph: {owner!r}") from exc
        raw, context = reader.read_member(index)
    amp = int(context) / max(1, len(raw))
    if amp > MAX_MEMBER_AMPLIFICATION or int(context) > MAX_DECODE_UNIT_BYTES:
        raise RuntimeError("logs public read exceeded locality contract")
    return raw, {
        "logical_bytes": len(raw),
        "decoded_context_bytes": int(context),
        "decoded_context_amplification": amp,
        "format_profile": LOGS_PROFILE,
    }


def read_member(archive: Path, rel: str) -> bytes:
    return read_member_with_stats(archive, rel)[0]


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    if not _is_logs_archive(archive):
        return _BASE_EXTRACT(archive, dst, max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
    return LOGS_FUSED.extract(
        archive,
        dst,
        max_output_bytes=max_output_bytes,
        safe_symlinks=safe_symlinks,
    )


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    return _BASE_BUILD_ABLATION(root, out, mode)
