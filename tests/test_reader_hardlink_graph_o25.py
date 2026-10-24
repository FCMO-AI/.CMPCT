"""O25: authentic revision-24 Reader hardlink-graph safety and semantics court.

This is intentionally independent from the structural-validator-only mutation tests:
the SHA-committed checkpoint and physical RAW blob pass through real CMPCT open.
"""
from __future__ import annotations

import binascii
import sys
from pathlib import Path

import msgpack
import pytest

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_DIR, K_FILE,
    K_HARDLINK, MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive


PAYLOAD = b"o25-physical-owner-raw-payload\x00\xff"


def _archive(path: Path, edges: dict[str, str], *, target_kind: int = K_FILE) -> Path:
    """Build real r24 physical bytes, with a SHA-committed checkpoint index."""
    owner = ["owner.bin", target_kind, 0o644, 0,
             len(PAYLOAD) if target_kind == K_FILE else 0,
             sha(PAYLOAD) if target_kind == K_FILE else b"",
             [S_BLOB, 0] if target_kind == K_FILE else None]
    records = [owner]
    records.extend(
        [name, K_HARDLINK, 0o644, 0, len(PAYLOAD), sha(PAYLOAD), [target]]
        for name, target in edges.items()
    )
    manifest = {
        "v": VERSION,
        "files": sorted(records, key=lambda row: row[0]),
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }
    raw_index = msgpack.packb(manifest, use_bin_type=True)
    packed_index = zc(raw_index, 3)
    physical = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xFFFFFFFF, sha(PAYLOAD),
    ) + PAYLOAD
    header = HDR.pack(
        MAGIC, VERSION, 0, len(packed_index), len(raw_index),
        len(physical), sha(raw_index),
    )
    footer = FTR.pack(
        FMAGIC, 0, 1, 0, 0, len(packed_index), len(raw_index),
        0, sha(raw_index),
    )
    path.write_bytes(header + packed_index + physical + packed_index + footer)
    return path


def test_o25_direct_owner_and_alias_control(tmp_path):
    path = _archive(tmp_path / "control.cmpct", {"alias": "owner.bin"})
    assert preflight_archive(path)["files"] == 2
    with CMPCT(path) as reader:
        assert reader.read("owner.bin") == PAYLOAD
        assert reader.read("alias") == PAYLOAD
        assert reader.read_range("alias", 2, 7) == PAYLOAD[2:9]
        assert reader.read_raw_range_verified("alias", 3, 4) == PAYLOAD[3:7]
        assert reader.file_sha256("alias") == sha(PAYLOAD)
        assert reader.verify() == 2


@pytest.mark.parametrize("edges", [
    {"cycle": "cycle"},
    {"left": "right", "right": "left"},
    {"orphan": "unlisted"},
])
def test_o25_invalid_alias_graph_rejected_on_ordinary_open(tmp_path, edges):
    path = _archive(tmp_path / "invalid.cmpct", edges)
    with pytest.raises(ValidationError):
        preflight_archive(path)
    # A plain Reader must not expose a tree which can recurse without bound
    # or fail after extraction has already published unrelated members.
    with pytest.raises((IOError, ValueError), match="hardlink|owner"):
        with CMPCT(path):
            pass


def test_o25_wrong_kind_owner_rejected_on_ordinary_open(tmp_path):
    path = _archive(tmp_path / "directory-owner.cmpct", {"alias": "owner.bin"}, target_kind=K_DIR)
    with pytest.raises(ValidationError):
        preflight_archive(path)
    with pytest.raises((IOError, ValueError), match="hardlink|owner"):
        with CMPCT(path):
            pass


def test_o25_deep_acyclic_chain_avoids_python_call_stack(tmp_path):
    # Strict preflight deliberately accepts valid acyclic hardlink chains;
    # a Reader API must not impose Python's recursion depth as a hidden limit.
    count = max(sys.getrecursionlimit() + 64, 1300)
    edges = {f"alias{i:05d}": f"alias{i + 1:05d}" for i in range(count - 1)}
    edges[f"alias{count - 1:05d}"] = "owner.bin"
    path = _archive(tmp_path / "deep.cmpct", edges)
    assert preflight_archive(path)["files"] == count + 1
    with CMPCT(path) as reader:
        assert reader.read("alias00000") == PAYLOAD
        assert reader.read_range("alias00000", 1, 10) == PAYLOAD[1:11]
        assert reader.read_raw_range_verified("alias00000", 0, 3) == PAYLOAD[:3]
        assert reader.read(f"alias{count-1:05d}") == PAYLOAD
        assert reader.file_sha256("alias00000") == sha(PAYLOAD)
        # Every alias is SHA-checked by the genuine Reader; neither repeated
        # ownership lookups nor direct reads should depend on recursion depth.
        assert reader.verify() == count + 1


def test_o25_plain_checkpoint_has_no_hardlink_dependency(tmp_path):
    path = _archive(tmp_path / "plain.cmpct", {})
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as reader:
        assert reader.read("owner.bin") == PAYLOAD
        assert reader.read_range("owner.bin", 2, 5) == PAYLOAD[2:7]
        assert reader.read_raw_range_verified("owner.bin", 0, len(PAYLOAD)) == PAYLOAD
        assert reader.verify() == 1


def test_o25_branching_alias_graph_reuses_terminal_owner(tmp_path):
    # A shared intermediate alias must not turn N siblings into N full
    # traversals; all leaves must bind one terminal inode/bytes.
    edges = {"pivot01": "pivot02", "pivot02": "owner.bin"}
    edges.update({f"fan{i:04d}": "pivot01" for i in range(256)})
    path = _archive(tmp_path / "fanout.cmpct", edges)
    assert preflight_archive(path)["files"] == len(edges) + 1
    with CMPCT(path) as reader:
        for i in range(256):
            name = f"fan{i:04d}"
            assert reader.read(name) == PAYLOAD
            assert reader.read_range(name, 1, 4) == PAYLOAD[1:5]
            assert reader.file_sha256(name) == sha(PAYLOAD)
        assert reader.verify() == len(edges) + 1
