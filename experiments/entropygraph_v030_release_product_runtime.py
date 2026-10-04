"""Release-product runtime composition with the proven one-session Logs extractor.

The ordinary promoted product remains the semantic and build owner. This composition changes no archive grammar,
selection, creation, locality, recovery, list/read, or verification behavior. It only routes extraction of an already-
recognized promoted Logs archive through the exact-head one-session semantic-owner extractor; every other archive
continues through the ordinary promoted release product unchanged.

This is the narrow canonicalization bridge required before changing the ordinary public binding. Release credit is
still denied until the exact candidate's full runtime, native/Android, recovery and strict authority receipts converge.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as LOGS_RUNTIME

for _name in dir(PRODUCT):
    if not _name.startswith("__"):
        globals()[_name] = getattr(PRODUCT, _name)


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = PRODUCT.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
):
    archive = Path(archive)
    if PRODUCT._LOGS_PROMOTED._is_logs_archive(archive):
        return LOGS_RUNTIME.extract(
            archive,
            dst,
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )
    return PRODUCT.extract(
        archive,
        dst,
        max_output_bytes=max_output_bytes,
        safe_symlinks=safe_symlinks,
    )


PROMOTED_LOGS_ONE_SESSION_EXTRACTION = True
PROMOTED_LOGS_ONE_SESSION_EXTRACTION_RELEASE_BRIDGE = "extract-only; all non-Logs behavior delegates to ordinary promoted release product"
