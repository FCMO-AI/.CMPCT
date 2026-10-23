"""Regression: internal decoder futures must complete before Reader dependencies close.

Fixed, Builder-independent revision-24 archives provide exact source/logical identity.
The worker is intentionally stopped immediately before it calls the real CMPCT reader.
"""
from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import json
from pathlib import Path
import threading

import pytest

from cmpct.reader import CMPCT

GOLDEN = Path(__file__).resolve().parent / "conformance" / "v24-direct-codecs.json"


class TrackingExecutor:
    def __init__(self, pool):
        self.pool = pool
        self.entered_shutdown = threading.Event()

    def submit(self, *args, **kwargs):
        return self.pool.submit(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        self.entered_shutdown.set()
        return self.pool.shutdown(*args, **kwargs)


@pytest.mark.parametrize("codec", [0, 1, 3, 4], ids=["raw", "zstd", "zstd-dict", "deflate"])
def test_close_joins_decoder_worker_before_mmap_release(tmp_path: Path, codec: int):
    if codec == 3:
        v = json.loads((GOLDEN.parent / "v24-zstd-dictionary.json").read_text())["vector"]
    else:
        vectors = json.loads(GOLDEN.read_text())["vectors"]
        v = next(v for v in vectors if v["codec"] == codec)
    archive = tmp_path / "source.cmpct"
    archive.write_bytes(base64.b64decode(v["archive_base64"]))
    reader = CMPCT(archive)

    ready, release = threading.Event(), threading.Event()
    errors: list[BaseException] = []
    spy = TrackingExecutor(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    reader._executor = spy

    def worker():
        ready.set()
        if not release.wait(timeout=10):
            raise AssertionError("test worker was not released")
        # Exercise the real Reader's mmap and optional native codec path.
        return reader.read(v["name"])

    active = spy.submit(worker)
    assert ready.wait(timeout=10)
    queued = spy.submit(lambda: (_ for _ in ()).throw(AssertionError("queued task ran")))

    def close_reader():
        try:
            reader.close()
        except BaseException as exc:
            errors.append(exc)

    closing = threading.Thread(target=close_reader, daemon=True)
    closing.start()
    try:
        assert spy.entered_shutdown.wait(timeout=10), "shutdown not entered"
        assert reader.mm is not None, "mmap released while worker was still active"
    finally:
        release.set()

    closing.join(timeout=10)
    assert not closing.is_alive(), "shutdown deadlocked"
    assert not errors, errors
    assert hashlib.sha256(active.result(timeout=2)).hexdigest() == v["logical_sha256"]
    assert queued.cancelled(), "queued speculative work should be cancelled"
    assert reader.mm is None and reader.f.closed
    reader.close()  # idempotent
