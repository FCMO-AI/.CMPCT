"""Isolated canonical-profile module graph for CMPCT v0.30.

The research implementations remain the semantic owners of Geometry, PrefixGraph and the streamed reader, but
the release product must not rewrite their module globals in-place merely to select revision-25 magics. This
module loads those exact source files into private module namespaces, wires their dependencies to one another,
and binds the canonical r25 profile only inside that isolated graph.

The result preserves one source implementation per mechanism while removing process-global profile mutation:
research imports keep their historical CMPNX identities, canonical imports always see CMP25 identities, and
concurrent calls cannot observe one another's profile state.

Footnote: this is source reuse, not parser duplication. Each clone executes the same repository source file;
there is no second handwritten reader/encoder grammar to drift. The private module names exist only to give
those existing functions independent global namespaces for immutable release-profile configuration.
"""
from __future__ import annotations

import builtins
import importlib
import importlib.util
import sys
from types import ModuleType
from typing import Mapping

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
_REAL_IMPORT = builtins.__import__


def _private_importer(aliases: Mapping[str, ModuleType]):
    """Return an import function that resolves selected dependencies without touching global import state."""

    def local_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0:
            if name == "experiments" and fromlist:
                package = _REAL_IMPORT(name, globals, locals, fromlist, level)
                replacements = {
                    attr: aliases[f"experiments.{attr}"]
                    for attr in fromlist
                    if isinstance(attr, str) and f"experiments.{attr}" in aliases
                }
                if replacements:
                    proxy = ModuleType(package.__name__)
                    proxy.__dict__.update(package.__dict__)
                    proxy.__dict__.update(replacements)
                    return proxy
            if name in aliases:
                module = aliases[name]
                if fromlist:
                    return module
                package_name, attr = name.rsplit(".", 1)
                package = _REAL_IMPORT(package_name, globals, locals, (), level)
                proxy = ModuleType(package.__name__)
                proxy.__dict__.update(package.__dict__)
                setattr(proxy, attr, module)
                return proxy
        return _REAL_IMPORT(name, globals, locals, fromlist, level)

    return local_import


def _private_builtins(aliases: Mapping[str, ModuleType]) -> dict[str, object]:
    values: dict[str, object] = dict(vars(builtins))
    values["__import__"] = _private_importer(aliases)
    return values


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
    private_builtins = _private_builtins(aliases or {})
    try:
        module.__dict__["__builtins__"] = private_builtins
        clone_spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(clone_name, None)
        raise
    return module


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

# Transfer v3 and the frozen R3 Builder proved that the historical position-independent discovery source can be
# removed at the v0.30 attempt-5 child boundary without changing selected bytes or hard product invariants. Keep
# that accepted scheduler private to the canonical clone; ordinary v0.29/research imports remain untouched.
DISCOVERY_WORKER = importlib.import_module(DISCOVERY_WORKER_SOURCE)
SHARED.V030_SCHED = DISCOVERY_WORKER
SHARED.CHILD_RESULT_TIMEOUT_S = DISCOVERY_WORKER.CHILD_RESULT_TIMEOUT_S

RC = _clone(
    RC_SOURCE,
    "experiments._v030_canonical_release_candidate",
    aliases={G04_SOURCE: SHARED, PG_SOURCE: PG, POLICY_SOURCE: POLICY},
)

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


class _CanonicalImportContext:
    """Give one executing module a private import view without publishing aliases process-wide."""

    def __init__(self) -> None:
        self._namespace: dict[str, object] | None = None
        self._previous: object = _MISSING

    def __enter__(self) -> None:
        namespace = sys._getframe(1).f_globals
        self._namespace = namespace
        self._previous = namespace.get("__builtins__", _MISSING)
        namespace["__builtins__"] = _private_builtins(CANONICAL_ALIASES)

    def __exit__(self, exc_type, exc, tb) -> bool:
        assert self._namespace is not None
        if self._previous is _MISSING:
            self._namespace.pop("__builtins__", None)
        else:
            self._namespace["__builtins__"] = self._previous
        self._namespace = None
        self._previous = _MISSING
        return False


def canonical_import_context() -> _CanonicalImportContext:
    """Expose private dependencies only to the canonical implementation's execution namespace."""
    return _CanonicalImportContext()


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
