from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess

from cmpct.codec import zcd

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native" / "cmpct-core"
ROW = re.compile(r"^level=(\d+) usize=(\d+) csize=(\d+) sha256=([0-9a-f]{64})$")


def _payload() -> bytes:
    out = bytearray()
    phrase = b"cmpct exact raw dictionary ownership boundary\0"
    while len(out) < 155_648:
        i = len(out)
        out += phrase
        out += i.to_bytes(8, "little")
        out += phrase[: (i // 17) % len(phrase)]
    return bytes(out[:155_648])


def _dictionary() -> bytes:
    out = bytearray()
    seed = b"cmpct exact raw dictionary ownership boundary\0"
    while len(out) < 8192:
        out += seed
        out += len(out).to_bytes(4, "little")
    return bytes(out[:8192])


def test_package_owned_low_level_zstd_matches_canonical_dictionary_bytes() -> None:
    """Fail closed before #176 can swap ownership of canonical Zstd operations.

    The Rust arm reaches zstd-safe's low-level one-shot dictionary call through the already-pinned
    native-core graph. The Python arm is the current shipping ctypes/system-libzstd call. Equality is
    required on compressed bytes themselves; successful cross-decode is deliberately insufficient.
    """

    output = subprocess.check_output(
        ["cargo", "run", "--locked", "--quiet", "--bin", "zstd_abi_parity"],
        cwd=NATIVE,
        text=True,
    )
    rust: dict[int, tuple[int, str]] = {}
    for line in output.splitlines():
        match = ROW.fullmatch(line.strip())
        assert match, line
        level, usize, csize, digest = match.groups()
        assert int(usize) == 155_648
        rust[int(level)] = (int(csize), digest)

    src = _payload()
    dictionary = _dictionary()
    assert set(rust) == {1, 3, 9, 19}
    for level in sorted(rust):
        canonical = zcd(src, dictionary, level)
        assert rust[level] == (len(canonical), hashlib.sha256(canonical).hexdigest())
