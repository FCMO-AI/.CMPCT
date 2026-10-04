from __future__ import annotations

"""Repair wrapper for the shared front-door preflight A/B.

The v1 oracle referenced the pre-promotion internal name
``_c25cc01_source_shape``.  The shipping product now exposes the same source
shape helper as ``_compact_control_source_shape``.  This wrapper preserves the
entire v1 experiment and thresholds while rebinding only that stale diagnostic
call.  Product dispatch, selector policy, archive bytes, and release credit are
unchanged.
"""

from pathlib import Path

from benchmarks import v030_frontdoor_shared_preflight_oracle as V1
from experiments import entropygraph_v030_release_product as PRODUCT


def current_two_pass(root: Path) -> dict:
    logs = PRODUCT._logs_streaming_source_prefilter(root)
    if bool(logs["eligible"]):
        return {"logs_eligible": True, "shape": None}
    shape = PRODUCT._compact_control_source_shape(root)
    return {"logs_eligible": False, "shape": shape}


# Rebind the global used by V1.main(); all other experiment code and thresholds
# remain exactly the v1 implementation.
V1.current_two_pass = current_two_pass


if __name__ == "__main__":
    raise SystemExit(V1.main())
