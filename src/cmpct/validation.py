from __future__ import annotations

"""Bounded structural validation for untrusted CMPCT revision-24 archives.

Footnote: this module is an additive hostile-input gate. It validates archive-controlled lengths,
generation chains, index references and blob framing before payload decoding can allocate from those
values. It intentionally does not change revision-24 bytes or encoder policy.
"""

from dataclasses import dataclass
import os
from pathlib import Path

import msgpack

from .codec import (
    BHDR, BMAGIC, CODEC_DEFLATE, CODEC_RAW, CODEC_WAVFLAC, CODEC_ZSTD, CODEC_ZSTDDICT,
    FMAGIC, FTR, HDR, K_DIR, K_FILE, K_HARDLINK, K_SYMLINK, MAGIC,
    S_BLOB, S_CDC, S_CHUNKS, S_PACK, S_SPARSE, S_VZIP, VERSION, sha, zd,
)


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


def _read_exact(f, n: int, label: str) -> bytes:
    data = f.read(n)
    if len(data) != n:
        raise ValidationError(f"truncated {label}")
    return data


def _int(value, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValidationError(f"{label} must be an integer >= {minimum}")
    return value


def _ref(value, count: int, label: str) -> int:
    value = _int(value, label)
    if value >= count:
        raise ValidationError(f"{label} references missing object {value}")
    return value


def _unpack(payload: bytes, limits: ParserLimits, label: str):
    # Footnote: MessagePack has its own declared collection lengths. Bound them as part of the same
    # hostile-input boundary rather than validating only after millions of Python objects exist.
    cap = max(limits.max_files, limits.max_blobs, limits.max_recipes)
    try:
        return msgpack.unpackb(
            payload,
            raw=False,
            strict_map_key=False,
            max_str_len=max(limits.max_path_bytes, 1024 * 1024),
            max_bin_len=limits.max_index_bytes,
            max_array_len=cap,
            max_map_len=cap,
            max_ext_len=0,
        )
    except Exception as exc:
        raise ValidationError(f"invalid {label} MessagePack: {exc}") from exc


def _footer_candidates(f, archive_size: int):
    """Yield footer offsets newest-first with bounded scanning memory."""
    magic = FMAGIC
    block = 1024 * 1024
    pos = archive_size
    carry = b""
    while pos:
        n = min(block, pos)
        pos -= n
        f.seek(pos)
        chunk = f.read(n) + carry
        end = len(chunk)
        while True:
            i = chunk.rfind(magic, 0, end)
            if i < 0:
                break
            absolute = pos + i
            if absolute + FTR.size <= archive_size:
                yield absolute
            end = i
        carry = chunk[: len(magic) - 1]


def _decode_footer(f, archive_size: int, pos: int, limits: ParserLimits):
    if pos < 0 or pos + FTR.size > archive_size:
        return None
    f.seek(pos)
    raw = f.read(FTR.size)
    if len(raw) != FTR.size:
        return None
    magic, kind, codec, flags, reserved, csize, usize, prev, digest = FTR.unpack(raw)
    if magic != FMAGIC:
        return None

    # Cheap discriminator checks happen before size interpretation so random footer-magic bytes inside
    # compressed payloads do not become convincing fake generations.
    if kind not in (0, 1) or codec not in (0, 1) or flags or reserved:
        return None
    if csize > pos or (prev and (prev >= pos or prev + FTR.size > archive_size)):
        return None
    if csize > limits.max_generation_bytes or usize > limits.max_generation_bytes:
        raise ResourceLimitError(
            f"generation payload exceeds limit: compressed={csize}, uncompressed={usize}"
        )

    f.seek(pos - csize)
    encoded = _read_exact(f, csize, "generation payload")
    try:
        payload = encoded if codec == 0 else zd(encoded, usize)
    except Exception:
        return None
    if len(payload) != usize or sha(payload) != digest:
        return None
    return kind, payload, prev


def _apply_delta(index: dict, delta: dict, limits: ParserLimits) -> None:
    if not isinstance(delta, dict):
        raise ValidationError("transaction delta is not a map")
    new_blobs = delta.get("blobs", [])
    ops = delta.get("ops", [])
    files = index.get("files")
    blobs = index.get("blobs")
    if not isinstance(new_blobs, list) or not isinstance(ops, list):
        raise ValidationError("transaction delta blobs/ops must be arrays")
    if not isinstance(files, list) or not isinstance(blobs, list):
        raise ValidationError("checkpoint lacks files/blobs arrays")
    if len(blobs) + len(new_blobs) > limits.max_blobs:
        raise ResourceLimitError("blob count exceeds parser limit")
    blobs.extend(new_blobs)

    for op in ops:
        if not isinstance(op, list) or not op:
            raise ValidationError("malformed transaction operation")
        tag = op[0]
        if tag == "put" and len(op) == 2:
            row = op[1]
            if not isinstance(row, list) or not row or not isinstance(row[0], str):
                raise ValidationError("malformed put operation")
            for i, current in enumerate(files):
                if isinstance(current, list) and current and current[0] == row[0]:
                    files[i] = row
                    break
            else:
                files.append(row)
                if len(files) > limits.max_files:
                    raise ResourceLimitError("file count exceeds parser limit")
        elif tag == "del" and len(op) == 2 and isinstance(op[1], str):
            files[:] = [row for row in files if not (isinstance(row, list) and row and row[0] == op[1])]
        elif tag == "ren" and len(op) == 3 and all(isinstance(x, str) for x in op[1:]):
            for row in files:
                if isinstance(row, list) and row and row[0] == op[1]:
                    row[0] = op[2]
                    break
        else:
            raise ValidationError(f"unsupported transaction operation {tag!r}")


def _index_from_footer(f, archive_size: int, start: int, limits: ParserLimits):
    deltas = []
    seen = set()
    pos = start
    depth = 0
    while pos:
        if pos in seen:
            raise ValidationError("transaction footer cycle")
        if depth > limits.max_delta_depth:
            raise ResourceLimitError("transaction chain exceeds parser limit")
        seen.add(pos)
        generation = _decode_footer(f, archive_size, pos, limits)
        if generation is None:
            return None
        kind, payload, prev = generation
        decoded = _unpack(payload, limits, "generation")
        if kind == 0:
            if not isinstance(decoded, dict):
                raise ValidationError("checkpoint generation is not an index map")
            index = decoded
            for delta in reversed(deltas):
                _apply_delta(index, delta, limits)
            return index, depth
        if not isinstance(decoded, dict):
            raise ValidationError("delta generation is not a map")
        deltas.append(decoded)
        depth += 1
        pos = prev
    return None


def _load_effective_index(f, archive_size: int, limits: ParserLimits):
    if archive_size < HDR.size:
        raise ValidationError("archive is smaller than the revision-24 header")

    f.seek(0)
    header = _read_exact(f, HDR.size, "header")
    magic, version, flags, csize, usize, data_span, index_hash = HDR.unpack(header)
    if magic != MAGIC or version != VERSION:
        raise ValidationError("not CMPCT revision 24")
    if flags:
        raise ValidationError("unsupported header flags")
    if csize > limits.max_index_bytes or usize > limits.max_index_bytes:
        raise ResourceLimitError(
            f"primary index exceeds limit: compressed={csize}, uncompressed={usize}"
        )
    record_base = HDR.size + csize
    if record_base > archive_size or data_span > archive_size - record_base:
        raise ValidationError("header index/data span extends beyond archive")

    # Mirror reader recovery semantics: newest valid committed footer wins; an incomplete/corrupt tail
    # may be ignored in favor of the previous committed generation.
    for footer_pos in _footer_candidates(f, archive_size):
        recovered = _index_from_footer(f, archive_size, footer_pos, limits)
        if recovered is not None:
            index, depth = recovered
            return index, record_base, footer_pos, depth

    f.seek(HDR.size)
    encoded = _read_exact(f, csize, "primary index")
    try:
        payload = zd(encoded, usize)
    except Exception as exc:
        raise ValidationError(f"primary index decode failed: {exc}") from exc
    if len(payload) != usize or sha(payload) != index_hash:
        raise ValidationError("primary index integrity failure")
    index = _unpack(payload, limits, "primary index")
    if not isinstance(index, dict):
        raise ValidationError("primary index is not a map")
    return index, record_base, 0, 0


def _validate_recipe(recipe, blob_count: int, limits: ParserLimits, rid: int) -> None:
    if not isinstance(recipe, list) or len(recipe) != 6:
        raise ValidationError(f"recipe {rid} has invalid shape")
    skeleton, literals, payloads, digest, total, crc = recipe
    _ref(skeleton, blob_count, f"recipe {rid} skeleton")
    if not isinstance(literals, list) or not isinstance(payloads, list):
        raise ValidationError(f"recipe {rid} literals/payloads must be arrays")
    if len(literals) != len(payloads) + 1:
        raise ValidationError(f"recipe {rid} literal count mismatch")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in literals):
        raise ValidationError(f"recipe {rid} has invalid literal length")
    _int(total, f"recipe {rid} total size")
    _int(crc, f"recipe {rid} CRC32")
    if not isinstance(digest, (bytes, bytearray)) or len(digest) != 32:
        raise ValidationError(f"recipe {rid} SHA-256 must be 32 bytes")
    for pi, payload in enumerate(payloads):
        if not isinstance(payload, list) or len(payload) != 6:
            raise ValidationError(f"recipe {rid} payload {pi} has invalid shape")
        raw_ref, method, stream_mode, stream_ref, csize, level = payload
        _ref(raw_ref, blob_count, f"recipe {rid} payload {pi} raw blob")
        if method not in (0, 8):
            raise ValidationError(f"recipe {rid} payload {pi} uses unsupported ZIP method")
        if stream_mode not in (0, 1, 2):
            raise ValidationError(f"recipe {rid} payload {pi} uses unknown stream mode")
        _ref(stream_ref, blob_count, f"recipe {rid} payload {pi} stream blob")
        _int(csize, f"recipe {rid} payload {pi} compressed size")
        if not isinstance(level, int) or isinstance(level, bool) or level < -1 or level > 9:
            raise ValidationError(f"recipe {rid} payload {pi} has invalid Deflate level")


