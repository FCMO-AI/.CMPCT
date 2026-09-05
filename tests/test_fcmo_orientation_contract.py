from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FCMO_ORIENTATION = (
    "AGENTS.md",
    "AGENT_HUB.md",
    "AGI_ENGINEERING_OPERATIONS_STANDARD.md",
    "COMMUNICATION_SURFACE_INTELLIGENCE_STANDARD.md",
)


def test_adopted_fcmo_orientation_files_are_durable() -> None:
    missing = [path for path in REQUIRED_FCMO_ORIENTATION if not (ROOT / path).is_file()]
    assert not missing, f"missing adopted FCMO orientation files: {missing}"
