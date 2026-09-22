from __future__ import annotations

from benchmarks import v030_external_competitors_canonical as C


def _row(
    label: str,
    *,
    cb: int,
    zb: int,
    sb: int,
    ct: float,
    zt: float,
    st: float,
    zip_available: bool = True,
    zstd_available: bool = True,
) -> dict:
    return {
        "label": label,
        "formats": {
            "cmpct_v030": {"available": True, "archive_bytes": cb, "create_s": ct},
            "zip_deflate9": {"available": zip_available, "archive_bytes": zb, "create_s": zt},
            "tar_zstd19_solid": {"available": zstd_available, "archive_bytes": sb, "create_s": st},
        },
    }


def test_strict_scoreboard_counts_only_four_way_joint_wins() -> None:
    result = {
        "rows": [
            _row("green", cb=90, zb=100, sb=95, ct=0.8, zt=1.0, st=0.9),
            _row("zstd-time-red", cb=80, zb=100, sb=90, ct=1.0, zt=1.1, st=0.9),
            _row("zstd-size-red", cb=96, zb=100, sb=95, ct=0.7, zt=1.0, st=0.8),
        ]
    }
    s = C._strict_row_dominance(result)
    assert s["workload_count"] == 3
    assert s["complete_comparator_rows"] == 3
    assert s["strict_zip_size_wins"] == 3
    assert s["strict_zstd19_size_wins"] == 2
    assert s["strict_zip_create_wins"] == 3
    assert s["strict_zstd19_create_wins"] == 2
    assert s["strict_joint_wins"] == 1
    assert s["strict_joint_target"] == 3
    assert [row["strict_joint_win"] for row in s["rows"]] == [True, False, False]
    assert s["strict_no_ties_size_or_create"] is False


def test_strict_scoreboard_rejects_ties() -> None:
    result = {
        "rows": [
            _row("size-tie", cb=95, zb=100, sb=95, ct=0.7, zt=1.0, st=0.8),
            _row("time-tie", cb=90, zb=100, sb=95, ct=0.8, zt=1.0, st=0.8),
        ]
    }
    s = C._strict_row_dominance(result)
    assert s["strict_joint_wins"] == 0
    assert s["strict_zstd19_size_wins"] == 1
    assert s["strict_zstd19_create_wins"] == 1
    assert s["rows"][0]["strictly_beats_zstd19_size"] is False
    assert s["rows"][1]["strictly_beats_zstd19_create"] is False


def test_strict_scoreboard_missing_zstd_is_fail_closed() -> None:
    result = {
        "rows": [
            _row("complete", cb=90, zb=100, sb=95, ct=0.7, zt=1.0, st=0.8),
            _row("missing-zstd", cb=1, zb=100, sb=95, ct=0.01, zt=1.0, st=0.8, zstd_available=False),
        ]
    }
    s = C._strict_row_dominance(result)
    assert s["complete_comparator_rows"] == 1
    assert s["strict_joint_wins"] == 1
    missing = s["rows"][1]
    assert missing["comparators_complete"] is False
    assert missing["strict_joint_win"] is False
    assert missing["strictly_beats_zip_size"] is False
    assert missing["strictly_beats_zstd19_size"] is False
    assert missing["strictly_beats_zip_create"] is False
    assert missing["strictly_beats_zstd19_create"] is False


def test_strict_scoreboard_missing_zip_is_fail_closed() -> None:
    """The hard four-way contract cannot silently degrade to a Zstd-only authority."""
    result = {
        "rows": [
            _row("complete", cb=90, zb=100, sb=95, ct=0.7, zt=1.0, st=0.8),
            _row("missing-zip", cb=1, zb=100, sb=95, ct=0.01, zt=1.0, st=0.8, zip_available=False),
        ]
    }
    s = C._strict_row_dominance(result)
    assert s["complete_comparator_rows"] == 1
    assert s["strict_joint_wins"] == 1
    missing = s["rows"][1]
    assert missing["comparators_complete"] is False
    assert missing["strict_joint_win"] is False
    assert missing["strictly_beats_zip_size"] is False
    assert missing["strictly_beats_zstd19_size"] is False
    assert missing["strictly_beats_zip_create"] is False
    assert missing["strictly_beats_zstd19_create"] is False
