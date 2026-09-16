"""Operation-scoped transport for v0.30 r24 dictionary eligibility.

The promoted r24-v4 release policy makes ``.bin`` dictionary eligibility dynamic and thread-local.
Dictionary training runs in the build thread, while candidate encoding may run in worker threads.  A
worker must not re-decide a policy that the build thread already decided under a different thread-local
context: doing so made four-worker and one-worker builds produce different bytes.

This encoder-only hook captures *which content hashes are dictionary-eligible* immediately after
training, while the release policy owner is active.  If an encoder worker cannot see the same dynamic
text hint, a private Candidate view gains one stable historical text hint solely for the existing codec
audition.  Candidate bytes, stored metadata and source hints are not mutated.  Ordinary/historical
Builder calls are inert.

The causal evidence and frozen repair contract live in:
- docs/v030-rnd/R25_R24_WORKER_POLICY_PROPAGATION_V2_RESULT.md
- docs/v030-rnd/R25_R24_OPERATION_SCOPED_DICT_POLICY_REPAIR_PREREG.md
"""
from __future__ import annotations

from . import builder as B

_RELEASE_TEXT_HINT_TYPE = "_ReleaseTextHints"
_RELEASE_MEDIUM_BINARY_EXT = ".bin"
# Capture a stable historical text hint before release code can replace TEXT_EXT with its dynamic proxy.
_STABLE_TEXT_HINT = sorted(B.TEXT_EXT)[0]
_ORIGINAL_TRAIN_DICTIONARY = B.Builder._train_dictionary
_ORIGINAL_ENCODE_CANDIDATE = B.Builder._encode_candidate


def _capture_dictionary_policy(self: B.Builder):
    result = _ORIGINAL_TRAIN_DICTIONARY(self)
    active_release_policy = (
        type(B.TEXT_EXT).__name__ == _RELEASE_TEXT_HINT_TYPE
        and _RELEASE_MEDIUM_BINARY_EXT in B.TEXT_EXT
    )
    if active_release_policy and self.dictionary:
        self._cmpct_v030_dictionary_eligible_hashes = frozenset(
            h for h, candidate in self.cands.items()
            if any(hint in B.TEXT_EXT for hint in candidate.hints)
        )
    else:
        self._cmpct_v030_dictionary_eligible_hashes = None
    return result


def _encode_with_captured_policy(self: B.Builder, h: bytes, candidate: B.Candidate):
    eligible = getattr(self, "_cmpct_v030_dictionary_eligible_hashes", None)
    if eligible is not None and h in eligible and not any(hint in B.TEXT_EXT for hint in candidate.hints):
        # Hints are encoder evidence only and are not serialized.  This private view makes the existing
        # audition observe the parent-thread decision without mutating the shared Candidate or TEXT_EXT.
        proxy = B.Candidate(candidate.raw, set(candidate.hints) | {_STABLE_TEXT_HINT}, candidate.deflates)
        return _ORIGINAL_ENCODE_CANDIDATE(self, h, proxy)
    return _ORIGINAL_ENCODE_CANDIDATE(self, h, candidate)


def install() -> None:
    if getattr(B.Builder, "_cmpct_v030_worker_policy_capture_installed", False):
        return
    B.Builder._train_dictionary = _capture_dictionary_policy
    B.Builder._encode_candidate = _encode_with_captured_policy
    B.Builder._cmpct_v030_worker_policy_capture_installed = True


install()
