from __future__ import annotations

"""Research-only canonical integration candidate for r25 implicit filesystem control.

This module reuses the release-facing canonical primitives without mutating their module
globals. Profile staging uses the already-proven content-agnostic implicit-v4 admission
law; authenticated manifest validation accepts filesystem-v1 or implicit-v4 only after
binding it to identities from the same selected content graph.

The shipping canonical module is unchanged. No benchmark identity participates in
admission. Ties and semantic mismatches retain filesystem-v1. This candidate earns no
release credit; it exists to falsify the exact canonical integration shape before the
shipping source is changed.
"""

import hashlib
from pathlib import Path
import shutil
import tempfile

from experiments import entropygraph_v030_canonical_final as BASE
from experiments import entropygraph_v030_r25_manifest_admission as ADMIT

CANDIDATE_ID = "implicit-v4-direct-seam-v2"


def _prepare_profile_tree(root: Path, staging_root: Path) -> dict:
    prepared = ADMIT.prepare_profile_tree(
        root,
        staging_root,
        max_path_bytes=BASE.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=BASE.MAX_PROFILE_FILES,
        max_profile_logical_bytes=BASE.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=BASE.MAX_MANIFEST_ENTRIES,
    )
    if int(prepared["entries"]) > BASE.MAX_MANIFEST_ENTRIES:
        raise BASE.ProfileNotEligible("r25 filesystem manifest entry count exceeds reader policy")
    return prepared


def _validated_manifest(archive: Path) -> dict:
    raw, _stats = BASE._read_profile_member(archive, BASE.FS.FILESYSTEM_MANIFEST)
    content = BASE._profile_content_identities(archive)
    decoded, _encoding = ADMIT.decode_from_content_identities(
        raw,
        content_identities=content,
        max_path_bytes=BASE.POLICY.R.MAX_PATH_BYTES,
        max_entries=BASE.MAX_MANIFEST_ENTRIES,
    )
    return decoded


def treehash(root: Path) -> str:
    # User-tree identity remains the canonical filesystem-v1 semantic identity.
    return BASE.treehash(root)


def strong_verify(archive: Path) -> dict:
    archive = Path(archive)
    revision, profile = BASE._profile_for_archive(archive)
    if revision != BASE.REVISION:
        result = dict(BASE.strong_verify(archive))
        result["manifest_productization_candidate"] = CANDIDATE_ID
        result["release_credit"] = False
        return result

    with BASE._revision25_profile_context():
        base = dict(BASE.POLICY.strong_verify(archive))
    if not base.get("ok"):
        return {
            **base,
            "format_revision": revision,
            "format_profile": profile,
            "manifest_productization_candidate": CANDIDATE_ID,
            "release_credit": False,
        }
    try:
        manifest = _validated_manifest(archive)
        for rel, (size, digest) in manifest["regular"].items():
            raw, stats = BASE._read_profile_member(archive, rel)
            if len(raw) != size or hashlib.sha256(raw).digest() != digest:
                raise RuntimeError(f"r25 user member verification failed: {rel}")
            if stats["decoded_context_amplification"] > 8.0:
                raise RuntimeError(f"r25 member locality ceiling exceeded: {rel}")
        user_tree = BASE._semantic_tree_sha(manifest)
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "format_revision": revision,
            "format_profile": profile,
            "reader": CANDIDATE_ID,
            "manifest_productization_candidate": CANDIDATE_ID,
            "release_credit": False,
        }
    return {
        **base,
        "content_graph_tree_sha256": base.get("tree_sha256"),
        "tree_sha256": user_tree,
        "user_tree_sha256": user_tree,
        "format_revision": revision,
        "format_profile": profile,
        "filesystem_manifest_sha256": hashlib.sha256(manifest["raw"]).hexdigest(),
        "filesystem_entries": len(manifest["manifest"]["entries"]),
        "filesystem_semantics_verified": True,
        "canonical_release_facade": "cmpct-v030-canonical-final-v1",
        "manifest_productization_candidate": CANDIDATE_ID,
        "release_credit": False,
    }


