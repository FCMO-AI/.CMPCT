"""Reusable full-Program validation authority for ONE-G0.2 research.

Selective reads must not make archive validity depend on the requested root or range. The
reference preflight therefore validates every stored node. Repeating that O(graph) proof on
every range request is unnecessary once the exact Program has been opened and frozen.

`validate_program_snapshot()` creates an immutable snapshot, runs the ordinary full shape and
resource preflight exactly once, and returns an authority that can be consumed by optimized
read paths. It changes no ONE wire or validation semantic.
"""
from __future__ import annotations

from array import array
import struct
import sys
from types import MappingProxyType

from .ir import Program
from .vm import _Preflight, _preflight

_CONSTRUCTION_TOKEN = object()
_U64 = struct.Struct("<Q")
_MAX_U64 = (1 << 64) - 1


class _PackedLengths:
    """Immutable dense uint64 node-length table used only by a validated authority."""

    __slots__ = ("_blob", "_count")

    def __init__(self, values) -> None:
        packed = array("Q", values)
        if packed.itemsize != 8:
            raise RuntimeError("platform uint64 array is not 8 bytes")
        if sys.byteorder != "little":
            packed.byteswap()
        self._blob = packed.tobytes()
        self._count = len(packed)

    def __len__(self) -> int:
        return self._count

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[i] for i in range(*index.indices(self._count)))
        if type(index) is not int:
            raise TypeError("packed length index must be int or slice")
        if index < 0:
            index += self._count
        if index < 0 or index >= self._count:
            raise IndexError(index)
        return _U64.unpack_from(self._blob, index * 8)[0]

    def __iter__(self):
        for index in range(self._count):
            yield _U64.unpack_from(self._blob, index * 8)[0]

    @property
    def packed_bytes(self) -> int:
        return len(self._blob)

    @property
    def python_bytes(self) -> int:
        return sys.getsizeof(self) + sys.getsizeof(self._blob)


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
    def uses_compact_lengths(self) -> bool:
        return isinstance(self._preflight.lengths, _PackedLengths)

    @property
    def modeled_preflight_bytes(self) -> int:
        return 8 * len(self._preflight.lengths) + 16

    @property
    def python_preflight_bytes(self) -> int:
        lengths = self._preflight.lengths
        if isinstance(lengths, _PackedLengths):
            length_bytes = lengths.python_bytes
        else:
            length_bytes = sys.getsizeof(lengths) + sum(sys.getsizeof(value) for value in lengths)
        return sys.getsizeof(self._preflight) + length_bytes


def _snapshot_program(program: Program) -> Program:
    if not isinstance(program, Program):
        raise TypeError("program must be Program")
    return Program(nodes=tuple(program.nodes), roots=MappingProxyType(dict(program.roots)), limits=program.limits)


def _fully_preflight_snapshot(program: Program) -> tuple[Program, _Preflight]:
    snapshot = _snapshot_program(program)
    snapshot.validate_shape()
    return snapshot, _preflight(snapshot)


def validate_program_snapshot(program: Program) -> ValidatedProgram:
    snapshot, preflight = _fully_preflight_snapshot(program)
    return ValidatedProgram(snapshot, preflight, _token=_CONSTRUCTION_TOKEN)


def validate_program_snapshot_compact(program: Program) -> ValidatedProgram:
    """Retain validated node lengths densely when the exact semantic domain permits it.

    Full ordinary validation always happens first. ONE's research IR currently permits limits
    above uint64, so an extreme valid logical graph must not become invalid merely because this
    optional in-memory representation is narrower. Such graphs retain the ordinary certificate.
    """
    snapshot, preflight = _fully_preflight_snapshot(program)
    if any(value > _MAX_U64 for value in preflight.lengths):
        return ValidatedProgram(snapshot, preflight, _token=_CONSTRUCTION_TOKEN)
    compact = _Preflight(
        lengths=_PackedLengths(preflight.lengths),
        max_depth=preflight.max_depth,
        worst_work_bytes=preflight.worst_work_bytes,
    )
    return ValidatedProgram(snapshot, compact, _token=_CONSTRUCTION_TOKEN)