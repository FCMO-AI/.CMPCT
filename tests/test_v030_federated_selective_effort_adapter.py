from __future__ import annotations

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v4 as V4


def test_accepted_v029_compatibility_adapter_is_non_recursive_and_exact() -> None:
    rows = V4._accepted_rows_with_legacy_alias()
    assert len(rows) == 15
    assert sum(int(row["accepted_v029_bytes"]) for row in rows.values()) == 137_499_525
    for row in rows.values():
        assert int(row["archive_bytes"]) == int(row["accepted_v029_bytes"])


def test_accepted_v029_compatibility_adapter_restores_authoritative_loader() -> None:
    original = V1.GENERAL._accepted_v029_rows
    V1.GENERAL._accepted_v029_rows = V4._accepted_rows_with_legacy_alias
    try:
        rows = V1.GENERAL._accepted_v029_rows()
        assert len(rows) == 15
        assert sum(int(row["archive_bytes"]) for row in rows.values()) == 137_499_525
    finally:
        V1.GENERAL._accepted_v029_rows = original
    assert V1.GENERAL._accepted_v029_rows is original
