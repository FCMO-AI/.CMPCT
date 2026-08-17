"""Runtime/archive fingerprints for byte-exact CMPCT research evidence.

Compression research cannot call two artifacts "the same experiment" merely because their source tree hash
matches.  Serializer and codec versions can change authenticated metadata bytes, and CMPCT's evidence gates
care about complete stored bytes.  This helper records the environment plus the primary Geometry metadata
raw/compressed identities so a future one-byte movement is attributable instead of mysterious.

Footnote: this module does not participate in encoding or selection and therefore cannot improve a benchmark.
It is deliberately observational.  Promotion evidence should record these fields beside size/timing results.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

from experiments import entropygraph_v030_geometry as geometry


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _libzstd_version() -> dict[str, str | None]:
    library = ctypes.util.find_library("zstd")
    if not library:
        return {"library": None, "version": None}
    handle = ctypes.CDLL(library)
    handle.ZSTD_versionString.argtypes = []
    handle.ZSTD_versionString.restype = ctypes.c_char_p
    raw = handle.ZSTD_versionString()
    return {"library": library, "version": raw.decode("ascii") if raw else None}


def runtime_fingerprint() -> dict:
    """Return versions that can influence generator/serializer/compressor evidence bytes."""
    zstd = _libzstd_version()
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "msgpack_python": _distribution_version("msgpack"),
        "zstandard_python": _distribution_version("zstandard"),
        "libzstd_library": zstd["library"],
        "libzstd_version": zstd["version"],
        "byteorder": sys.byteorder,
    }


def geometry_archive_fingerprint(path: Path) -> dict:
    """Fingerprint complete CMPNX13 accounting without invoking the decoder selection path."""
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(geometry.HDR.size)
        if len(header) != geometry.HDR.size:
            raise RuntimeError("short Geometry archive while fingerprinting")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = geometry.HDR.unpack(header)
        if magic != geometry.MAG:
            raise RuntimeError("evidence fingerprint requires a CMPNX13 Geometry artifact")
        if mcs > geometry.MAX_DECODE_UNIT or mus > geometry.MAX_DECODE_UNIT:
            raise RuntimeError("Geometry metadata declaration exceeds evidence policy")
        meta_comp = stream.read(mcs)
        if len(meta_comp) != mcs:
            raise RuntimeError("short Geometry primary metadata while fingerprinting")
    meta_raw = geometry.zd(meta_comp, mus)
    if len(meta_raw) != mus or geometry.H(meta_raw) != meta_sha:
        raise RuntimeError("Geometry metadata authentication failed while fingerprinting")

    # CMPNX13 writes the same compressed metadata twice and exactly one fixed physical header per record.
    # Solving the complete-size equation makes payload bytes explicit in evidence instead of leaving archive
    # overhead implicit: size = HDR + 2*meta_comp + count*PH + payloads + FTR.
    payload_bytes = size - geometry.HDR.size - geometry.FTR.size - 2 * mcs - count * geometry.PH.size
    if payload_bytes < 0:
        raise RuntimeError("Geometry complete-artifact accounting underflow")

    return {
        "archive_bytes": size,
        "record_count": int(count),
        "physical_header_bytes": int(count) * geometry.PH.size,
        "physical_payload_bytes": int(payload_bytes),
        "metadata_raw_bytes": int(mus),
        "metadata_compressed_bytes_each": int(mcs),
        "metadata_compressed_bytes_total": int(2 * mcs),
        "metadata_raw_sha256": hashlib.sha256(meta_raw).hexdigest(),
        "metadata_compressed_sha256": hashlib.sha256(meta_comp).hexdigest(),
        "merkle_root_sha256": bytes(merkle).hex(),
        "declared_max_decode_unit": int(max_decode),
        "declared_max_decoder_memory": int(max_memory),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fingerprint CMPCT Geometry research evidence")
    parser.add_argument("archive", type=Path, nargs="?")
    args = parser.parse_args()
    output = {"runtime": runtime_fingerprint()}
    if args.archive is not None:
        output["geometry_archive"] = geometry_archive_fingerprint(args.archive)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
