"""Promotion-policy facade for the streamed CMPCT v0.30 release reader.

``entropygraph_v030_release_reader`` owns the bounded streaming mechanics.  This facade deliberately owns the
stricter *promotion* admission rules that should not be hidden inside transform/graph code:

- canonical PrefixGraph path order must match the tree-hash order;
- direct PrefixGraph bases are exactly integer ``-1`` (no string/float coercion);
- dependency-depth/resource declarations use exact numeric types rather than permissive ``int()``/``float()``
  conversions;
- G0-G4 locality/decode/memory declarations must be finite, non-boolean numeric/integer values within policy.

The facade installs these validators into the streamed reader once, then delegates verification/extraction.
This works because metadata decoders resolve their validator globals at call time.  Writer bytes are untouched.

Footnote: keeping promotion policy as a narrow adapter is intentional during convergence.  After the format is
frozen, these checks can be folded into the owning reader without changing archive bytes; until then, one
single-sourced streamed implementation is safer than maintaining two almost-identical decoders.
"""
from __future__ import annotations

import math
from pathlib import Path

from experiments import entropygraph_v030_release_reader as R

_BASE_G04_VALIDATE = R._validate_g04_meta
_BASE_PG_VALIDATE = R._validate_pg_meta
_INSTALLED = False


def _strict_g04_validate(meta: object, expected_count: int | None = None) -> dict:
    result = _BASE_G04_VALIDATE(meta, expected_count)

    amp = result.get("max_geometry_member_read_amplification")
    if isinstance(amp, bool) or not isinstance(amp, (int, float)) or not math.isfinite(float(amp)):
        raise RuntimeError("G0-G4 locality declaration must be a finite number")
    if float(amp) > R.MAX_MEMBER_READ_AMP:
        raise RuntimeError("G0-G4 locality declaration exceeds release policy")

    max_decode = result.get("max_decode_unit")
    if not isinstance(max_decode, int) or isinstance(max_decode, bool) or max_decode < 1:
        raise RuntimeError("G0-G4 decode-unit declaration must be an exact positive integer")
    if max_decode > R.G04.MAX_DECODE_UNIT:
        raise RuntimeError("G0-G4 decode-unit declaration exceeds release policy")

    max_memory = result.get("max_decoder_memory")
    if not isinstance(max_memory, int) or isinstance(max_memory, bool) or max_memory < 1:
        raise RuntimeError("G0-G4 decoder-memory declaration must be an exact positive integer")
    if max_memory > R.G04.MAX_DECODER_MEMORY:
        raise RuntimeError("G0-G4 decoder-memory declaration exceeds release policy")
    return result


def _strict_pg_validate(meta: object) -> dict:
    result = _BASE_PG_VALIDATE(meta)
    rels = result["files"]

    # The PrefixGraph writer already emits sorted paths.  Requiring that canonical order at read time prevents
    # an attacker from making logical tree identity depend on arbitrary metadata ordering even though all
    # individual file digests remain valid.
    if rels != sorted(rels):
        raise RuntimeError("PrefixGraph file table is not in canonical path order")

    for desc in result["records"]:
        if desc[0] == "direct":
            base = desc[1]
            if not isinstance(base, int) or isinstance(base, bool) or base != -1:
                raise RuntimeError("PrefixGraph direct base must be exact integer -1")

    depth = result.get("max_dependency_depth")
    if not isinstance(depth, int) or isinstance(depth, bool) or not 0 <= depth <= 1:
        raise RuntimeError("PrefixGraph dependency depth must be exact integer 0/1")
    return result


def install_policy() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    R._validate_g04_meta = _strict_g04_validate
    R._validate_pg_meta = _strict_pg_validate
    _INSTALLED = True


install_policy()


def strong_verify(archive: Path) -> dict:
    return R.strong_verify(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = R.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    return R.extract(archive, dst, max_output_bytes=max_output_bytes)


def treehash(root: Path) -> str:
    return R.treehash(root)


DEFAULT_MAX_EXTRACT_BYTES = R.DEFAULT_MAX_EXTRACT_BYTES
MAX_DECLARED_LOGICAL_BYTES = R.MAX_DECLARED_LOGICAL_BYTES
MAX_MEMBER_READ_AMP = R.MAX_MEMBER_READ_AMP
MAX_RECORD_CACHE_BYTES = R.MAX_RECORD_CACHE_BYTES
MAX_NODE_CACHE_BYTES = R.MAX_NODE_CACHE_BYTES
