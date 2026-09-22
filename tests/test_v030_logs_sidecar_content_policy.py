from __future__ import annotations

import gzip
from pathlib import Path

from benchmarks import v030_logs_inverse_edge_sidecar_pack_content_policy as P


def test_inverse_edge_discovery_ignores_extensions(tmp_path: Path) -> None:
    plain = (b"2026-09-01 event=value\n" * 256)
    # Deliberately lie with both names: the plain member looks compressed, while the gzip
    # sidecar has no useful extension. Admission must follow bytes + exact decoded identity.
    (tmp_path / "plain.gz").write_bytes(plain)
    (tmp_path / "opaque.data").write_bytes(gzip.compress(plain, compresslevel=6, mtime=0))

    rows, edges, stats = P._scan_and_edges(tmp_path)
    assert stats["uses_path_or_suffix_for_codec_admission"] is False
    assert stats["decoded_sidecars"] == 1
    assert stats["inverse_edges"] == 1
    target = next(iter(edges))
    source, codec = edges[target]
    assert codec == "gzip"
    assert rows[target]["rel"] == "plain.gz"
    assert rows[source]["rel"] == "opaque.data"


def test_segment_and_direct_group_policy_is_path_invariant(tmp_path: Path) -> None:
    plain_a = b"a" * 1024
    plain_b = b"b" * 1200
    zipped_a = gzip.compress(plain_a, compresslevel=6, mtime=0)
    zipped_b = gzip.compress(plain_b, compresslevel=6, mtime=0)
    # None of these suffixes describe content correctly.
    for name, raw in (("a.zst", plain_a), ("b.xz", plain_b), ("c.log", zipped_a), ("d.bin", zipped_b)):
        (tmp_path / name).write_bytes(raw)

    rows, edges, _ = P._scan_and_edges(tmp_path)
    segments, amp, unit = P._plan_segments(rows, edges)
    groups = P._plan_direct_groups(rows, edges, segments)

    assert len(edges) == 2
    assert amp <= P.MAX_MEMBER_AMPLIFICATION
    assert unit <= P.MAX_DECODE_UNIT
    # Both retained gzip sources are grouped by detected codec, not their .log/.bin names.
    assert len(groups) == 1
    assert {rows[i]["content_codec"] for i in groups[0]} == {"gzip"}
