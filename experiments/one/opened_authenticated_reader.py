"""Shared-open authenticated selective reader for ONE-G0.2 research.

This is an engineering surface over already-promoted mechanisms, not a new ONE format.
Opening proves complete Program validity once and binds one immutable authentication tree/root
commitment. Repeated reads then execute only authenticated native reconstruction cones.
"""
from __future__ import annotations

from .auth_tree import AuthTree
from .authenticated_native_selective_cone import (
    AuthenticatedNativeSelectiveStats,
    reconstruct_validated_authenticated_native_range,
)
from .ir import OneError, Program
from .validated_program import ValidatedProgram, validate_program_snapshot_compact

_CONSTRUCTION_TOKEN = object()


class OpenedAuthenticatedReader:
    """Opaque shared-open authority for repeated authenticated selective reads."""

    __slots__ = ("_validated", "_root_name", "_tree", "_expected_root", "_sealed")

    def __init__(
        self,
        validated: ValidatedProgram,
        root_name: str,
        tree: AuthTree,
        expected_root: bytes,
        *,
        _token: object,
    ) -> None:
        if _token is not _CONSTRUCTION_TOKEN:
            raise TypeError("OpenedAuthenticatedReader must be created by open_authenticated_reader")
        object.__setattr__(self, "_validated", validated)
        object.__setattr__(self, "_root_name", root_name)
        object.__setattr__(self, "_tree", tree)
        object.__setattr__(self, "_expected_root", expected_root)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("OpenedAuthenticatedReader is immutable")
        object.__setattr__(self, name, value)

    @property
    def root_name(self) -> str:
        return self._root_name

    @property
    def validation_state_bytes(self) -> int:
        return self._validated.python_preflight_bytes

    @property
    def uses_compact_validation(self) -> bool:
        return self._validated.uses_compact_lengths

    @property
    def auth_index_bytes(self) -> int:
        return self._tree.stored_index_bytes

    def read(self, start: int, length: int) -> tuple[bytes, AuthenticatedNativeSelectiveStats]:
        return reconstruct_validated_authenticated_native_range(
            self._validated,
            self._root_name,
            self._tree,
            self._expected_root,
            start,
            length,
        )


def open_authenticated_reader(
    program: Program,
    root_name: str,
    tree: AuthTree,
    expected_root: bytes,
) -> OpenedAuthenticatedReader:
    """Validate/snapshot a Program once and bind its selective authentication authority.

    The expected AuthTree commitment is checked at open. Each read still authenticates the
    reconstructed leaf payloads against that commitment; opening never substitutes trust in
    caller-owned mutable Program state or a whole-root reconstruction shortcut.
    """
    if not isinstance(tree, AuthTree):
        raise TypeError("tree must be AuthTree")
    if type(expected_root) is not bytes or len(expected_root) != 32:
        raise OneError("expected authentication root must be 32 bytes")
    if expected_root != tree.root:
        raise OneError("authentication tree does not match expected root")

    validated = validate_program_snapshot_compact(program)
    root = validated.program.roots.get(root_name)
    if root is None:
        raise OneError(f"unknown root {root_name!r}")
    if tree.total_len != root.length:
        raise OneError("authentication tree length does not match selected root")

    return OpenedAuthenticatedReader(
        validated,
        root_name,
        tree,
        bytes(expected_root),
        _token=_CONSTRUCTION_TOKEN,
    )
