from __future__ import annotations

import threading

from experiments import entropygraph_v030_geometry_overlay_g04 as research_g04
from experiments import entropygraph_v030_prefixgraph as research_pg
from experiments import entropygraph_v030_release_candidate as research_rc

# Import the product only after capturing the ordinary research modules.  This ordering is deliberate: the old
# implementation rewrote these exact module objects while a canonical operation was active.
_RESEARCH_G04_MAGIC = research_g04.MAG
_RESEARCH_G04_TAIL = research_g04.TAIL
_RESEARCH_PG_MAGIC = research_pg.MAGIC
_RESEARCH_PG_TAIL = research_pg.TAIL
_RESEARCH_RC_G04 = research_rc.G04
_RESEARCH_RC_ELIGIBILITY = research_rc._prefixgraph_eligibility
_RESEARCH_RC_LOCALITY = research_rc._prefixgraph_locality

from experiments import entropygraph_v030_canonical_final as canonical  # noqa: E402


def test_canonical_import_does_not_rebind_research_modules() -> None:
    assert canonical.G04_RESEARCH is not research_g04
    assert canonical.PG is not research_pg
    assert canonical.RC is not research_rc

    assert research_g04.MAG == _RESEARCH_G04_MAGIC
    assert research_g04.TAIL == _RESEARCH_G04_TAIL
    assert research_pg.MAGIC == _RESEARCH_PG_MAGIC
    assert research_pg.TAIL == _RESEARCH_PG_TAIL
    assert research_rc.G04 is _RESEARCH_RC_G04
    assert research_rc._prefixgraph_eligibility is _RESEARCH_RC_ELIGIBILITY
    assert research_rc._prefixgraph_locality is _RESEARCH_RC_LOCALITY

    assert canonical.G04_RESEARCH.MAG == canonical.G04_MAGIC
    assert canonical.G04_RESEARCH.TAIL == canonical.G04_TAIL
    assert canonical.PG.MAGIC == canonical.PG_MAGIC
    assert canonical.PG.TAIL == canonical.PG_TAIL
    assert canonical.RC.G04 is canonical.SHARED

    # Footnote: canonical and research code reuse the same source files but execute with independent global
    # namespaces.  This is the invariant that removes import-order profile identity from released semantics.


def test_active_canonical_profile_context_is_invisible_to_concurrent_research_callers() -> None:
    entered = threading.Event()
    release = threading.Event()
    failure: list[BaseException] = []

    def canonical_operation() -> None:
        try:
            with canonical._revision25_profile_context():
                entered.set()
                if not release.wait(timeout=5):
                    raise AssertionError("test synchronization timeout")
        except BaseException as exc:  # pragma: no cover - surfaced in the owning thread below.
            failure.append(exc)
            entered.set()

    worker = threading.Thread(target=canonical_operation, name="canonical-profile-isolation-test")
    worker.start()
    assert entered.wait(timeout=5)
    try:
        # These are the values a direct research build/reader would resolve from its module globals while a
        # canonical operation is active.  They must remain exactly the pre-import research identities.
        assert research_g04.MAG == _RESEARCH_G04_MAGIC
        assert research_g04.TAIL == _RESEARCH_G04_TAIL
        assert research_pg.MAGIC == _RESEARCH_PG_MAGIC
        assert research_pg.TAIL == _RESEARCH_PG_TAIL
        assert research_rc.G04 is _RESEARCH_RC_G04
        assert research_rc._prefixgraph_eligibility is _RESEARCH_RC_ELIGIBILITY
        assert research_rc._prefixgraph_locality is _RESEARCH_RC_LOCALITY
    finally:
        release.set()
        worker.join(timeout=5)

    assert not worker.is_alive()
    assert not failure

    # Footnote: a coarse lock around canonical calls was insufficient because research callers did not acquire
    # that lock.  Isolation removes the shared mutable object entirely instead of asking unrelated callers to
    # coordinate with a release-only mutex.


def test_isolation_loader_restores_normal_import_resolution() -> None:
    canonical.PROFILE_ISOLATION.assert_research_modules_unchanged()
    assert canonical.PROFILE_ISOLATION.G04 is canonical.G04_RESEARCH
    assert canonical.PROFILE_ISOLATION.PG is canonical.PG
    assert canonical.PROFILE_ISOLATION.RC is canonical.RC

    # The ordinary import names still resolve to ordinary research modules after canonical initialization.
    from experiments import entropygraph_v030_geometry_overlay_g04 as g04_again
    from experiments import entropygraph_v030_prefixgraph as pg_again

    assert g04_again is research_g04
    assert pg_again is research_pg
