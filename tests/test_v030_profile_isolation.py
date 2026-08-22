from __future__ import annotations

import subprocess
import sys
import textwrap
import threading

from experiments import entropygraph_v030_geometry_overlay_g04 as research_g04
from experiments import entropygraph_v030_prefixgraph as research_pg
from experiments import entropygraph_v030_release_candidate as research_rc
from experiments import entropygraph_v030_canonical_final as canonical


def test_canonical_import_does_not_rebind_research_modules() -> None:
    """Prove import isolation in a fresh interpreter instead of inheriting pytest collection state.

    The repository intentionally retains historical/provisional research modules whose own tests may exercise
    temporary profile bindings.  A release-isolation test must therefore own its import order rather than
    snapshotting mutable module globals during pytest collection and comparing them much later after unrelated
    tests have run.  The child process gives this invariant the exact clean import boundary it is meant to test.
    """
    script = textwrap.dedent(
        """
        from experiments import entropygraph_v030_geometry_overlay_g04 as research_g04
        from experiments import entropygraph_v030_prefixgraph as research_pg
        from experiments import entropygraph_v030_release_candidate as research_rc

        before = (
            research_g04.MAG,
            research_g04.TAIL,
            research_pg.MAGIC,
            research_pg.TAIL,
            research_rc.G04,
            research_rc._prefixgraph_eligibility,
            research_rc._prefixgraph_locality,
        )

        from experiments import entropygraph_v030_canonical_final as canonical

        after = (
            research_g04.MAG,
            research_g04.TAIL,
            research_pg.MAGIC,
            research_pg.TAIL,
            research_rc.G04,
            research_rc._prefixgraph_eligibility,
            research_rc._prefixgraph_locality,
        )
        assert after == before
        assert canonical.G04_RESEARCH is not research_g04
        assert canonical.PG is not research_pg
        assert canonical.RC is not research_rc
        assert canonical.G04_RESEARCH.MAG == canonical.G04_MAGIC
        assert canonical.G04_RESEARCH.TAIL == canonical.G04_TAIL
        assert canonical.PG.MAGIC == canonical.PG_MAGIC
        assert canonical.PG.TAIL == canonical.PG_TAIL
        assert canonical.RC.G04 is canonical.SHARED
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_active_canonical_profile_context_is_invisible_to_concurrent_research_callers() -> None:
    entered = threading.Event()
    release = threading.Event()
    failure: list[BaseException] = []

    # Snapshot immediately before the operation under test. This deliberately ignores unrelated historical
    # research state established by earlier tests; the invariant is that a canonical operation never changes it.
    before = (
        research_g04.MAG,
        research_g04.TAIL,
        research_pg.MAGIC,
        research_pg.TAIL,
        research_rc.G04,
        research_rc._prefixgraph_eligibility,
        research_rc._prefixgraph_locality,
    )

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
        during = (
            research_g04.MAG,
            research_g04.TAIL,
            research_pg.MAGIC,
            research_pg.TAIL,
            research_rc.G04,
            research_rc._prefixgraph_eligibility,
            research_rc._prefixgraph_locality,
        )
        assert during == before
    finally:
        release.set()
        worker.join(timeout=5)

    assert not worker.is_alive()
    assert not failure
    after = (
        research_g04.MAG,
        research_g04.TAIL,
        research_pg.MAGIC,
        research_pg.TAIL,
        research_rc.G04,
        research_rc._prefixgraph_eligibility,
        research_rc._prefixgraph_locality,
    )
    assert after == before


def test_isolation_loader_restores_normal_import_resolution() -> None:
    canonical.PROFILE_ISOLATION.assert_research_modules_unchanged()
    assert canonical.PROFILE_ISOLATION.G04 is canonical.G04_RESEARCH
    assert canonical.PROFILE_ISOLATION.PG is canonical.PG
    assert canonical.PROFILE_ISOLATION.RC is canonical.RC

    # The ordinary import names still resolve to the ordinary research module objects after canonical setup.
    from experiments import entropygraph_v030_geometry_overlay_g04 as g04_again
    from experiments import entropygraph_v030_prefixgraph as pg_again
    from experiments import entropygraph_v030_release_candidate as rc_again

    assert g04_again is research_g04
    assert pg_again is research_pg
    assert rc_again is research_rc
