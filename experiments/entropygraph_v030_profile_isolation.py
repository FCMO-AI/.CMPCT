"""Isolated canonical-profile module graph for CMPCT v0.30.

The research implementations remain the semantic owners of Geometry, PrefixGraph and the streamed reader, but
the release product must not rewrite their module globals in-place merely to select revision-25 magics.  This
module loads those exact source files into private module namespaces, wires their dependencies to one another,
and binds the canonical r25 profile only inside that isolated graph.

The result preserves one source implementation per mechanism while removing process-global profile mutation:
research imports keep their historical CMPNX identities, canonical imports always see CMP25 identities, and
concurrent calls cannot observe one another's profile state.

Footnote: this is source reuse, not parser duplication.  Each clone executes the same repository source file;
there is no second handwritten reader/encoder grammar to drift.  The private module names exist only to give
those existing functions independent global namespaces for immutable release-profile configuration.
"""
from __future__ import annotations

from contextlib import contextmanager
import importlib
import importlib.util
import sys
from types import ModuleType
from typing import Iterator, Mapping

G04_SOURCE = "experiments.entropygraph_v030_geometry_overlay_g04"
PG_SOURCE = "experiments.entropygraph_v030_prefixgraph"
READER_SOURCE = "experiments.entropygraph_v030_release_reader"
POLICY_SOURCE = "experiments.entropygraph_v030_release_reader_policy"
ADMISSION_SOURCE = "experiments.entropygraph_v030_release_admission"
SHARED_SOURCE = "experiments.entropygraph_v030_shared_portfolio"
RC_SOURCE = "experiments.entropygraph_v030_release_candidate"
DISCOVERY_WORKER_SOURCE = "experiments.entropygraph_v030_discovery_neutral_worker"

G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PG_MAGIC = b"CMP25PG\0"
PG_TAIL = b"C25PGTL\0"

_MISSING = object()


@contextmanager
def _temporary_aliases(aliases: Mapping[str, ModuleType]) -> Iterator[None]:
    """Temporarily make absolute ``experiments.X`` imports resolve to private clone modules.

    Footnote: both ``sys.modules`` and the package attribute are changed because ``from experiments import X``
    may consult either cache.  Every prior value is restored in ``finally`` so loading the release graph cannot
    leave ordinary research imports redirected after initialization.
    """
    package = importlib.import_module("experiments")
    saved_modules: dict[str, object] = {}
    saved_attrs: dict[str, object] = {}
    try:
        for fullname, module in aliases.items():
            attr = fullname.rsplit(".", 1)[-1]
            saved_modules[fullname] = sys.modules.get(fullname, _MISSING)
            saved_attrs[attr] = getattr(package, attr, _MISSING)
            sys.modules[fullname] = module
            setattr(package, attr, module)
        yield
    finally:
        for fullname in reversed(tuple(aliases)):
            attr = fullname.rsplit(".", 1)[-1]
            previous_module = saved_modules[fullname]
            if previous_module is _MISSING:
                sys.modules.pop(fullname, None)
            else:
                sys.modules[fullname] = previous_module  # type: ignore[assignment]
            previous_attr = saved_attrs[attr]
            if previous_attr is _MISSING:
                try:
                    delattr(package, attr)
                except AttributeError:
                    pass
            else:
                setattr(package, attr, previous_attr)


def _clone(source_name: str, clone_name: str, *, aliases: Mapping[str, ModuleType] | None = None) -> ModuleType:
    """Execute one existing source module in an independent private global namespace."""
    source_spec = importlib.util.find_spec(source_name)
    if source_spec is None or source_spec.origin is None:
        raise RuntimeError(f"cannot resolve v0.30 semantic-owner source module: {source_name}")
    clone_spec = importlib.util.spec_from_file_location(clone_name, source_spec.origin)
    if clone_spec is None or clone_spec.loader is None:
        raise RuntimeError(f"cannot construct v0.30 isolated module spec: {source_name}")
    module = importlib.util.module_from_spec(clone_spec)
    sys.modules[clone_name] = module
    try:
        with _temporary_aliases(aliases or {}):
            clone_spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(clone_name, None)
        raise
    return module


