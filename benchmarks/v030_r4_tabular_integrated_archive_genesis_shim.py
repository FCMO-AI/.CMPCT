from __future__ import annotations

"""Compatibility shim for the integrated R4 archive falsifier.

The first integrated runner accidentally called a helper that does not exist in
``mosaic_v029_generalization_bench``.  This shim supplies the exact frozen
v0.29 stored-byte rows from the source-sealed ONE Genesis artifact
(run 34573437613, artifact 10191000395) and then executes the unchanged
integrated falsifier.  The 15 values sum to the final Genesis v0.29 total
137,499,525 B; Analytics is 6,135,172 B.

Research-only.  It changes neither contender, admission, owner, group size,
threshold, format nor product selector.
"""

import runpy

from benchmarks import mosaic_v029_generalization_bench as V029

_GENESIS_V029_STORED = {
    ("neutral_hostile_v1", "01_developer_repository"): 744_337,
    ("neutral_hostile_v1", "02_office_workspace"): 5_954_026,
    ("neutral_hostile_v1", "03_media_library"): 28_719_497,
    ("neutral_hostile_v1", "04_analytics_and_database"): 6_135_172,
    ("neutral_hostile_v1", "05_logs_and_telemetry"): 3_550_609,
    ("neutral_hostile_v1", "06_incremental_backups"): 8_223_844,
    ("neutral_hostile_v1", "07_incompressible_and_encrypted_like"): 10_193_958,
    ("neutral_hostile_v1", "08_many_tiny_files"): 420_318,
    ("neutral_hostile_v1", "09_ml_artifacts"): 13_836_439,
    ("neutral_hostile_v1", "10_large_mixed_binary"): 12_593_372,
    ("resemblance_hostile_v1", "01_shifted_versions"): 1_723_056,
    ("resemblance_hostile_v1", "02_false_neighbors"): 34_698_771,
    ("resemblance_hostile_v1", "03_boundary_churn"): 79_876,
    ("resemblance_hostile_v1", "04_deflate_family"): 14_597,
    ("resemblance_hostile_v1", "05_incompressible"): 10_611_653,
}

assert len(_GENESIS_V029_STORED) == 15
assert sum(_GENESIS_V029_STORED.values()) == 137_499_525
assert _GENESIS_V029_STORED[("neutral_hostile_v1", "04_analytics_and_database")] == 6_135_172


def _accepted_v029_rows() -> dict[tuple[str, str], dict[str, int]]:
    return {
        key: {"accepted_v029_bytes": value}
        for key, value in _GENESIS_V029_STORED.items()
    }


V029._accepted_v029_rows = _accepted_v029_rows
runpy.run_module("benchmarks.v030_r4_tabular_integrated_archive", run_name="__main__")
