"""Bounded writer-only relation-band semantics for ONE-G0.2.

This module is a semantic/reference substrate, not a product-speed claim. The
capture object is deliberately feed-based so an encoder can collect relation
features while bytes are already passing through the fused observer. No reader
operation, codec choice, or reconstruction behavior is introduced here.
"""
from __future__ import annotations

from dataclasses import dataclass

_SHIFTS = (-2, -1, 0, 1, 2)
_QUERY_SHIFTS = (-2, -1, 1, 2)
_BAND_COUNT = 4
_PROBES_PER_BAND = 4
_MIN_RELATION_BYTES = 1024


@dataclass(frozen=True)
class RelationBandFeatures:
    relation_bytes: int
    probe_positions: tuple[int, ...]
    source_bands: tuple[bytes, ...]
    shifted_bands: tuple[tuple[int, tuple[bytes, ...]], ...]
    retained_feature_bytes: int

    def bands_for_shift(self, shift: int) -> tuple[bytes, ...]:
        if shift == 0:
            return self.source_bands
        for candidate_shift, bands in self.shifted_bands:
            if candidate_shift == shift:
                return bands
        raise ValueError("unsupported relation-band shift")


@dataclass(frozen=True)
class RelationNomination:
    target_id: int
    candidate_source_ids: tuple[int, ...]
    saturated_bucket_hits: int
    candidate_overflow: bool


@dataclass(frozen=True)
class RelationBandIndexStats:
    objects_indexed: int
    retained_source_refs: int
    saturated_buckets: int
    emitted_candidate_pairs: int


class RelationBandCapture:
    """Feed-only capture that can share an existing forward source pass.

    Exactly sixteen interior probe positions are used for relation-capable inputs.
    For each probe we retain the five neighboring bytes needed to form the zero
    view and all four bounded shift views. `feed()` must receive every source byte
    exactly once in increasing position order; this freezes deterministic resource
    semantics and prevents a hidden second discovery pass.
    """

    def __init__(self, relation_bytes: int):
        if type(relation_bytes) is not int or relation_bytes < 0:
            raise ValueError("relation_bytes must be a non-negative integer")
        self._length = relation_bytes
        self._next_position = 0
        self._enabled = relation_bytes >= _MIN_RELATION_BYTES
        self._positions = self._make_positions(relation_bytes) if self._enabled else ()
        self._values = [[None for _ in _SHIFTS] for _ in self._positions]
        wanted: dict[int, list[tuple[int, int]]] = {}
        for probe_id, p in enumerate(self._positions):
            for shift_id, shift in enumerate(_SHIFTS):
                wanted.setdefault(p + shift, []).append((probe_id, shift_id))
        self._wanted = wanted

    @staticmethod
    def _make_positions(length: int) -> tuple[int, ...]:
        positions = []
        for sample in range(_BAND_COUNT * _PROBES_PER_BAND):
            p = ((sample + 1) * length) // 17
            p = max(2, min(length - 3, p))
            positions.append(p)
        return tuple(positions)

    def feed(self, position: int, value: int) -> None:
        if type(position) is not int or position != self._next_position:
            raise ValueError("relation-band capture requires a contiguous forward pass")
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("relation-band source value must be one byte")
        if position >= self._length:
            raise ValueError("relation-band capture received bytes past declared length")
        for probe_id, shift_id in self._wanted.get(position, ()):
            self._values[probe_id][shift_id] = value
        self._next_position += 1

    def finish(self) -> RelationBandFeatures | None:
        if self._next_position != self._length:
            raise ValueError("relation-band capture ended before declared length")
        if not self._enabled:
            return None
        if any(value is None for probe in self._values for value in probe):
            raise AssertionError("internal relation-band capture is incomplete")

        by_shift: dict[int, list[int]] = {shift: [] for shift in _SHIFTS}
        for probe in self._values:
            for shift_id, shift in enumerate(_SHIFTS):
                value = probe[shift_id]
                assert value is not None
                by_shift[shift].append(value)

        def bands(values: list[int]) -> tuple[bytes, ...]:
            return tuple(
                bytes(values[start:start + _PROBES_PER_BAND])
                for start in range(0, len(values), _PROBES_PER_BAND)
            )

        source_bands = bands(by_shift[0])
        shifted = tuple((shift, bands(by_shift[shift])) for shift in _QUERY_SHIFTS)
        return RelationBandFeatures(
            relation_bytes=self._length,
            probe_positions=self._positions,
            source_bands=source_bands,
            shifted_bands=shifted,
            retained_feature_bytes=len(self._positions) * len(_SHIFTS),
        )


