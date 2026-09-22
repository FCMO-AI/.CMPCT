from __future__ import annotations

"""Superseding r24 streaming-finalize ownership probe.

V2 already removes raw/Deflate payload lifetime and streams completed records.  This module changes one later
ownership fact only: after ``_encode_candidate`` has finished and the caller already holds the exact Candidate
object needed to compute its immutable record ingredients, remove that consumed object from ``Builder.cands``.
The inherited v2 encode closure still computes raw length/CRC and clears payload fields from its local Candidate
reference before returning, so archive bytes and policy remain owned by the exact v2 semantic implementation.
"""

from experiments import entropygraph_v030_r24_streaming_finalize as V2


class ConsumedCandidateEvictingStreamingFinalizeBuilder(V2.StreamingFinalizeBuilder):
    """V2 streaming finalizer with immediate post-encode Candidate-map eviction."""

    def _encode_candidate(self, content_hash, candidate):
        result = super()._encode_candidate(content_hash, candidate)
        # At this boundary codec competition is complete. The v2 caller retains ``candidate`` locally long enough
        # to capture raw length/CRC and clear raw/Deflate state; all later archive reference resolution is through
        # its independent href map. Fail closed if ownership drift means the dictionary no longer contains the
        # exact object we were asked to encode.
        if self.cands.get(content_hash) is not candidate:
            raise RuntimeError("streaming v3 consumed-candidate ownership drift")
        del self.cands[content_hash]
        return result


CONTROL_CLASS = V2.StreamingFinalizeBuilder
EVICT_CLASS = ConsumedCandidateEvictingStreamingFinalizeBuilder
SPOOL_MEMORY_BYTES = V2.SPOOL_MEMORY_BYTES
MAX_IN_FLIGHT_FACTOR = V2.MAX_IN_FLIGHT_FACTOR

PROMOTION_BOUNDARY = {
    "archive_bytes_changed": False,
    "grammar_changed": False,
    "codec_policy_changed": False,
    "selector_changed": False,
    "release_credit": False,
    "single_intervention": "evict consumed Candidate shell from Builder.cands after encode completion",
    "next_gate": "same-run shipping/control/evict exact-output RSS and wall-time oracle",
}
