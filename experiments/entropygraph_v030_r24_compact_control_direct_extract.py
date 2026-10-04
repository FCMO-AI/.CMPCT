"""Research-only direct C25CC01 extraction over the authenticated mature-r24 semantic owner.

The shipping compact-control reader already expands authenticated C25CC01 control exactly to the ordinary r24 index
and presents the unchanged physical payload span through ``_direct_r24_reader``. The current C25CC01 extraction path
nevertheless rebuilds that index into a second r24 archive, compresses the compatibility control, writes the complete
archive to a temporary file, reopens/maps it, and only then calls the mature extractor.

This module removes only that compatibility materialization. It retains the exact mature ``CMPCT.extractall`` owner,
caller output budget, safe-symlink policy, C25CC01 control authentication, compact-control locality audit, and
transactional publication helper. It is deliberately research-only until exact output/error identity and timing
prove that the compatibility archive can be removed from the canonical path.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = PRODUCT.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    dst = Path(dst)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    parsed = CC._parse(archive)
    CC._audit_s_pack_locality(parsed["index"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-c25-direct-", dir=dst.parent))
    installed = False
    try:
        with CC._direct_r24_reader(parsed) as reader:
            reader.extractall(staging, max_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
        # Canonical final publication already provides rollback-on-replace semantics. Reuse that exact owner rather
        # than growing a second transactional filesystem grammar in this experiment.
        PRODUCT._BASE_IMPL.C._publish_tree(staging, dst)
        installed = True
    finally:
        if not installed and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
