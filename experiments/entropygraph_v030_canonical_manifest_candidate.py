from __future__ import annotations

"""Research-only canonical integration candidate for r25 implicit filesystem control.

This module exercises the exact release-facing canonical implementation with only two
operation-scoped seams replaced: profile staging uses the already-proven content-agnostic
implicit-v4 admission law, and authenticated manifest validation accepts either the
legacy filesystem-v1 control or implicit-v4 expanded against identities from the same
selected content graph.  The shipping canonical module is restored after every call.

No benchmark identity participates in admission.  Ties and any semantic mismatch retain
filesystem-v1.  This candidate earns no release credit; it exists to falsify the exact
canonical integration shape before the shipping module is changed.
"""

from contextlib import contextmanager
from pathlib import Path
import threading

from experiments import entropygraph_v030_canonical_final as BASE
from experiments import entropygraph_v030_r25_manifest_admission as ADMIT

_LOCK = threading.RLock()


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


@contextmanager
def _candidate_context():
    """Patch only the two canonical semantic seams for one candidate operation."""
    with _LOCK:
        old_prepare = BASE._prepare_profile_tree
        old_validate = BASE._validated_manifest
        BASE._prepare_profile_tree = _prepare_profile_tree
        BASE._validated_manifest = _validated_manifest
        try:
            yield
        finally:
            BASE._prepare_profile_tree = old_prepare
            BASE._validated_manifest = old_validate


def treehash(root: Path) -> str:
    # Source-tree identity is intentionally unchanged and remains filesystem-v1 semantics.
    return BASE.treehash(root)


def build(root: Path, out: Path) -> dict:
    with _candidate_context():
        result = dict(BASE.build(root, out))
    result["manifest_productization_candidate"] = "implicit-v4-operation-scoped-v1"
    result["release_credit"] = False
    return result


def strong_verify(archive: Path) -> dict:
    with _candidate_context():
        result = dict(BASE.strong_verify(archive))
    result["manifest_productization_candidate"] = "implicit-v4-operation-scoped-v1"
    result["release_credit"] = False
    return result


def read_member_with_stats(archive: Path, rel: str):
    with _candidate_context():
        return BASE.read_member_with_stats(archive, rel)


def read_member(archive: Path, rel: str) -> bytes:
    with _candidate_context():
        return BASE.read_member(archive, rel)


def list_members(archive: Path) -> list[dict]:
    with _candidate_context():
        return BASE.list_members(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = BASE.POLICY.DEFAULT_MAX_EXTRACT_BYTES, safe_symlinks: bool = True) -> None:
    with _candidate_context():
        BASE.extract(archive, dst, max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    with _candidate_context():
        result = dict(BASE.build_ablation(root, out, mode))
    result["manifest_productization_candidate"] = "implicit-v4-operation-scoped-v1"
    result["release_credit"] = False
    return result
