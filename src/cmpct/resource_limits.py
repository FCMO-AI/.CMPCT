from __future__ import annotations

"""Shared hostile-input resource policy, cheap to import from the ordinary Reader.

The strict structural validator re-exports these exact objects; do not duplicate
defaults or exception classes. Signed generations are bounded *before* decode.
"""

from dataclasses import dataclass
import os


class ValidationError(IOError):
    """Archive structure is invalid or unsafe to hand to the reference reader."""


class ResourceLimitError(ValidationError):
    """Archive metadata exceeds an explicit hostile-input resource ceiling."""


@dataclass(frozen=True)
class ParserLimits:
    """Configurable implementation ceilings; these are not yet revision-24 format maxima.

    Footnote: final interoperability maxima belong in the normative 1.0 specification. These generous
    defaults simply ensure a tiny hostile archive cannot request unbounded Python objects or decode
    buffers while the pre-1.0 format is still being hardened.
    """

    max_index_bytes: int = 256 * 1024 * 1024
    max_generation_bytes: int = 256 * 1024 * 1024
    max_blob_bytes: int = 1024 * 1024 * 1024
    max_files: int = 4_000_000
    max_blobs: int = 4_000_000
    max_recipes: int = 1_000_000
    max_path_bytes: int = 1024 * 1024
    max_delta_depth: int = 128

    @classmethod
    def from_env(cls) -> "ParserLimits":
        base = cls()

        def read(name: str, default: int) -> int:
            raw = os.environ.get(name)
            if raw is None:
                return default
            try:
                value = int(raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be an integer") from exc
            if value <= 0:
                raise ValueError(f"{name} must be positive")
            return value

        return cls(
            max_index_bytes=read("CMPCT_MAX_INDEX_BYTES", base.max_index_bytes),
            max_generation_bytes=read("CMPCT_MAX_GENERATION_BYTES", base.max_generation_bytes),
            max_blob_bytes=read("CMPCT_MAX_BLOB_BYTES", base.max_blob_bytes),
            max_files=read("CMPCT_MAX_FILES", base.max_files),
            max_blobs=read("CMPCT_MAX_BLOBS", base.max_blobs),
            max_recipes=read("CMPCT_MAX_RECIPES", base.max_recipes),
            max_path_bytes=read("CMPCT_MAX_PATH_BYTES", base.max_path_bytes),
            max_delta_depth=read("CMPCT_MAX_DELTA_DEPTH", base.max_delta_depth),
        )
