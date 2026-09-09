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


class _PackedLengths:
    """Immutable dense uint64 node-length table used only by a validated authority.

    The ordinary preflight computes Python integers because that representation is convenient
    while proving the graph. Repeated reads need only indexed immutable lengths. Packing after
    proof avoids retaining one Python integer object per stored node while preserving exactly
    the same values and lookup semantics.
    """

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
    def uses_compact_lengths(self) -> bool:
        return isinstance(self._preflight.lengths, _PackedLengths)

    @property
    def modeled_preflight_bytes(self) -> int:
        """Stable state model: one uint64 output length per node plus two uint64 scalars."""
        return 8 * len(self._preflight.lengths) + 16

    @property
    def python_preflight_bytes(self) -> int:
        """Approximate CPython retained bytes for the proof object and length storage."""
        lengths = self._preflight.lengths
        if isinstance(lengths, _PackedLengths):
            length_bytes = lengths.python_bytes
        else:
            length_bytes = sys.getsizeof(lengths) + sum(sys.getsizeof(value) for value in lengths)
        return sys.getsizeof(self._preflight) + length_bytes


def _snapshot_program(program: Program) -> Program:
    if not isinstance(program, Program):
        raise TypeError("program must be Program")
    return Program(
        nodes=tuple(program.nodes),
        roots=MappingProxyType(dict(program.roots)),
        limits=program.limits,
    )


def _fully_preflight_snapshot(program: Program) -> tuple[Program, _Preflight]:
    snapshot = _snapshot_program(program)
    snapshot.validate_shape()
    return snapshot, _preflight(snapshot)


def validate_program_snapshot(program: Program) -> ValidatedProgram:
    """Snapshot and fully validate `program` once for repeated bounded reads.

    Nodes, refs, roots and limits are frozen dataclasses except that Program accepts any
    Mapping for roots. Copying roots behind MappingProxyType closes that last caller-mutable
    alias before validation authority is granted.
    """
    snapshot, preflight = _fully_preflight_snapshot(program)
    return ValidatedProgram(snapshot, preflight, _token=_CONSTRUCTION_TOKEN)


def validate_program_snapshot_compact(program: Program) -> ValidatedProgram:
    """Create the same authority while retaining node lengths in packed immutable storage.

    Full ordinary validation still happens before packing. The temporary Python tuple returned
    by `_preflight()` dies after construction; only the exact packed lengths and scalar proof
    values are retained by the authority.
    """
    snapshot, preflight = _fully_preflight_snapshot(program)
    compact = _Preflight(
        lengths=_PackedLengths(preflight.lengths),
        max_depth=preflight.max_depth,
        worst_work_bytes=preflight.worst_work_bytes,
    )
    return ValidatedProgram(snapshot, compact, _token=_CONSTRUCTION_TOKEN)