def capture_relation_bands(data: bytes) -> RelationBandFeatures | None:
    """Reference convenience wrapper; production fusion should call `feed()` inline."""
    if type(data) is not bytes:
        raise TypeError("relation-band input must be bytes")
    capture = RelationBandCapture(len(data))
    for position, value in enumerate(data):
        capture.feed(position, value)
    return capture.finish()


class RelationBandIndex:
    """Bounded deterministic pair nominator over relation-band features.

    Buckets that exceed `max_sources_per_signature` are marked saturated and are
    no longer used for nomination. This is intentionally fail-closed for resource
    safety: saturation may reduce compression opportunity, but can never affect
    reconstruction correctness because exact relation proof is downstream.

    Candidate overflow is surfaced explicitly instead of silently truncating the
    target's candidate set. A caller may then decline relation search for that
    target and fall back to ordinary ONE representation.
    """

    def __init__(self, *, max_sources_per_signature: int = 8, max_candidates_per_target: int = 64):
        for name, value in {
            "max_sources_per_signature": max_sources_per_signature,
            "max_candidates_per_target": max_candidates_per_target,
        }.items():
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        self._max_sources = max_sources_per_signature
        self._max_candidates = max_candidates_per_target
        self._buckets: dict[tuple[int, int, bytes], list[int] | None] = {}
        self._objects = 0
        self._retained_refs = 0
        self._saturated = 0
        self._emitted = 0

    def nominate_and_insert(self, target_id: int, features: RelationBandFeatures) -> RelationNomination:
        if type(target_id) is not int or target_id < 0:
            raise ValueError("target_id must be a non-negative integer")
        candidates: set[int] = set()
        saturated_hits = 0
        overflow = False

        for shift, bands in features.shifted_bands:
            for band_id, signature in enumerate(bands):
                key = (features.relation_bytes, band_id, signature)
                bucket = self._buckets.get(key)
                if bucket is None and key in self._buckets:
                    saturated_hits += 1
                    continue
                if bucket:
                    candidates.update(bucket)
                    if len(candidates) > self._max_candidates:
                        overflow = True
                        candidates.clear()
                        break
            if overflow:
                break

        if not overflow:
            self._emitted += len(candidates)

        for band_id, signature in enumerate(features.source_bands):
            key = (features.relation_bytes, band_id, signature)
            if key not in self._buckets:
                self._buckets[key] = [target_id]
                self._retained_refs += 1
                continue
            bucket = self._buckets[key]
            if bucket is None:
                continue
            if len(bucket) >= self._max_sources:
                self._retained_refs -= len(bucket)
                self._buckets[key] = None
                self._saturated += 1
            else:
                bucket.append(target_id)
                self._retained_refs += 1

        self._objects += 1
        return RelationNomination(
            target_id=target_id,
            candidate_source_ids=tuple(sorted(candidates)) if not overflow else (),
            saturated_bucket_hits=saturated_hits,
            candidate_overflow=overflow,
        )

    @property
    def stats(self) -> RelationBandIndexStats:
        return RelationBandIndexStats(
            objects_indexed=self._objects,
            retained_source_refs=self._retained_refs,
            saturated_buckets=self._saturated,
            emitted_candidate_pairs=self._emitted,
        )
