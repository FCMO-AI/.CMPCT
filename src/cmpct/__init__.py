"""CMPCT experimental archive engine.

The package version follows the current on-disk prototype revision. The repository, not the
version string, is the canonical source of truth until the 1.0 format is frozen.
"""
__version__ = "0.24.0"

# Encoder-only v0.30 release guard.  The hook is inert for ordinary/historical Builder instances and activates
# only after the promoted release product installs its thread-local r24-v4 policy.  Keeping the installation here
# makes every import order deterministic: release code cannot accidentally miss the nested-container locality law.
from . import v030_release_locality as _v030_release_locality  # noqa: E402,F401