# Build the private dependency graph in dependency order.  Only the private clones receive canonical profile
# identities; the ordinary research modules loaded elsewhere in the process remain untouched.
G04 = _clone(G04_SOURCE, "experiments._v030_canonical_g04")
G04.MAG = G04_MAGIC
G04.TAIL = G04_TAIL

PG = _clone(PG_SOURCE, "experiments._v030_canonical_prefixgraph")
PG.MAGIC = PG_MAGIC
PG.TAIL = PG_TAIL

READER = _clone(
    READER_SOURCE,
    "experiments._v030_canonical_release_reader",
    aliases={G04_SOURCE: G04, PG_SOURCE: PG},
)
POLICY = _clone(
    POLICY_SOURCE,
    "experiments._v030_canonical_release_reader_policy",
    aliases={READER_SOURCE: READER},
)
ADMISSION = _clone(
    ADMISSION_SOURCE,
    "experiments._v030_canonical_release_admission",
    aliases={PG_SOURCE: PG, POLICY_SOURCE: POLICY},
)
SHARED = _clone(
    SHARED_SOURCE,
    "experiments._v030_canonical_shared_portfolio",
    aliases={G04_SOURCE: G04},
)

# Transfer v3 proved that the historical position-independent discovery source contributes no selected bytes on
# the complete frozen release-runtime matrix while exporting measurable attempt-5 search cost. Bind the accepted
# R3 neutralization only inside this private canonical shared clone. The provider itself scopes the override to
# the spawned attempt-5 child and restores it in ``finally``; ordinary v0.29/research imports keep their historical
# worker and discovery source untouched, preserving them as independent byte/evidence oracles.
DISCOVERY_WORKER = importlib.import_module(DISCOVERY_WORKER_SOURCE)
SHARED.V029_SCHED = DISCOVERY_WORKER

RC = _clone(
    RC_SOURCE,
    "experiments._v030_canonical_release_candidate",
    aliases={G04_SOURCE: SHARED, PG_SOURCE: PG, POLICY_SOURCE: POLICY},
)

# The release-only admission helpers are a stricter replacement for the older research selector helpers.
# Bind them once inside the private graph rather than rewriting the public research module on every operation.
RC.G04 = SHARED
RC.PG = PG
RC.READER = POLICY
RC._prefixgraph_eligibility = ADMISSION.prefixgraph_eligibility
RC._prefixgraph_locality = ADMISSION.prefixgraph_locality

CANONICAL_ALIASES: dict[str, ModuleType] = {
    G04_SOURCE: G04,
    PG_SOURCE: PG,
    ADMISSION_SOURCE: ADMISSION,
    RC_SOURCE: RC,
    POLICY_SOURCE: POLICY,
    SHARED_SOURCE: SHARED,
}


@contextmanager
def canonical_import_context() -> Iterator[None]:
    """Expose the isolated graph only while importing the canonical implementation module."""
    with _temporary_aliases(CANONICAL_ALIASES):
        yield


def assert_research_modules_unchanged() -> None:
    """Fail if canonical initialization ever starts mutating ordinary research profile identities."""
    research_g04 = importlib.import_module(G04_SOURCE)
    research_pg = importlib.import_module(PG_SOURCE)
    if research_g04 is G04 or research_pg is PG:
        raise RuntimeError("canonical profile isolation leaked private modules into research imports")
    if research_g04.MAG == G04_MAGIC or research_pg.MAGIC == PG_MAGIC:
        raise RuntimeError("canonical profile initialization rewrote research module identity")


__all__ = [
    "G04",
    "PG",
    "READER",
    "POLICY",
    "ADMISSION",
    "SHARED",
    "RC",
    "G04_MAGIC",
    "G04_TAIL",
    "PG_MAGIC",
    "PG_TAIL",
    "canonical_import_context",
    "assert_research_modules_unchanged",
]
