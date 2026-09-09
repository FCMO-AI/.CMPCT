"""Reusable full-Program validation authority for ONE-G0.2 research.

Selective reads must not make archive validity depend on the requested root or range. The
reference preflight therefore validates every stored node. Repeating that O(graph) proof on
every range request is unnecessary once the exact Program has been opened and frozen.

`validate_program_snapshot()` creates an immutable snapshot, runs the ordinary full shape and
resource preflight exactly once, and returns an authority that can be consumed by optimized
read paths. It changes no ONE wire or validation semantic.
"""
from __future__ import annotations

import sys
from types import MappingProxyType

from .ir import Program
from .vm import _Preflight, _preflight

_CONSTRUCTION_TOKEN = object()


class ValidatedProgram:
    """Opaque sealed authority proving one immutable Program snapshot passed full preflight."""

    __slots__ = ("_program", "_preflight", "_sealed")

    def __init__(self, program: Program, preflight: _Preflight, *, _token: object) -> None:
        if _token is not _CONSTRUCTION_TOKEN:
            raise TypeError("ValidatedProgram must be created by validate_program_snapshot")
        object.__setattr__(self, "_program", program)
        object.__setattr__(self, "_preflight", preflight)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        # A validation capability is useful only if its identity cannot later be rebound to
        # another Program. This protects normal in-process use against stale-authority bugs;
        # Python reflection is not treated as a hostile-process security boundary.
        if getattr(self, "_sealed", False):
            raise AttributeError("ValidatedProgram is immutable")
        object.__setattr__(self, name, value)

    @property
    def program(self) -> Program:
        return self._program

    @property
    def preflight(self) -> _Preflight:
        return self._preflight

    @property
    def preflight_entry_count(self) -> int:
        return len(self._preflight.lengths)

    @property
    def modeled_preflight_bytes(self) -> int:
        """Stable state model: one uint64 output length per node plus two uint64 scalars."""
        return 8 * len(self._preflight.lengths) + 16

    @property
    def python_preflight_bytes(self) -> int:
        """Approximate CPython retained bytes for the proof object and its length integers."""
        return (
            sys.getsizeof(self._preflight)
            + sys.getsizeof(self._preflight.lengths)
            + sum(sys.getsizeof(value) for value in self._preflight.lengths)
        )


def validate_program_snapshot(program: Program) -> ValidatedProgram:
    """Snapshot and fully validate `program` once for repeated bounded reads.

    Nodes, refs, roots and limits are frozen dataclasses except that Program accepts any
    Mapping for roots. Copying roots behind MappingProxyType closes that last caller-mutable
    alias before validation authority is granted.
    """
    if not isinstance(program, Program):
        raise TypeError("program must be Program")
    snapshot = Program(
        nodes=tuple(program.nodes),
        roots=MappingProxyType(dict(program.roots)),
        limits=program.limits,
    )
    snapshot.validate_shape()
    preflight = _preflight(snapshot)
    return ValidatedProgram(snapshot, preflight, _token=_CONSTRUCTION_TOKEN)
