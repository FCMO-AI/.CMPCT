from __future__ import annotations

import os
from pathlib import Path
import random

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _tree(root: Path) -> Path:
    src=root/'src';src.mkdir()
    rng=random.Random(0xC0DEC0DE)
    for i in range(48):
        (src/f'module-{i:03d}.txt').write_text(
            f'module={i}\n'+('shared configuration payload\n'*120)+(f'unique={i*i}\n'*9),encoding='utf-8'
        )
    for i in range(8):
        (src/f'blob-{i:02d}.bin').write_bytes(bytes(rng.getrandbits(8) for _ in range(28_000+i*257)))
    return src


def test_parallel_encode_is_byte_identical_to_one_worker(tmp_path: Path):
    src=_tree(tmp_path)
    one=tmp_path/'one.cmpct';many=tmp_path/'many.cmpct'
    Builder(src,workers=1,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000).build(one)
    Builder(src,workers=4,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000).build(many)
    # Footnote: this is stronger than semantic round-trip parity. A scheduler may reorder completion,
    # but candidate materialization is hash-sorted, so the complete archive bytes must remain identical.
    assert one.read_bytes()==many.read_bytes()
    with CMPCT(many) as ar:
        assert ar.verify()==56


def test_reproducible_mode_ignores_mtime_and_source_date_epoch_is_stable(tmp_path: Path,monkeypatch):
    src=_tree(tmp_path)
    first=tmp_path/'first.cmpct';second=tmp_path/'second.cmpct'
    monkeypatch.setenv('SOURCE_DATE_EPOCH','1712345678')
    Builder(src,workers=2,reproducible=True).build(first)
    # Change filesystem timestamps without changing logical bytes. Default fidelity mode is allowed to
    # reflect this; reproducible mode must not.
    for i,path in enumerate(sorted(p for p in src.rglob('*') if p.is_file())):
        ns=1_900_000_000_000_000_000+i*1_000_000
        os.utime(path,ns=(ns,ns),follow_symlinks=False)
    Builder(src,workers=3,reproducible=True).build(second)
    assert first.read_bytes()==second.read_bytes()


def test_default_mode_still_preserves_source_metadata_semantics(tmp_path: Path):
    src=_tree(tmp_path)
    fidelity=tmp_path/'fidelity.cmpct'
    stats=Builder(src,workers=1,reproducible=False).build(fidelity)
    assert stats['reproducible'] is False
    with CMPCT(fidelity) as ar:
        row=ar.by['module-000.txt']
        assert row[3]==(src/'module-000.txt').stat().st_mtime_ns