def _validate_storage(path: str, kind: int, size: int, storage, blobs, recipes) -> None:
    blob_count = len(blobs)
    if kind == K_DIR:
        if storage is not None:
            raise ValidationError(f"directory {path!r} unexpectedly has storage")
        return
    if kind == K_HARDLINK:
        if not isinstance(storage, list) or len(storage) != 1 or not isinstance(storage[0], str):
            raise ValidationError(f"hardlink {path!r} has invalid target")
        return
    if kind == K_SYMLINK:
        if not isinstance(storage, list) or len(storage) != 2 or storage[0] != S_BLOB:
            raise ValidationError(f"symlink {path!r} must use direct blob storage")
        _ref(storage[1], blob_count, f"symlink {path!r}")
        return
    if kind != K_FILE or not isinstance(storage, list) or not storage:
        raise ValidationError(f"file {path!r} has invalid storage")

    tag = storage[0]
    if tag == S_BLOB:
        if len(storage) != 2:
            raise ValidationError(f"file {path!r} has malformed blob storage")
        _ref(storage[1], blob_count, f"file {path!r}")
    elif tag == S_PACK:
        if len(storage) != 4:
            raise ValidationError(f"file {path!r} has malformed pack storage")
        idx = _ref(storage[1], blob_count, f"file {path!r} pack")
        off = _int(storage[2], f"file {path!r} pack offset")
        length = _int(storage[3], f"file {path!r} pack length")
        if length != size or off + length > blobs[idx][1]:
            raise ValidationError(f"file {path!r} pack slice exceeds blob")
    elif tag == S_CHUNKS:
        if len(storage) != 2 or not isinstance(storage[1], list):
            raise ValidationError(f"file {path!r} has malformed chunk storage")
        total = 0
        for ci, idx in enumerate(storage[1]):
            idx = _ref(idx, blob_count, f"file {path!r} chunk {ci}")
            total += blobs[idx][1]
        if total != size:
            raise ValidationError(f"file {path!r} chunk lengths do not equal logical size")
    elif tag == S_CDC:
        if len(storage) != 2 or not isinstance(storage[1], list):
            raise ValidationError(f"file {path!r} has malformed CDC storage")
        total = 0
        for ci, item in enumerate(storage[1]):
            if not isinstance(item, list) or len(item) != 2:
                raise ValidationError(f"file {path!r} CDC chunk {ci} has invalid shape")
            length = _int(item[0], f"file {path!r} CDC chunk {ci} length", minimum=1)
            idx = _ref(item[1], blob_count, f"file {path!r} CDC chunk {ci}")
            if length != blobs[idx][1]:
                raise ValidationError(f"file {path!r} CDC chunk {ci} length disagrees with blob")
            total += length
        if total != size:
            raise ValidationError(f"file {path!r} CDC lengths do not equal logical size")
    elif tag == S_SPARSE:
        if len(storage) != 2 or not isinstance(storage[1], list):
            raise ValidationError(f"file {path!r} has malformed sparse storage")
        previous_end = 0
        for ei, extent in enumerate(storage[1]):
            if not isinstance(extent, list) or len(extent) != 3 or not isinstance(extent[2], list):
                raise ValidationError(f"file {path!r} sparse extent {ei} has invalid shape")
            off = _int(extent[0], f"file {path!r} extent {ei} offset")
            length = _int(extent[1], f"file {path!r} extent {ei} length", minimum=1)
            if off < previous_end or off + length > size:
                raise ValidationError(f"file {path!r} sparse extent {ei} overlaps or exceeds file")
            stored = 0
            for ci, idx in enumerate(extent[2]):
                idx = _ref(idx, blob_count, f"file {path!r} extent {ei} chunk {ci}")
                stored += blobs[idx][1]
            if stored != length:
                raise ValidationError(f"file {path!r} sparse extent {ei} length mismatch")
            previous_end = off + length
    elif tag == S_VZIP:
        if len(storage) != 2:
            raise ValidationError(f"file {path!r} has malformed virtual-ZIP storage")
        rid = _ref(storage[1], len(recipes), f"file {path!r} virtual-ZIP recipe")
        if recipes[rid][4] != size:
            raise ValidationError(f"file {path!r} virtual-ZIP size mismatch")
    else:
        raise ValidationError(f"file {path!r} uses unknown storage kind {tag!r}")


