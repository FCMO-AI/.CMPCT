"""CMPCT experimental archive engine.

The package version follows the current on-disk prototype revision. The repository, not the
version string, is the canonical source of truth until the 1.0 format is frozen.
"""
__version__ = "0.24.0"

# Encoder-only v0.30 release guards. They are inert for ordinary/historical Builder instances and
# activate only under the promoted release-owned r24-v4 policy. Keeping installation here makes every
# import order deterministic: release code cannot accidentally miss locality enforcement or operation-
# scoped worker-policy transport.
from . import v030_release_locality as _v030_release_locality  # noqa: E402,F401
from . import v030_worker_policy_capture as _v030_worker_policy_capture  # noqa: E402,F401
