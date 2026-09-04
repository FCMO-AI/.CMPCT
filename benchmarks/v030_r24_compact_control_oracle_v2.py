from __future__ import annotations

"""Execution repair for the r24 compact-control frontier.

v1's measurement logic is authoritative, but its target helper assumed its scratch directory already existed.
This wrapper creates only that directory and leaves corpus identity, archive construction, comparator timing,
control-plane transform, strict inequalities, and schema unchanged.
"""

from pathlib import Path

from benchmarks import v030_r24_compact_control_oracle as BASE

_ORIGINAL_MEASURE_TARGET = BASE._measure_target


def _measure_target_with_workdir(source: Path, work: Path) -> dict:
    Path(work).mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_MEASURE_TARGET(source, work)


def main() -> None:
    BASE._measure_target = _measure_target_with_workdir
    try:
        BASE.main()
    finally:
        BASE._measure_target = _ORIGINAL_MEASURE_TARGET


if __name__ == "__main__":
    main()
