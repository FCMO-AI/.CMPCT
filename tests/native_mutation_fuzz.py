from __future__ import annotations

"""Deterministic native parser/range mutation fuzz gate.

This is deliberately dependency-free so every CI/platform job can run it. It is not a substitute for
coverage-guided libFuzzer, but it gives the public C ABI a permanent hostile-input property: bounded
byte mutations and truncations of independent revision-24 archives may be accepted or rejected with a
typed status, but must never panic, crash, return an impossible entry count, or perform an out-of-range
successful read.
"""

import base64
import ctypes
import json
import random
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
FIXTURES = (
    ROOT / "tests/conformance/v24-direct-codecs.json",
    ROOT / "tests/conformance/v24-chunk-maps.json",
    ROOT / "tests/conformance/v24-sparse.json",
    ROOT / "tests/conformance/v24-zstd-dictionary.json",
    ROOT / "tests/conformance/v24-wavflac.json",
    ROOT / "tests/conformance/v24-pack.json",
    ROOT / "tests/conformance/v24-virtual-zip.json",
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode0.json",
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode1.json",
    ROOT / "tests/conformance/v24-virtual-zip-deflate-mode2.json",
    ROOT / "tests/conformance/v24-recovery.json",
)

OPEN_STATUSES = {0, -2, -3, -4, -7}
READ_STATUSES = {0, -2, -3, -4, -6, -7}
MAX_REASONABLE_ENTRIES = 4_000_000


class EntryInfo(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("mode", ctypes.c_uint32),
        ("size", ctypes.c_uint64),
        ("mtime_ns", ctypes.c_int64),
    ]


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_info.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(EntryInfo),
    ]
    lib.cmpct_entry_info.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    return lib


def _archives_from_fixture(path: Path) -> list[bytes]:
    doc = json.loads(path.read_text())
    vector = doc.get("vector", doc)
    out: list[bytes] = []

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("archive_base64") and isinstance(child, str):
                    out.append(base64.b64decode(child))
                elif key == "archive_base64" and isinstance(child, str):
                    out.append(base64.b64decode(child))
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(vector)
    # Some recovery fixture fields end in `_base64` rather than `archive_base64`.
    if path.name == "v24-recovery.json":
        for key, value in vector.items():
            if key.endswith("_base64") and isinstance(value, str):
                decoded = base64.b64decode(value)
                if decoded not in out:
                    out.append(decoded)
    if not out:
        raise AssertionError(f"no archive bytes found in {path}")
    return out


def _exercise(lib, root: Path, data: bytes, case: str) -> None:
    path = root / f"{case}.cmpct"
    path.write_bytes(data)
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(str(path).encode(), ctypes.byref(handle))
    assert status in OPEN_STATUSES, (case, status)
    if status != 0:
        assert not handle.value, (case, "failed open returned a live handle")
        return

    try:
        count = int(lib.cmpct_entry_count(handle))
        assert 0 <= count <= MAX_REASONABLE_ENTRIES, (case, count)
        for index in range(min(count, 8)):
            info = EntryInfo()
            status = lib.cmpct_entry_info(handle, index, ctypes.byref(info))
            assert status == 0, (case, index, status)
            if info.kind != 0 or info.size == 0:
                continue
            length = min(int(info.size), 32)
            out = ctypes.create_string_buffer(length)
            got = ctypes.c_size_t()
            status = lib.cmpct_entry_read_range(
                handle, index, 0, out, length, ctypes.byref(got)
            )
            assert status in READ_STATUSES, (case, index, status)
            if status == 0:
                assert got.value == length, (case, index, got.value, length)
            else:
                assert got.value == 0, (case, index, status, got.value)

            # Footnote: regardless of archive mutation, asking for two bytes starting at logical EOF-1
            # can never be a successful full-length range. This property catches arithmetic/bounds
            # regressions even when a mutated index remains structurally parseable.
            if info.size:
                got = ctypes.c_size_t()
                status = lib.cmpct_entry_read_range(
                    handle,
                    index,
                    info.size - 1,
                    out,
                    2,
                    ctypes.byref(got),
                )
                assert status == -6, (case, index, status)
                assert got.value == 0
    finally:
        lib.cmpct_close(handle)


def _mutations(data: bytes, seed: int):
    rng = random.Random(seed)
    if not data:
        return
    yield data

    # Boundary truncations attack all framing layers without allocating new random payloads.
    cuts = {0, 1, 7, 8, 12, 32, 67, 68, len(data) // 2, max(0, len(data) - 1)}
    for cut in sorted(c for c in cuts if 0 <= c < len(data)):
        yield data[:cut]

    # Deterministic bit/byte mutations retain file size so offset arithmetic and authenticated-index
    # disagreement paths receive much deeper exercise than pure truncation alone.
    for _ in range(48):
        mutated = bytearray(data)
        for _ in range(rng.randint(1, 4)):
            pos = rng.randrange(len(mutated))
            mutated[pos] ^= 1 << rng.randrange(8)
        yield bytes(mutated)

    for _ in range(16):
        mutated = bytearray(data)
        start = rng.randrange(len(mutated))
        span = min(rng.randint(1, 32), len(mutated) - start)
        mutated[start : start + span] = rng.randbytes(span)
        yield bytes(mutated)


def main() -> None:
    lib = _load_lib()
    corpus: list[tuple[str, bytes]] = []
    for fixture in FIXTURES:
        for index, archive in enumerate(_archives_from_fixture(fixture)):
            corpus.append((f"{fixture.stem}-{index}", archive))

    with tempfile.TemporaryDirectory(prefix="cmpct-native-mutation-") as td:
        root = Path(td)
        cases = 0
        for corpus_index, (name, archive) in enumerate(corpus):
            for mutation_index, mutated in enumerate(
                _mutations(archive, 0xC0_24_5EED + corpus_index)
            ):
                _exercise(lib, root, mutated, f"{name}-{mutation_index}")
                cases += 1
        assert cases >= 500, cases
        print(json.dumps({"schema": "cmpct-native-mutation-fuzz-v1", "cases": cases}))


if __name__ == "__main__":
    main()
