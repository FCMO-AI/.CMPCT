from pathlib import Path
import ctypes
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_PACK


def main(lib_path: str) -> None:
    lib = ctypes.CDLL(lib_path)
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "src"
        root.mkdir()
        expected = {}
        for i in range(80):
            data = (f"tiny-{i:03d}:" + "alpha beta gamma delta " * 12).encode()
            path = root / f"item-{i:03d}.txt"
            path.write_bytes(data)
            expected[path.name] = data

        archive = Path(td) / "pack.cmpct"
        Builder(root).build(archive)
        with CMPCT(archive) as py:
            assert any(
                row[1] == 0 and row[6][0] == S_PACK for row in py.files
            ), "fixture did not exercise S_PACK"

        handle = ctypes.c_void_p()
        assert lib.cmpct_open(str(archive).encode(), ctypes.byref(handle)) == 0
        try:
            count = lib.cmpct_entry_count(handle)
            seen = 0
            for index in range(count):
                length = ctypes.c_size_t()
                assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(length)) == 0
                buf = ctypes.create_string_buffer(length.value + 1)
                assert (
                    lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(length))
                    == 0
                )
                name = buf.value.decode()
                if name not in expected:
                    continue

                target = expected[name]
                out = (ctypes.c_uint8 * len(target))()
                got = ctypes.c_size_t()
                assert (
                    lib.cmpct_entry_read_range(
                        handle, index, 0, out, len(target), ctypes.byref(got)
                    )
                    == 0
                )
                assert bytes(out[: got.value]) == target

                # Footnote: a complete read proves member identity, but platform document providers
                # mostly issue small seeked reads. Exercise a non-zero logical offset too so S_PACK
                # cannot accidentally work only when the packed member starts at its own byte zero.
                slice_offset = 17
                slice_length = 41
                slice_out = (ctypes.c_uint8 * slice_length)()
                slice_got = ctypes.c_size_t()
                assert (
                    lib.cmpct_entry_read_range(
                        handle,
                        index,
                        slice_offset,
                        slice_out,
                        slice_length,
                        ctypes.byref(slice_got),
                    )
                    == 0
                )
                assert slice_got.value == slice_length
                assert bytes(slice_out) == target[
                    slice_offset : slice_offset + slice_length
                ]
                seen += 1
            assert seen == len(expected)
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
