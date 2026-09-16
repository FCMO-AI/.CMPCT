from __future__ import annotations

from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from experiments import entropygraph_v025 as V25


def test_direct_memory_capture_intercepts_only_target_and_restores_historical_open(tmp_path):
    target = tmp_path / "captured.c25eg07"
    ordinary = tmp_path / "ordinary.bin"
    capture = V4._Capture()
    had_open = "open" in V25.__dict__
    previous = V25.__dict__.get("open")
    try:
        with V4._module_open_capture(target, capture):
            with V25.open(target, "wb") as stream:
                stream.write(b"authenticated-envelope")
            with V25.open(ordinary, "wb") as stream:
                stream.write(b"ordinary-io")

        assert capture.getvalue() == b"authenticated-envelope"
        assert not target.exists(), "captured final archive must not hit disk"
        assert ordinary.read_bytes() == b"ordinary-io", "unrelated I/O must remain ordinary filesystem I/O"
        if had_open:
            assert V25.__dict__.get("open") is previous
        else:
            assert "open" not in V25.__dict__
    finally:
        capture.really_close()


def test_capture_close_is_non_destructive_until_explicit_release():
    capture = V4._Capture()
    try:
        capture.write(b"proof")
        capture.close()
        assert capture.getvalue() == b"proof"
        assert not capture.closed
    finally:
        capture.really_close()
    assert capture.closed
