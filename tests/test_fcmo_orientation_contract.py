from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PARENT_ORIENTATION = (
    "AGENTS.md",
    "AGENT_HUB.md",
    "AGI_ENGINEERING_OPERATIONS_STANDARD.md",
    "COMMUNICATION_SURFACE_INTELLIGENCE_STANDARD.md",
)


def test_adopted_parent_orientation_files_are_durable() -> None:
    missing = [path for path in REQUIRED_PARENT_ORIENTATION if not (ROOT / path).is_file()]
    assert not missing, f"missing adopted parent-orientation files: {missing}"
