"""Compile observed maximal constant runs into generic ONE fill/concat Law.

This is writer-side compilation only.  The reader ontology is unchanged: qualifying
constant spans become existing ``fill`` nodes; all other bytes remain Surprise and the
pieces are joined with ordinary ``concat``.  No run-specific reader operation exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.observe import RunOpportunity

MIN_FILL_RUN = 32


@dataclass(frozen=True)
class RunFillStats:
    observed_runs: int
    qualifying_runs: int
    fill_bytes: int
    surprise_bytes_current: int
    concat_refs: int
    bounded: bool


def _literal_pair(
    source: bytes,
    target: bytes,
    current_digest: str | None = None,
    previous_digest: str | None = None,
) -> tuple[Program, RunFillStats]:
    current = current_digest or sha256(target).hexdigest()
    previous = previous_digest or sha256(source).hexdigest()
    nodes = (Node("surprise", surprise=source), Node("surprise", surprise=target))
    program = Program(
        nodes,
        {
            "previous": Root(Ref(0), len(source), previous),
            "current": Root(Ref(1), len(target), current),
        },
        Limits(),
    )
    return program, RunFillStats(0, 0, 0, len(target), 0, True)


def program_from_observed_runs(
    source: bytes,
    target: bytes,
    runs: tuple[RunOpportunity, ...],
    *,
    min_fill_run: int = MIN_FILL_RUN,
    current_digest: str | None = None,
    previous_digest: str | None = None,
) -> tuple[Program, RunFillStats]:
    """Build a bounded pair Program from exact maximal-run evidence.

    Runs must be ordered, non-overlapping and byte-exact against ``target``.  Runs below
    the fixed economic floor remain Surprise.  If the resulting generic graph would
    exceed the existing node/ref cap, the function returns the ordinary literal Program
    rather than changing reader limits or inventing another representation mechanism.

    Trusted precomputed root digests may be supplied so callers that already paid root
    authentication do not accidentally charge the candidate a second full-source hash.
    """
    if type(source) is not bytes or type(target) is not bytes:
        raise TypeError("ONE run/fill compiler inputs must be bytes")
    if type(runs) is not tuple or any(not isinstance(run, RunOpportunity) for run in runs):
        raise TypeError("runs must be a tuple of RunOpportunity values")
    if type(min_fill_run) is not int or min_fill_run <= 0:
        raise ValueError("min_fill_run must be a positive integer")

    current = current_digest or sha256(target).hexdigest()
    previous = previous_digest or sha256(source).hexdigest()
    qualifying: list[RunOpportunity] = []
    previous_end = 0
    for run in runs:
        if run.start < previous_end or run.start < 0 or run.length <= 0:
            raise ValueError("observed runs must be ordered, positive and non-overlapping")
        end = run.start + run.length
        if end > len(target) or not 0 <= run.value <= 255:
            raise ValueError("observed run exceeds target or byte-value bounds")
        if target[run.start:end] != bytes([run.value]) * run.length:
            raise ValueError("observed run is not byte-exact against target")
        previous_end = end
        if run.length >= min_fill_run:
            qualifying.append(run)

    if not qualifying:
        program, _ = _literal_pair(source, target, current, previous)
        return program, RunFillStats(len(runs), 0, 0, len(target), 0, True)

    limits = Limits()
    nodes: list[Node] = [Node("surprise", surprise=source)]
    pieces: list[Ref] = []
    cursor = 0
    fill_bytes = 0
    surprise_current = 0

    for run in qualifying:
        if run.start > cursor:
            payload = target[cursor:run.start]
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=payload, declared_length=len(payload)))
            pieces.append(Ref(node_id))
            surprise_current += len(payload)
        node_id = len(nodes)
        nodes.append(Node("fill", count=run.length, value=run.value, declared_length=run.length))
        pieces.append(Ref(node_id))
        fill_bytes += run.length
        cursor = run.start + run.length

    if cursor < len(target):
        payload = target[cursor:]
        node_id = len(nodes)
        nodes.append(Node("surprise", surprise=payload, declared_length=len(payload)))
        pieces.append(Ref(node_id))
        surprise_current += len(payload)

    # Empty target is handled by the literal path above because it has no qualifying run.
    # Ref/node caps are kept unchanged.  A graph that does not fit is Crystallized back to
    # ordinary Surprise for this first compiler experiment rather than expanding limits.
    extra_root_node = 0 if len(pieces) == 1 else 1
    if len(nodes) + extra_root_node > limits.max_nodes or len(pieces) > limits.max_nodes:
        program, _ = _literal_pair(source, target, current, previous)
        return program, RunFillStats(len(runs), len(qualifying), 0, len(target), 0, False)

    if len(pieces) == 1:
        current_ref = pieces[0]
        concat_refs = 0
    else:
        root_id = len(nodes)
        nodes.append(Node("concat", refs=tuple(pieces), declared_length=len(target)))
        current_ref = Ref(root_id)
        concat_refs = len(pieces)

    program = Program(
        tuple(nodes),
        {
            "previous": Root(Ref(0), len(source), previous),
            "current": Root(current_ref, len(target), current),
        },
        limits,
    )
    return program, RunFillStats(
        observed_runs=len(runs),
        qualifying_runs=len(qualifying),
        fill_bytes=fill_bytes,
        surprise_bytes_current=surprise_current,
        concat_refs=concat_refs,
        bounded=True,
    )
