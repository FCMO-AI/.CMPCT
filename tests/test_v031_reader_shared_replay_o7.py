"""O7: installed Reader on genuine authenticated r24 journal, not a simulated index.

These are correctness courts only. Source-exact historical-vs-candidate A/B is
in benchmarks/v031_reader_shared_replay_o7.py.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import ValidationError, preflight_archive

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
from v031_signed_delta_replay_o0 import PAYLOAD, make_case  # noqa: E402


def _source(tmp_path: Path) -> Path:
    data = tmp_path / "input"
    data.mkdir()
    (data / "single.bin").write_bytes(PAYLOAD)
    source = tmp_path / "builder.cmpct"
    Builder(data, workers=1, reproducible=True).build(source)
    return source


@pytest.mark.parametrize("n", [64, 512, 2048])
def test_signed_r24_reader_replays_exact_index_and_payload_from_checkpoint(
    tmp_path: Path, n: int,
) -> None:
    delta, checkpoint, fingerprint = make_case(tmp_path, _source(tmp_path), n)
    assert fingerprint["result_index_equal"] is True
    assert preflight_archive(delta)["delta_depth"] == 1
    with CMPCT(delta) as journal, CMPCT(checkpoint) as direct:
        assert journal.index == direct.index
        assert journal.files == direct.files
        assert journal.delta_depth == 1 and direct.delta_depth == 0
        for number in (0, n // 2, n - 1):
            name = f"g{number:06d}.bin"
            assert journal.read(name) == direct.read(name) == PAYLOAD


def test_signed_multi_generation_collision_and_deletion_replay(tmp_path: Path) -> None:
    delta, _, _ = make_case(tmp_path, _source(tmp_path), 72)
    with CMPCT(delta) as initial:
        first_footer = initial.latest_footer_pos
        appended = copy.deepcopy(initial.by["g000010.bin"])
        appended[0] = "added.bin"
    ops = [
        ["ren", "g000000.bin", "r000000.bin"],
        ["del", "g000001.bin"],
        ["put", appended],
        # Duplicate names exist transiently, but final tree has no collision.
        ["ren", "g000004.bin", "g000005.bin"],
        ["del", "g000005.bin"],
    ]
    new_footer, _ = _append_generation(delta, {"blobs": [], "ops": ops}, first_footer)
    with CMPCT(delta) as intermediate:
        assert intermediate.latest_footer_pos == new_footer
        assert intermediate.delta_depth == 2
        assert intermediate.read("added.bin") == intermediate.read("r000000.bin") == PAYLOAD
        assert "g000004.bin" not in intermediate.by
        assert "g000005.bin" not in intermediate.by
        assert len(intermediate.files) == 70  # -1 deleted, +1 put, -2 dup deleted
    assert preflight_archive(delta)["files"] == 70
    newer, _ = _append_generation(
        delta, {"blobs": [], "ops": [["ren", "r000000.bin", "final.bin"]]},
        new_footer,
    )
    assert newer > new_footer
    with CMPCT(delta) as final:
        assert final.delta_depth == 3
        assert "r000000.bin" not in final.by
        assert final.read("final.bin") == PAYLOAD


def test_signed_unsupported_delta_is_refused_by_reader_and_preflight(tmp_path: Path) -> None:
    delta, _, _ = make_case(tmp_path, _source(tmp_path), 72)
    with CMPCT(delta) as original:
        prev = original.latest_footer_pos
    _append_generation(
        delta, {"blobs": [], "ops": [["unexpected-op", "g000000.bin"]]}, prev,
    )
    # Historical Reader ignored unknown tags. Strict shared replay now refuses
    # authenticated malformed transactions, consistent with preflight.
    with pytest.raises(ValidationError, match="unsupported transaction operation"):
        preflight_archive(delta)
    with pytest.raises(ValidationError, match="unsupported transaction operation"):
        CMPCT(delta)


def test_incomplete_unsigned_tail_retains_latest_valid_generation(tmp_path: Path) -> None:
    delta, _, _ = make_case(tmp_path, _source(tmp_path), 72)
    with CMPCT(delta) as before:
        expected = copy.deepcopy(before.index)
        footer = before.latest_footer_pos
    with delta.open("ab") as f:
        f.write(b"interrupted-unsigned-tail-CMPTF24\\x00")
    with CMPCT(delta) as recovered:
        assert recovered.index == expected
        assert recovered.latest_footer_pos == footer
        assert recovered.read("g000000.bin") == PAYLOAD
