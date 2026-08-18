"""Canonical CMPCT v0.30 product implementation with isolated revision-25 profile state.

The implementation body is preserved verbatim in ``entropygraph_v030_canonical_final_impl``.  This front module
loads that exact source against an isolated module graph whose Geometry, PrefixGraph, reader, admission and shared
portfolio globals are private to the release product.  Ordinary research modules therefore keep their historical
CMPNX profile identities and cannot observe canonical r25 profile rebinding through import order or concurrency.

Footnote: the split is intentionally mechanical rather than a rewrite.  Keeping the reviewed implementation blob
intact avoids deleting design notes or subtly changing product behavior while removing the process-global profile
mutation defect found during T03 adversarial review.
"""
from __future__ import annotations

import importlib

from experiments import entropygraph_v030_profile_isolation as _ISOLATION

_ISOLATION.assert_research_modules_unchanged()
with _ISOLATION.canonical_import_context():
    _IMPLEMENTATION = importlib.import_module("experiments.entropygraph_v030_canonical_final_impl")

# Re-export the complete implementation surface, including intentionally testable private helpers. Functions
# retain the implementation module's globals, which are already bound to the isolated canonical dependency graph.
for _name, _value in vars(_IMPLEMENTATION).items():
    if _name in {
        "__name__",
        "__package__",
        "__loader__",
        "__spec__",
        "__file__",
        "__cached__",
        "__builtins__",
        "__doc__",
    }:
        continue
    globals()[_name] = _value

# The release wrapper itself owns these diagnostic handles so tests can prove isolation directly.
PROFILE_ISOLATION = _ISOLATION
IMPLEMENTATION_MODULE = _IMPLEMENTATION

# Footnote: no ordinary research module is mutated after this import. The implementation's historical
# ``_revision25_profile_context`` now snapshots and restores private clone state only; its assignments are
# idempotent inside that isolated graph and invisible to concurrent research calls.

if __name__ == "__main__":
    # Preserve the pre-split CLI contract. Importing the implementation under its private module name means its
    # own ``if __name__ == '__main__'`` block cannot fire, so the wrapper delegates explicitly.
    _IMPLEMENTATION._main()
