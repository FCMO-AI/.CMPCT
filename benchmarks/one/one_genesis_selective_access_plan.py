from __future__ import annotations

"""Contender-neutral selective request selection for the Genesis gate.

Frozen by ONE_GENESIS_SELECTIVE_ACCESS_PLAN_v0.1_2026-09-10.md.  This
module selects requests only; it never executes a contender.
"""

from dataclasses import dataclass
from pathlib import Path
import stat

PLAN_VERSION = "largest-regular-member-lexical-tie-v1"


@dataclass(frozen=True)
class SelectiveRequest:
    status: str
    selection_rule: str = PLAN_VERSION
    relative_path: str | None = None
    requested_bytes: int | None = None
    reason: str | None = None

    def to_dict(self) -> dict:
        result = {"status": self.status, "selection_rule": self.selection_rule}
        if self.relative_path is not None:
            result["relative_path"] = self.relative_path
        if self.requested_bytes is not None:
            result["requested_bytes"] = self.requested_bytes
        if self.reason is not None:
            result["reason"] = self.reason
        return result


def _regular_members(root: Path) -> list[tuple[str, int]]:
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"workload root is not a directory: {root}")
    rows: list[tuple[str, int]] = []
    for path in root.rglob("*"):
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError as exc:
            raise RuntimeError(f"workload mutated during selective request selection: {path}") from exc
        if not stat.S_ISREG(mode):
            continue
        rel = path.relative_to(root).as_posix()
        rows.append((rel, path.stat().st_size))
    rows.sort(key=lambda item: item[0])
    return rows


def select_primary_request(root: Path) -> SelectiveRequest:
    members = _regular_members(root)
    if not members:
        return SelectiveRequest(
            status="unavailable",
            reason="workload has no regular file to select",
        )
    if len(members) == 1:
        return SelectiveRequest(
            status="unavailable",
            relative_path=members[0][0],
            requested_bytes=members[0][1],
            reason="single regular member would collapse selective access into whole-object access",
        )
    # max length, then lexical minimum. Avoid platform directory-order dependence.
    max_size = max(size for _rel, size in members)
    rel, size = min((rel, size) for rel, size in members if size == max_size)
    return SelectiveRequest(status="selected", relative_path=rel, requested_bytes=size)