def read_member_with_stats(archive: Path, rel: str):
    archive = Path(archive)
    revision, profile = BASE._profile_for_archive(archive)
    if revision != BASE.REVISION:
        return BASE.read_member_with_stats(archive, rel)
    decoded = _validated_manifest(archive)
    rows = {row[0]: row for row in decoded["manifest"]["entries"]}
    row = rows.get(rel)
    if row is None:
        raise KeyError(rel)
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        raw = row[7].encode("utf-8", "surrogateescape")
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": len(raw),
            "decoded_context_amplification": 1.0,
            "format_profile": profile,
            "member_kind": "symlink",
        }
    if kind == "h":
        raw, stats = read_member_with_stats(archive, row[7])
        return raw, {**stats, "member_kind": "hardlink", "hardlink_owner": row[7]}
    raw, stats = BASE._read_profile_member(archive, rel)
    return raw, {**stats, "member_kind": "file"}


def read_member(archive: Path, rel: str) -> bytes:
    return read_member_with_stats(archive, rel)[0]


def list_members(archive: Path) -> list[dict]:
    archive = Path(archive)
    revision, profile = BASE._profile_for_archive(archive)
    if revision != BASE.REVISION:
        return BASE.list_members(archive)
    decoded = _validated_manifest(archive)
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    result = []
    for row in decoded["manifest"]["entries"]:
        size = int(row[7][0]) if row[1] == "f" else 0
        result.append({"path": row[0], "kind": names[row[1]], "size": size})
    return result


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = BASE.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    dst = Path(dst)
    revision, profile = BASE._profile_for_archive(archive)
    if revision != BASE.REVISION:
        BASE.extract(archive, dst, max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
        return
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    decoded = _validated_manifest(archive)
    if safe_symlinks:
        BASE._validate_safe_symlinks(decoded)
    dst.parent.mkdir(parents=True, exist_ok=True)
    wrapper = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-candidate-", dir=dst.parent))
    publish_root = wrapper
    try:
        content_root = wrapper / "tree"
        internal_budget = min(
            BASE.POLICY.R.MAX_DECLARED_LOGICAL_BYTES,
            max_output_bytes + BASE.FS.MAX_MANIFEST_BYTES,
        )
        with BASE._revision25_profile_context():
            BASE.POLICY.extract(archive, content_root, max_output_bytes=internal_budget)
        BASE.FS.restore_manifest_tree(content_root, decoded, safe_symlinks=False)
        user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
        if user_bytes > max_output_bytes:
            raise RuntimeError("r25 extraction exceeds caller output budget")
        publish_root = content_root
        BASE._publish_tree(publish_root, dst)
    except Exception:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)
        raise
    else:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    """Build the same canonical r25 ablation substrate with only manifest admission changed."""
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-manifest-candidate-", dir=out.parent) as td:
        staged = Path(td) / "tree"
        prepared = _prepare_profile_tree(root, staged)
        with BASE._revision25_profile_context():
            if mode == "v029":
                stats = dict(BASE.G04_RESEARCH.BASE.build(staged, out))
            elif mode == "geometry":
                stats = dict(BASE.SHARED.build(staged, out))
            elif mode == "prefixgraph":
                expected = BASE.PG.treehash(staged)
                eligible, reason = BASE.ADMISSION.prefixgraph_eligibility(staged, expected)
                if not eligible:
                    raise BASE.ProfileNotEligible(f"PrefixGraph ablation rejected: {reason}")
                stats = dict(BASE.PG.build(staged, out))
                locality = BASE.ADMISSION.prefixgraph_locality(out)
                if not locality.get("passed"):
                    raise BASE.ProfileNotEligible("PrefixGraph ablation exceeded locality ceiling")
                stats["prefixgraph_locality"] = locality
            elif mode == "combined":
                stats = dict(BASE.RC.build(staged, out))
            else:
                raise ValueError(f"unknown v0.30 ablation mode: {mode}")
    return {
        **stats,
        "ablation": mode,
        "filesystem_manifest_sha256": prepared["manifest_sha256"],
        "filesystem_manifest_bytes": prepared["manifest_bytes"],
        "canonical_publication": False,
        "manifest_productization_candidate": CANDIDATE_ID,
        "release_credit": False,
    }
