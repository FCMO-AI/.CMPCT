"""Canonical CMPCT v0.30 product implementation with isolated revision-25 profile state.

The reviewed implementation body is preserved in ``entropygraph_v030_canonical_final_impl.py`` and executed
*inside this public module's global namespace* while its Geometry, PrefixGraph, reader, admission and shared-
portfolio imports are temporarily routed to private canonical module namespaces. Ordinary research modules
therefore keep their historical CMPNX identities, while public canonical helpers retain normal Python dependency
injection/monkeypatch behavior because their ``__globals__`` is this module rather than a hidden re-export target.

Footnote: executing the preserved source here is deliberately different from importing it and copying function
objects afterward. Re-exported functions keep the hidden module's globals, so callers replacing a public reader
or candidate provider would appear to patch the canonical API while the operation silently used another object.
One execution namespace plus isolated dependencies removes both hazards without rewriting the reviewed product
implementation or introducing a second handwritten archive grammar.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_profile_isolation as _ISOLATION

_WRAPPER_DOC = __doc__
_IMPLEMENTATION_PATH = Path(__file__).with_name("entropygraph_v030_canonical_final_impl.py")

_ISOLATION.assert_research_modules_unchanged()
with _ISOLATION.canonical_import_context():
    _SOURCE = _IMPLEMENTATION_PATH.read_bytes()
    # Footnote: compile the preserved implementation as a module but execute it in *this* module dictionary.
    # Functions/classes therefore resolve later global substitutions through the public canonical namespace,
    # while the import statements executed right now bind only the isolated release-profile dependencies.
    exec(compile(_SOURCE, str(_IMPLEMENTATION_PATH), "exec"), globals(), globals())

# Keep the public wrapper's architectural explanation instead of exposing the preserved implementation's older
# module docstring. The executable implementation itself remains unchanged below the source boundary.
__doc__ = _WRAPPER_DOC
PROFILE_ISOLATION = _ISOLATION
IMPLEMENTATION_SOURCE = _IMPLEMENTATION_PATH

# No ordinary research module is mutated after initialization. The preserved implementation's historical
# ``_revision25_profile_context`` now snapshots/restores private clone state only; those assignments are
# idempotent inside the isolated graph and invisible to concurrent research calls.

if __name__ == "__main__":
    _main()