def _validate_index(index: dict, record_base: int, archive_size: int, limits: ParserLimits) -> None:
    if index.get("v") != VERSION:
        raise ValidationError(f"index revision is not {VERSION}")
    files = index.get("files")
    blobs = index.get("blobs")
    recipes = index.get("recipes")
    if not isinstance(files, list) or not isinstance(blobs, list) or not isinstance(recipes, list):
        raise ValidationError("index files/blobs/recipes must be arrays")
    if len(files) > limits.max_files:
        raise ResourceLimitError("file count exceeds parser limit")
    if len(blobs) > limits.max_blobs:
        raise ResourceLimitError("blob count exceeds parser limit")
    if len(recipes) > limits.max_recipes:
        raise ResourceLimitError("recipe count exceeds parser limit")

    for i, blob in enumerate(blobs):
        if not isinstance(blob, list) or len(blob) != 5:
            raise ValidationError(f"blob {i} index row has invalid shape")
        off, usize, csize, codec, meta_len = blob
        off = _int(off, f"blob {i} offset")
        usize = _int(usize, f"blob {i} uncompressed size")
        csize = _int(csize, f"blob {i} compressed size")
        meta_len = _int(meta_len, f"blob {i} metadata size")
        if codec not in (CODEC_RAW, CODEC_ZSTD, CODEC_WAVFLAC, CODEC_ZSTDDICT, CODEC_DEFLATE):
            raise ValidationError(f"blob {i} uses unknown codec {codec!r}")
        if max(usize, csize) > limits.max_blob_bytes:
            raise ResourceLimitError(f"blob {i} size exceeds parser limit")
        if meta_len > limits.max_index_bytes:
            raise ResourceLimitError(f"blob {i} metadata exceeds parser limit")
        if record_base + off + BHDR.size + meta_len + csize > archive_size:
            raise ValidationError(f"blob {i} extends beyond archive")

    for rid, recipe in enumerate(recipes):
        _validate_recipe(recipe, len(blobs), limits, rid)

    dict_idx = index.get("dict_blob")
    if dict_idx is not None:
        _ref(dict_idx, len(blobs), "dictionary blob")

    seen_paths = set()
    hardlinks = {}
    for fi, row in enumerate(files):
        if not isinstance(row, list) or len(row) != 7:
            raise ValidationError(f"file row {fi} has invalid shape")
        path, kind, mode, mtime, size, whole_hash, storage = row
        if not isinstance(path, str):
            raise ValidationError(f"file row {fi} path is not text")
        path_bytes = path.encode("utf-8", "surrogatepass")
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        if (
            not path
            or len(path_bytes) > limits.max_path_bytes
            or normalized.startswith("/")
            or any(part in ("", "..") for part in parts)
        ):
            raise ValidationError(f"unsafe logical path {path!r}")
        if path in seen_paths:
            raise ValidationError(f"duplicate logical path {path!r}")
        seen_paths.add(path)
        if kind not in (K_FILE, K_DIR, K_SYMLINK, K_HARDLINK):
            raise ValidationError(f"file {path!r} has unknown kind {kind!r}")
        _int(mode, f"file {path!r} mode")
        if not isinstance(mtime, int) or isinstance(mtime, bool):
            raise ValidationError(f"file {path!r} mtime must be an integer")
        size = _int(size, f"file {path!r} size")
        if whole_hash is not None and (
            not isinstance(whole_hash, (bytes, bytearray)) or len(whole_hash) != 32
        ):
            raise ValidationError(f"file {path!r} logical hash must be 32 bytes")
        _validate_storage(path, kind, size, storage, blobs, recipes)
        if kind == K_HARDLINK:
            hardlinks[path] = storage[0]

    for path, target in hardlinks.items():
        if target not in seen_paths:
            raise ValidationError(f"hardlink {path!r} targets missing path {target!r}")
        walked = {path}
        current = target
        while current in hardlinks:
            if current in walked:
                raise ValidationError(f"hardlink cycle involving {path!r}")
            walked.add(current)
            current = hardlinks[current]

    fsmeta = index.get("fsmeta", {})
    if not isinstance(fsmeta, dict):
        raise ValidationError("fsmeta must be a map")
    owner = fsmeta.get("owner", [0, 0])
    if not isinstance(owner, list) or len(owner) != 2:
        raise ValidationError("fsmeta owner must be [uid, gid]")
    for value in owner:
        _int(value, "fsmeta owner")
    for label in ("owner_overrides", "xattrs"):
        rows = fsmeta.get(label, [])
        if not isinstance(rows, list):
            raise ValidationError(f"fsmeta {label} must be an array")
        for row in rows:
            if not isinstance(row, list) or not row:
                raise ValidationError(f"fsmeta {label} row is malformed")
            _ref(row[0], len(files), f"fsmeta {label} file")


