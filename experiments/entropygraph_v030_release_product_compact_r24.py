"""One-shot v0.30 product candidate for the measured compact r24 fallback policy.

This module deliberately changes only the two release-r24 policy owners isolated by PR #208:

* restore the mature 64 KiB exact-Deflate reuse floor; and
* remove release-only medium-binary S_PACK admission.

The 256 KiB micro-pack ceiling, wide-single-file policy, r25 path, reader grammar, selectors,
comparators, release thresholds, dead-dictionary elision, and final verification remain inherited
from the promoted release product.  The medium-binary terminal shortcut is disabled as part of this
candidate because its evidence depended on the packing policy being removed; silently retaining that
shortcut with different bytes would exceed the experiment's evidence envelope.

This is a bounded product candidate, not release authority.  It exists to run the complete unchanged
release matrix once.  Promotion requires zero deterministic byte regressions plus all inherited
runtime/RSS/locality/native/recovery/platform gates.
"""
from __future__ import annotations

from experiments import entropygraph_v030_release_product as _PRODUCT

_BASE = _PRODUCT._BASE_IMPL

# PR #208 isolated blanket exact-stream retention as the dominant incremental-backups byte owner.
# Restore the mature floor rather than inventing a new corpus-tuned threshold.
_BASE.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES = 64 * 1024

# The residual decomposition then isolated release-only `.bin` S_PACK admission as the remaining
# +~19.6 KiB owner while the 256 KiB micro-pack ceiling itself was neutral/helpful.  Keep the mature
# TEXT_EXT view for every thread; wide-single-file chunking remains independently controlled by the
# existing thread-local CDC dispatcher.
def _compact_contains(self, item) -> bool:
    return item in _BASE._R24_ORIGINAL_TEXT_EXT


def _compact_iter(self):
    return iter(sorted(_BASE._R24_ORIGINAL_TEXT_EXT))


def _compact_len(self) -> int:
    return len(_BASE._R24_ORIGINAL_TEXT_EXT)


_BASE._ReleaseTextHints.__contains__ = _compact_contains
_BASE._ReleaseTextHints.__iter__ = _compact_iter
_BASE._ReleaseTextHints.__len__ = _compact_len

# The medium-binary terminal was earned with the now-removed packing policy.  Fail closed instead of
# claiming that its old byte/runtime proof transfers to a different r24 representation.
def _no_medium_terminal(root, out):
    return None


_BASE._build_medium_binary_terminal_if_eligible = _no_medium_terminal
_PRODUCT._build_medium_binary_terminal_if_eligible = _no_medium_terminal

# Re-export the promoted product after applying the two narrowly justified encoder-policy changes.
# Functions retain their original globals in `_PRODUCT`, so callers of this module exercise the real
# product boundary rather than a copied implementation.
for _name in dir(_PRODUCT):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_PRODUCT, _name)

# Preserve an explicit machine-readable identity for receipts/introspection.
PRODUCT_CANDIDATE = "v030-compact-r24-release-policy-v1"
R24_COMPACT_DEFLATE_REUSE_MIN_BYTES = 64 * 1024
R24_COMPACT_MEDIUM_BINARY_PACKING = False
R24_COMPACT_MEDIUM_TERMINAL = False
