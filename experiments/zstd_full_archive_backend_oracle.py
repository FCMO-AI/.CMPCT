from __future__ import annotations
"""Second-rung #176 oracle: full canonical archive identity under a Python-zstandard encoder backend."""
import hashlib
from pathlib import Path
import tempfile

import zstandard as zstd
from cmpct import builder as B
from cmpct.reader import Reader


def _py_zc(data: bytes, level: int) -> bytes:
    if not data:
        return b""
    return zstd.ZstdCompressor(level=level).compress(data)


def _py_zcd(data: bytes, dictionary: bytes, level: int) -> bytes:
    if not data:
        return b""
    d = zstd.ZstdCompressionDict(dictionary, dict_type=zstd.DICT_TYPE_RAWCONTENT)
    return zstd.ZstdCompressor(level=level, dict_data=d).compress(data)


def _tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        src = base / "src"
        src.mkdir()
        # Enough related text to exercise dictionary training plus incompressible/general binary data.
        for i in range(48):
            (src / f"doc-{i:02d}.txt").write_text(
                (f"record={i} alpha beta gamma delta shared-schema exact-lossless\n" * 512)
                + ("common footer and repeated semantic structure\n" * 256)
            )
        (src / "binary.bin").write_bytes(bytes(range(256)) * 1024)
        system = base / "system.cmpct"
        python_backend = base / "python.cmpct"

        B.Builder(src, reproducible=True).build(system)
        original_zc, original_zcd = B.zc, B.zcd
        try:
            B.zc, B.zcd = _py_zc, _py_zcd
            B.Builder(src, reproducible=True).build(python_backend)
        finally:
            B.zc, B.zcd = original_zc, original_zcd

        assert system.read_bytes() == python_backend.read_bytes(), "full archive bytes diverged across zstd backends"
        out = base / "out"
        Reader(python_backend).extract_all(out)
        assert _tree(src) == _tree(out), "Python-backend archive failed exact reconstruction"
        print({
            "schema": "cmpct-zstd-full-archive-backend-v1",
            "archive_bytes": system.stat().st_size,
            "archive_sha256": hashlib.sha256(system.read_bytes()).hexdigest(),
            "tree_files": len(_tree(src)),
            "byte_identical": True,
            "reconstruction_exact": True,
        })


if __name__ == "__main__":
    main()
