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

_PRESERVED_STRONG_VERIFY = strong_verify


def _r25_build(staged_root: Path, out: Path) -> dict:
    """Build the r25 tournament while leaving final complete-product verification to this canonical parent."""
    started = time.perf_counter()
    with _revision25_profile_context():
        stats = dict(RC.build(staged_root, out, post_publish_verify=False))
    # Footnote: RC still strong-verifies every candidate that can win and proves the selected bytes survive its
    # atomic publication. Only RC's *second* published-path logical pass is deferred. ``build`` below resolves
    # this replacement through the shared module globals and always calls canonical ``strong_verify`` after the
    # exact r24-vs-r25 winner is published, so every user-visible product still receives that final proof once.
    return {**stats, "create_s": time.perf_counter() - started}


def strong_verify(archive: Path) -> dict:
    """Strong-verify canonical r25 in one content pass plus one authenticated manifest binding pass.

    The shared release reader already reconstructs every profile member, authenticates payload and logical
    identities, authenticates the complete content-graph tree, and enforces locality. The filesystem manifest is
    then read and bound to those authenticated metadata identities. Re-reading every regular member afterward
    proves the same bytes a second time and is deliberately avoided here.
    """
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        return _PRESERVED_STRONG_VERIFY(archive)

    with _revision25_profile_context():
        base = dict(POLICY.strong_verify(archive))
    if not base.get("ok"):
        return {**base, "format_revision": revision, "format_profile": profile}
    try:
        manifest = _validated_manifest(archive)
        user_tree = _semantic_tree_sha(manifest)
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "format_revision": revision,
            "format_profile": profile,
            "reader": "cmpct-v030-canonical-final-v1",
        }

    # Footnote: ``POLICY.strong_verify`` is the byte proof; ``_validated_manifest`` is the semantic binding.
    # The latter compares every manifest regular-file (size, SHA-256) identity with the authenticated profile
    # metadata, so the already verified content graph and the user-visible filesystem description cannot diverge.
    return {
        **base,
        "content_graph_tree_sha256": base.get("tree_sha256"),
        "tree_sha256": user_tree,
        "user_tree_sha256": user_tree,
        "format_revision": revision,
        "format_profile": profile,
        "filesystem_manifest_sha256": hashlib.sha256(manifest["raw"]).hexdigest(),
        "filesystem_entries": len(manifest["manifest"]["entries"]),
        "filesystem_semantics_verified": True,
        "regular_members_verified_by_policy_stream": len(manifest["regular"]),
        "verification_strategy": "single-content-pass-plus-authenticated-manifest-binding",
        "canonical_release_facade": "cmpct-v030-canonical-final-v1",
    }


if __name__ == "__main__":
    _main()
