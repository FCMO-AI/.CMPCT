from __future__ import annotations

import os
from pathlib import Path
import stat

from experiments import entropygraph_v030_r24_media_terminal as media


def _collect_like_media(root: Path) -> list[tuple[Path, int]]:
    rows: list[tuple[Path, int]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                rows.append((path, int(st.st_size)))
    return rows


def test_precollected_media_analysis_is_exact_for_ineligible_shape(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"\xff\xd8\xff" + b"a" * 4093)
    (tmp_path / "b.bin").write_bytes(b"plain" * 400)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.bin").write_bytes(b"\x89PNG\r\n\x1a\n" + b"b" * 1024)

    assert media.analyze_precollected(_collect_like_media(tmp_path)) == media.analyze(tmp_path)


def test_precollected_media_analysis_is_exact_for_eligible_shape(tmp_path: Path) -> None:
    # Eight >=1 MiB opaque-media-shaped files satisfy the structural floor. The deterministic 0..255 cycle keeps
    # sampled entropy at 8 bits/byte without relying on host randomness or benchmark identity.
    payload = bytes(range(256)) * 4096
    for idx in range(media.MIN_REGULAR_FILES):
        head = b"\xff\xd8\xff" + bytes([idx])
        (tmp_path / f"member-{idx:02d}.bin").write_bytes(head + payload)

    direct = media.analyze(tmp_path)
    reused = media.analyze_precollected(_collect_like_media(tmp_path))
    assert reused == direct
    assert direct["eligible"] is True
    assert direct["sample_entropy_bits_per_byte"] >= media.MIN_ENTROPY_BITS_PER_BYTE
