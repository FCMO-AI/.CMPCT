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
    # Exact structured payload that exposed the 104 B vs 105 B mismatch in #177.
    return (b"structured-record\0" * 8192) + bytes(range(64)) * 128


def _dictionary() -> bytes:
    return (b"alpha beta gamma delta structured-record\0" * 128)[:4096]


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
    assert len(src) == 155_648
    assert len(dictionary) == 4096
    assert set(rust) == {1, 3, 9, 19}
    for level in sorted(rust):
        canonical = zcd(src, dictionary, level)
        assert rust[level] == (len(canonical), hashlib.sha256(canonical).hexdigest())
