"""Promotion-policy facade for the streamed CMPCT v0.30 release reader.

``entropygraph_v030_release_reader`` owns the bounded streaming mechanics. This facade deliberately owns the
stricter *promotion* admission rules that should not be hidden inside transform/graph code:

- canonical PrefixGraph path order must match the tree-hash order;
- direct PrefixGraph bases are exactly integer ``-1`` (no string/float coercion);
- dependency-depth/resource declarations use exact numeric types rather than permissive ``int()``/``float()``
  conversions;
- G0-G4 locality declarations must be finite, non-boolean values within policy;
- optional duplicate decode/memory metadata declarations, when present, must match exact integer policy.

The authenticated G0-G4 header remains authoritative for decode-unit and decoder-memory ceilings. The facade
therefore never requires those values to be redundantly present in metadata; it only tightens their type if a
future writer chooses to duplicate them there.

The facade installs these validators into the streamed reader once, then delegates verification/extraction.
This works because metadata decoders resolve their validator globals at call time. Writer bytes are untouched.

Footnote: keeping promotion policy as a narrow adapter is intentional during convergence. After the format is
frozen, these checks can be folded into the owning reader without changing archive bytes; until then, one
single-sourced streamed implementation is safer than maintaining two almost-identical decoders.
"""
from __future__ import annotations

import math
from pathlib import Path

from experiments import entropygraph_v030_release_reader as R

_BASE_G04_VALIDATE = R._validate_g04_meta
_BASE_PG_VALIDATE = R._validate_pg_meta
_BASE_G04_OPEN = R._g04_open
_INSTALLED = False


def _strict_g04_validate(meta: object, expected_count: int | None = None) -> dict:
    result = _BASE_G04_VALIDATE(meta, expected_count)

    amp = result.get("max_geometry_member_read_amplification")
    if isinstance(amp, bool) or not isinstance(amp, (int, float)) or not math.isfinite(float(amp)):
        raise RuntimeError("G0-G4 locality declaration must be a finite number")
    if float(amp) > R.MAX_MEMBER_READ_AMP:
        raise RuntimeError("G0-G4 locality declaration exceeds release policy")

    # Footnote: max-decode/max-memory are authenticated in the fixed archive header. Metadata duplication is
    # optional. If duplicated, forbid coercive strings/floats/bools and require the duplicate to stay in policy.
    if "max_decode_unit" in result:
        max_decode = result["max_decode_unit"]
        if not isinstance(max_decode, int) or isinstance(max_decode, bool) or max_decode < 1:
            raise RuntimeError("G0-G4 decode-unit metadata declaration must be an exact positive integer")
        if max_decode > R.G04.MAX_DECODE_UNIT:
            raise RuntimeError("G0-G4 decode-unit metadata declaration exceeds release policy")

    if "max_decoder_memory" in result:
        max_memory = result["max_decoder_memory"]
        if not isinstance(max_memory, int) or isinstance(max_memory, bool) or max_memory < 1:
            raise RuntimeError("G0-G4 decoder-memory metadata declaration must be an exact positive integer")
        if max_memory > R.G04.MAX_DECODER_MEMORY:
            raise RuntimeError("G0-G4 decoder-memory metadata declaration exceeds release policy")
    return result


def _strict_pg_validate(meta: object) -> dict:
    result = _BASE_PG_VALIDATE(meta)
    rels = result["files"]

    # The PrefixGraph writer already emits sorted paths. Requiring that canonical order at read time prevents
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