def _validate_blob_headers(f, index: dict, record_base: int, archive_size: int, limits: ParserLimits) -> None:
    """Cross-check physical records without decompressing payloads."""
    for i, blob in enumerate(index["blobs"]):
        off, usize, csize, codec, meta_len = blob
        pos = record_base + off
        f.seek(pos)
        raw = _read_exact(f, BHDR.size, f"blob {i} header")
        magic, pcodec, flags, reserved, pusize, pcsize, pmeta, crc32, digest = BHDR.unpack(raw)
        if magic != BMAGIC:
            raise ValidationError(f"blob {i} magic mismatch")
        if flags or reserved:
            raise ValidationError(f"blob {i} uses unsupported flags")
        if (pcodec, pusize, pcsize, pmeta) != (codec, usize, csize, meta_len):
            raise ValidationError(f"blob {i} physical header disagrees with index")
        if max(pusize, pcsize) > limits.max_blob_bytes or pmeta > limits.max_index_bytes:
            raise ResourceLimitError(f"blob {i} physical declaration exceeds parser limit")
        if pos + BHDR.size + pmeta + pcsize > archive_size:
            raise ValidationError(f"blob {i} physical payload extends beyond archive")


def preflight_archive(
    path: str | os.PathLike[str],
    limits: ParserLimits | None = None,
    *,
    verify_blob_headers: bool = True,
) -> dict:
    """Boundedly validate revision-24 structure without materializing logical files."""
    limits = limits or ParserLimits.from_env()
    archive = Path(path)
    with archive.open("rb") as f:
        archive_size = os.fstat(f.fileno()).st_size
        index, record_base, footer_pos, depth = _load_effective_index(f, archive_size, limits)
        _validate_index(index, record_base, archive_size, limits)
        if verify_blob_headers:
            _validate_blob_headers(f, index, record_base, archive_size, limits)
    return {
        "version": index["v"],
        "files": len(index["files"]),
        "blobs": len(index["blobs"]),
        "recipes": len(index["recipes"]),
        "latest_footer": footer_pos,
        "delta_depth": depth,
        "archive_bytes": archive_size,
    }
