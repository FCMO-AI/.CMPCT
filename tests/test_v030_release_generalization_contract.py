from __future__ import annotations

from benchmarks import v030_release_generalization as gate


def test_accepted_v029_row_reconstruction_is_exact() -> None:
    rows = gate._accepted_v029_rows()
    assert len(rows) == 15
    assert sum(row["accepted_v029_bytes"] for row in rows.values()) == 137_501_815
    assert rows[("resemblance_hostile_v1", "01_shifted_versions")]["accepted_v029_bytes"] == 1_723_056
    assert rows[("resemblance_hostile_v1", "03_boundary_churn")]["accepted_v029_bytes"] == 79_876


def test_numeric_revision_floor_does_not_get_easier_on_smaller_v029_substrate() -> None:
    # Footnote: v0.29 is slightly smaller than v0.28. A naive percentage-only rule would lower the absolute
    # hurdle. The existing campaign explicitly carried 687,783 B forward, so v0.30 inherits that stricter
    # number rather than reverse-engineering a more convenient threshold from the current aggregate.
    assert gate.INHERITED_ABSOLUTE_REVISION_FLOOR == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES >= (gate.EXPECTED_V029_TOTAL + 199) // 200
    assert gate.MIN_IMPROVED_ROWS == 3
    assert gate.MAX_MEMBER_READ_AMP == 8.0
