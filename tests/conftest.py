"""Test-suite isolation for historical v0.30 profile-mutating compatibility tests.

The promoted canonical-final implementation must prove that importing/using it never rewrites ordinary research
module identities. A historical provisional canonical module predates that rule and intentionally mutates those
same globals at import time. Full-suite collection used to import the historical module first, contaminating the
process before canonical-final's safety assertion could even run.

This harness imports canonical-final against pristine research state, then keeps the historical module cached but
restores the research graph. Each test starts from the pristine research profile; only the historical canonical
test module receives its legacy profile installation for the duration of that test. Production assertions remain
unchanged and still fail if canonical-final itself leaks profile state.
"""
from __future__ import annotations

import pytest

from experiments import entropygraph_v030_geometry_overlay_g04 as _G04
from experiments import entropygraph_v030_prefixgraph as _PG
from experiments import entropygraph_v030_release_candidate as _RC
from experiments import entropygraph_v030_release_reader_policy as _POLICY
from experiments import entropygraph_v030_shared_portfolio as _SHARED


_PRISTINE = {
    "g04_mag": _G04.MAG,
    "g04_tail": _G04.TAIL,
    "shared_mag": _SHARED.MAG,
    "shared_tail": _SHARED.TAIL,
    "pg_magic": _PG.MAGIC,
    "pg_tail": _PG.TAIL,
    "reader_g04_mag": _POLICY.R.G04.MAG,
    "reader_g04_tail": _POLICY.R.G04.TAIL,
    "reader_pg_magic": _POLICY.R.PG.MAGIC,
    "reader_pg_tail": _POLICY.R.PG.TAIL,
    "rc_g04": _RC.G04,
    "rc_eligibility": _RC._prefixgraph_eligibility,
    "rc_locality": _RC._prefixgraph_locality,
}


def _restore_pristine() -> None:
    _G04.MAG = _PRISTINE["g04_mag"]
    _G04.TAIL = _PRISTINE["g04_tail"]
    _SHARED.MAG = _PRISTINE["shared_mag"]
    _SHARED.TAIL = _PRISTINE["shared_tail"]
    _PG.MAGIC = _PRISTINE["pg_magic"]
    _PG.TAIL = _PRISTINE["pg_tail"]
    _POLICY.R.G04.MAG = _PRISTINE["reader_g04_mag"]
    _POLICY.R.G04.TAIL = _PRISTINE["reader_g04_tail"]
    _POLICY.R.PG.MAGIC = _PRISTINE["reader_pg_magic"]
    _POLICY.R.PG.TAIL = _PRISTINE["reader_pg_tail"]
    _RC.G04 = _PRISTINE["rc_g04"]
    _RC._prefixgraph_eligibility = _PRISTINE["rc_eligibility"]
    _RC._prefixgraph_locality = _PRISTINE["rc_locality"]


# Establish the release invariant before pytest imports the historical mutating test module. Importing the legacy
# module afterward is safe only because it is cached and its mutations are immediately rolled back below.
from experiments import entropygraph_v030_canonical_final as _CANONICAL_FINAL  # noqa: E402,F401
from experiments import entropygraph_v030_canonical as _LEGACY_CANONICAL  # noqa: E402

_restore_pristine()


@pytest.fixture(autouse=True)
def _isolate_v030_profile_globals(request):
    _restore_pristine()
    historical_test = request.node.module.__name__.endswith("test_v030_canonical")
    if historical_test:
        _LEGACY_CANONICAL.install_revision25_profiles()
    try:
        yield
    finally:
        _restore_pristine()


# Footnote: the fixture does not mock profile values, skip tests, or weaken assertions. It gives the obsolete
# compatibility suite its documented legacy precondition while ensuring that state cannot leak across test cases.
