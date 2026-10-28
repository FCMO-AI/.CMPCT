"""J24K09 exact-source scoped diff custody, independent of the Reader itself.

Fail if candidate changes any unrelated codec/Reader byte or if historical parent
source differs. The guard never adjusts the tested product or source baseline.
"""
from __future__ import annotations

import pathlib
import subprocess

BASE = "78bc1f552fee24970228f89ac25dbf23307b0406"
BLOBS = {
    "src/cmpct/codec.py": "a5e5fd0cdaff9001d4d00e131c163c8768adc2b0",
    "src/cmpct/reader.py": "b37b786966ac1506a0439567d4a58eea472d85f8",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def source_at_base(path: str) -> str:
    assert git("rev-parse", f"{BASE}:{path}") == BLOBS[path]
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"]).decode("utf-8")


def restore_codec(candidate: str) -> str:
    oldsig = "def range_vzip(recipe,get_content,get_stream,start:int,length:int)->bytes:"
    newsig = "def range_vzip(recipe,get_content,get_stream,start:int,length:int,stream_size=None)->bytes:"
    assert candidate.count(newsig) == 1
    candidate = candidate.replace(newsig, oldsig)
    start = ("        elif outpos<end and (stream_size is not None or\\n"
             "                             (method==zipfile.ZIP_DEFLATED and stream_mode==2)):\\n"
             "            # A skipped physical stream determines every later logical offset.")
    end = "        outpos+=csize"
    i = candidate.index(start)
    j = candidate.index(end, i)
    old = """        elif method==zipfile.ZIP_DEFLATED and stream_mode==2 and outpos<end:
            # Regenerated Deflate has no stored csize oracle. To locate a later
            # literal correctly, verify every *preceding* mode2 stream exactly.
            # Preserve lazy reads that end before this stream and never retain
            # an unselected reconstructed stream in the result.
            if len(get_stream(stream_mode,streamref,level))!=csize:
                raise IOError('virtual ZIP selective reconstruction length mismatch')
"""
    return candidate[:i] + old + candidate[j:]


def restore_reader(candidate: str) -> str:
    start = "    def _vzip_physical_stream_size("
    end = "    def file_sha256("
    assert candidate.count(start) == 1
    i = candidate.index(start)
    j = candidate.index(end, i)
    candidate = candidate[:i] + candidate[j:]
    old = "if storage[0]==S_VZIP:return range_vzip(self.recipes[storage[1]],self._blob,self._stream,start,length)"
    new = "if storage[0]==S_VZIP:return range_vzip(self.recipes[storage[1]],self._blob,self._stream,start,length,self._vzip_physical_stream_size)"
    assert candidate.count(new) == 1
    return candidate.replace(new, old)


def main() -> None:
    transforms = {
        "src/cmpct/codec.py": restore_codec,
        "src/cmpct/reader.py": restore_reader,
    }
    for path, fn in transforms.items():
        original = source_at_base(path)
        candidate = pathlib.Path(path).read_text(encoding="utf-8")
        assert fn(candidate) == original, f"unapproved source difference: {path}"
        print(f"J24K09_EXACT_SOURCE_CUSTODY_PASS {path} baseline={BLOBS[path]}")


if __name__ == "__main__":
    main()
