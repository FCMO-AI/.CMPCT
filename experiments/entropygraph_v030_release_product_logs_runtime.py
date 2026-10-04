"""Canonical productization boundary for the proven one-session logs extractor.

This module preserves the promoted structural logs selector/format/reader surface byte-for-byte and replaces only
logs extraction with the exact semantic-owner path that earned an exact-head 11-round promotion signal. Non-logs
archives continue through the mature promoted product unchanged. No archive bytes, selector facts, locality rules,
recovery rules, or release thresholds are changed here.

The fused extractor opens one authenticated logs Archive session, proves graph (size, SHA-256) identities equal the
authenticated filesystem manifest, shares member/pack decode caches for the operation, restores each logical value
once, and avoids both materializing the internal manifest and the second on-disk SHA-256 pass. Final release credit
still belongs exclusively to the ordinary exact-candidate authority.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_logs_fused_extract as FUSED

# Re-export the promoted product surface first; override extraction below only.
for _name in dir(PRODUCT):
    if not _name.startswith("__"):
        globals()[_name] = getattr(PRODUCT, _name)


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = PRODUCT.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    if not PRODUCT._is_logs_archive(archive):
        return PRODUCT.extract(
            archive,
            dst,
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )
    return FUSED.extract(
        archive,
        dst,
        max_output_bytes=max_output_bytes,
        safe_symlinks=safe_symlinks,
    )


PROMOTED_LOGS_ONE_SESSION_EXTRACTION = True
PROMOTED_LOGS_ONE_SESSION_EXTRACTION_EVIDENCE = (
    "exact-head 11-round A/B: 55.578 ms -> 42.844 ms median (22.91% faster), exact outputs; "
    "one authenticated archive session; no second on-disk SHA-256 pass"
)