def _g04_open_reuse_identical_metadata(archive: Path) -> tuple[object, dict, int, list[int], bytes, bool]:
    """Open G04 while decoding an exactly duplicated authenticated metadata blob only once.

    Canonical writers store the same compressed metadata bytes at the head and tail. The historical recovery
    reader independently decompressed and parsed both copies even when every authenticated declaration and the
    compressed bytes were identical. That duplicate work is unnecessary on the healthy path: once the primary
    copy has passed bounded decompression, SHA-256, schema validation and Merkle validation, an identical tail
    byte string with the same raw-size/digest/Merkle declarations denotes that exact already-validated object.

    Any difference takes the historical independent tail-decode path. A bad/missing primary therefore still
    recovers from the tail, a bad tail still leaves an authenticated primary available under the existing law,
    and two independently authenticated but conflicting copies are still rejected. Archive bytes are untouched.
    """
    size = archive.stat().st_size
    stream = archive.open("rb")
    primary = None
    tail = None
    primary_error = None
    tail_error = None
    primary_comp: bytes | None = None
    primary_mus: int | None = None

    try:
        try:
            stream.seek(0)
            header = stream.read(R.G04.HDR.size)
            if len(header) != R.G04.HDR.size:
                raise RuntimeError("short G0-G4 primary header")
            magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = R.G04.HDR.unpack(header)
            if magic != R.G04.MAG:
                raise RuntimeError("not G0-G4 archive")
            R._int(mcs, "G0-G4 primary compressed metadata", maximum=R.MAX_META_BYTES)
            R._int(mus, "G0-G4 primary metadata", maximum=R.MAX_META_BYTES)
            R._int(count, "G0-G4 primary record count", maximum=R.MAX_NODES)
            if max_decode > R.G04.MAX_DECODE_UNIT or max_memory > R.G04.MAX_DECODER_MEMORY:
                raise RuntimeError("G0-G4 primary resource declaration exceeds policy")
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short G0-G4 primary metadata")
            meta = R._decode_g04_meta(comp, mus, meta_sha, count)
            if R.G04.O._merkle_root(list(meta["record_leaf_sha256"])) != merkle:
                raise RuntimeError("G0-G4 primary Merkle mismatch")
            primary = (meta, int(mcs), meta_sha, merkle)
            primary_comp = comp
            primary_mus = int(mus)
        except Exception as exc:
            primary_error = exc

        try:
            if size < R.G04.FTR.size:
                raise RuntimeError("short G0-G4 tail")
            stream.seek(size - R.G04.FTR.size)
            footer = stream.read(R.G04.FTR.size)
            magic, mcs, mus, meta_sha, merkle = R.G04.FTR.unpack(footer)
            if magic != R.G04.TAIL:
                raise RuntimeError("G0-G4 tail magic")
            R._int(mcs, "G0-G4 tail compressed metadata", maximum=R.MAX_META_BYTES)
            R._int(mus, "G0-G4 tail metadata", maximum=R.MAX_META_BYTES)
            meta_offset = size - R.G04.FTR.size - mcs
            if meta_offset < R.G04.HDR.size:
                raise RuntimeError("G0-G4 tail metadata offset")
            stream.seek(meta_offset)
            comp = stream.read(mcs)
            if len(comp) != mcs:
                raise RuntimeError("short G0-G4 tail metadata")

            if (
                primary is not None
                and primary_comp is not None
                and primary_mus is not None
                and comp == primary_comp
                and int(mus) == primary_mus
                and meta_sha == primary[2]
                and merkle == primary[3]
            ):
                meta = primary[0]
            else:
                meta = R._decode_g04_meta(comp, mus, meta_sha, None)
                if R.G04.O._merkle_root(list(meta["record_leaf_sha256"])) != merkle:
                    raise RuntimeError("G0-G4 tail Merkle mismatch")
            tail = (meta, int(mcs), meta_sha, merkle, meta_offset)
        except Exception as exc:
            tail_error = exc

        if primary is None and tail is None:
            raise RuntimeError(
                f"no authenticated G0-G4 metadata: primary={primary_error!r}; tail={tail_error!r}"
            )
        if primary is not None and tail is not None and (primary[2] != tail[2] or primary[3] != tail[3]):
            raise RuntimeError("conflicting authenticated G0-G4 metadata copies")

        chosen = primary if primary is not None else tail
        assert chosen is not None
        meta = chosen[0]
        mcs = chosen[1]
        record_start = R.G04.HDR.size + mcs
        offsets = list(meta["record_rel_offsets"])

        expected_rel = 0
        for rel in offsets:
            if rel != expected_rel:
                raise RuntimeError("G0-G4 physical table contains gap or overlap")
            stream.seek(record_start + rel)
            header = stream.read(R.PH.size)
            if len(header) != R.PH.size:
                raise RuntimeError("short G0-G4 physical header during preflight")
            codec, usize, csize, _crc, _logical_sha = R.PH.unpack(header)
            if codec not in (R.G04.O.CODEC_RAW, R.G04.O.CODEC_ZSTD, R.G04.O.CODEC_PREFLATE):
                raise RuntimeError("unknown G0-G4 physical codec during preflight")
            R._int(usize, "G0-G4 physical decode size", maximum=R.G04.MAX_DECODE_UNIT)
            R._int(csize, "G0-G4 physical payload size", maximum=R.G04.MAX_DECODE_UNIT + 1024 * 1024)
            expected_rel += R.PH.size + csize
        physical_end = record_start + expected_rel
        if tail is not None:
            if physical_end != tail[4]:
                raise RuntimeError("G0-G4 physical endpoint does not bind authenticated tail")
        elif physical_end > size:
            raise RuntimeError("G0-G4 physical endpoint exceeds archive")
        return stream, meta, record_start, offsets, chosen[3], tail is not None
    except Exception:
        stream.close()
        raise


def install_policy() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    R._validate_g04_meta = _strict_g04_validate
    R._validate_pg_meta = _strict_pg_validate
    R._g04_open = _g04_open_reuse_identical_metadata
    _INSTALLED = True


install_policy()


def strong_verify(archive: Path) -> dict:
    return R.strong_verify(archive)


def extract(archive: Path, dst: Path, *, max_output_bytes: int = R.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    return R.extract(archive, dst, max_output_bytes=max_output_bytes)


def extract_verified_into_staging(
    archive: Path,
    staging: Path,
    *,
    max_output_bytes: int = R.DEFAULT_MAX_EXTRACT_BYTES,
) -> dict:
    """Stream one r25 profile directly into an unpublished caller-owned staging tree.

    The ordinary public ``extract`` remains transactional and unchanged.  Canonical r25 already owns a wider
    transaction because it must restore authenticated filesystem metadata after graph extraction.  Calling the
    ordinary extractor from inside that transaction created a redundant nested temp-directory + rename cycle.

    This hook reuses the exact same bounded/authenticated G0-G4 or PrefixGraph streamer and promotion validators;
    it merely lets the canonical parent own publication once.  Research/accepted-v0.29 grammars are deliberately
    rejected here so no caller can accidentally bypass their own extraction boundary.
    """
    max_output_bytes = R._int(
        max_output_bytes,
        "extraction output budget",
        minimum=1,
        maximum=R.MAX_DECLARED_LOGICAL_BYTES,
    )
    archive = Path(archive)
    staging = Path(staging)
    if staging.exists() and any(staging.iterdir()):
        raise RuntimeError("verified staging extraction requires an empty target directory")
    staging.mkdir(parents=True, exist_ok=True)
    magic = R._magic(archive)
    if magic == R.G04.MAG:
        return R._stream_g04(archive, staging, max_output_bytes)
    if magic == R.PG.MAGIC:
        return R._stream_pg(archive, staging, max_output_bytes)
    raise RuntimeError("verified staging extraction accepts canonical r25 graph profiles only")


def treehash(root: Path) -> str:
    return R.treehash(root)


DEFAULT_MAX_EXTRACT_BYTES = R.DEFAULT_MAX_EXTRACT_BYTES
MAX_DECLARED_LOGICAL_BYTES = R.MAX_DECLARED_LOGICAL_BYTES
MAX_MEMBER_READ_AMP = R.MAX_MEMBER_READ_AMP
MAX_RECORD_CACHE_BYTES = R.MAX_RECORD_CACHE_BYTES
MAX_NODE_CACHE_BYTES = R.MAX_NODE_CACHE_BYTES
PROMOTED_G04_IDENTICAL_METADATA_REUSE = True
