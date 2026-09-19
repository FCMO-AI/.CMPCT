from __future__ import annotations

"""Fresh-process runtime worker for the canonical v0.30 release product surface.

Timed pack/verify/extract operations remain engine-native. The v0.30 side reports the canonical product
user-tree identity; the accepted v0.29 comparison side remains the frozen CMPNX research baseline used by this
historical runtime gate and therefore must be verified by its own reader rather than being misclassified as r24.
Canonical r24-vs-r25 product parity is a separate release gate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil
import time


def _engine(name: str):
    if name == "v029":
        from experiments import entropygraph_v029_release as engine
    elif name == "v030":
        from experiments import entropygraph_v030_release_product as engine
    else:  # pragma: no cover
        raise ValueError(name)
    return engine


def _product_identity_engine():
    from experiments import entropygraph_v030_release_product as product

    return product


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _require_product_member_surface(engine, *, require_stats: bool = True) -> None:
    required = ["read_member", "list_members"]
    if require_stats:
        required.append("read_member_with_stats")
    missing = [name for name in required if not callable(getattr(engine, name, None))]
    if missing:
        raise RuntimeError("canonical product member surface unavailable: " + ", ".join(missing))


def _observed_product_member(engine, archive: Path, member: str) -> tuple[bytes, dict]:
    """Call the public product member operation and retain truthful operation-derived locality.

    Revision 25 exposes decoded-context accounting directly from the canonical operation. Revision 24 predates
    that API, so this one-shot benchmark process instruments the exact mature ``CMPCT`` object used by the public
    release facade and counts the uncompressed blob contexts actually touched by ``read``.

    Footnote: the instrumentation never substitutes a build declaration or a missing-value default. If the public
    operation cannot expose what it decoded, final release evidence fails instead of quietly reporting 0.0x/1.0x.
    """
    magic = Path(archive).read_bytes()[:8]
    _require_product_member_surface(engine, require_stats=magic != engine.R24_MAGIC)

    if magic != engine.R24_MAGIC:
        raw, direct = engine.read_member_with_stats(archive, member)
        stats = dict(direct)
        amp = stats.get("decoded_context_amplification")
        decoded = stats.get("decoded_context_bytes")
        if amp is None or decoded is None:
            raise RuntimeError("revision-25 product member operation omitted locality accounting")
        amp = float(amp)
        if amp <= 0:
            raise RuntimeError(f"revision-25 member operation returned invalid locality amplification: {amp}")
        stats["max_member_read_amplification"] = amp
        stats["locality_observed_from_actual_product_operation"] = True
        return bytes(raw), stats

    original_r24 = engine.CMPCT
    observations: list[dict] = []

    class TrackingR24(original_r24):
        def __init__(self, path):
            super().__init__(path)
            self._observed_blob_ids: set[int] = set()

        def _blob(self, idx):
            self._observed_blob_ids.add(int(idx))
            return super()._blob(idx)

        def close(self):
            if getattr(self, "blobs", None) is not None:
                decoded = sum(int(self.blobs[idx][1]) for idx in self._observed_blob_ids)
                observations.append(
                    {
                        "representation": "canonical-r24",
                        "decoded_context_bytes": decoded,
                        "decoded_blob_count": len(self._observed_blob_ids),
                    }
                )
            super().close()

    engine.CMPCT = TrackingR24
    try:
        raw = bytes(engine.read_member(archive, member))
    finally:
        engine.CMPCT = original_r24

    if len(observations) != 1:
        raise RuntimeError(f"r24 product member operation produced ambiguous locality observations: {observations!r}")
    stats = dict(observations[0])
    logical = len(raw)
    decoded = int(stats["decoded_context_bytes"])
    stats["logical_bytes"] = logical
    stats["max_member_read_amplification"] = max(logical, decoded) / max(1, logical)
    stats["locality_observed_from_actual_product_operation"] = True
    return raw, stats


def _tree_for_source(engine_name: str, engine, product, source: Path) -> str:
    """Return the identity domain owned by the measured side of the paired gate.

    v0.29 emits experimental CMPNX bytes, not canonical r24. Feeding those bytes to the v0.30 product facade is
    both semantically wrong and guaranteed to fail closed as ``research-only``. Keep the historical baseline in
    its frozen identity domain; v0.30 stays in the canonical product domain. The parent gate already requires
    each side to match the accepted source identity and separately enforces genuine r24-vs-r25 product parity.
    """
    return product.treehash(source) if engine_name == "v030" else engine.treehash(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("v029", "v030"), required=True)
    parser.add_argument("--op", choices=("pack", "verify", "extract", "members", "member"), required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--member")
    args = parser.parse_args()

    engine = _engine(args.engine)
    product = _product_identity_engine()
    started = time.perf_counter()

    if args.op == "pack":
        if args.source is None:
            raise SystemExit("--source required for pack")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        stats = engine.build(args.source, args.archive)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        result = {
            "engine": args.engine,
            "op": args.op,
            "archive_bytes": args.archive.stat().st_size,
            "tree_sha256": _tree_for_source(args.engine, engine, product, args.source),
            "build_stats": stats,
        }
    elif args.op == "verify":
        verified = engine.strong_verify(args.archive)
        if not verified.get("ok"):
            raise RuntimeError(f"{args.engine} strong verification failed: {verified!r}")
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        if args.engine == "v030":
            canonical_verified = verified
            tree_sha = canonical_verified.get("tree_sha256")
        else:
            # v0.29's accepted release-performance comparator is intentionally CMPNX research evidence. It is
            # not legal input to the canonical r24/r25 dispatcher, whose correct behavior is to reject it.
            canonical_verified = None
            tree_sha = verified.get("tree_sha256")
        result = {
            "engine": args.engine,
            "op": args.op,
            "tree_sha256": tree_sha,
            "engine_tree_sha256": verified.get("tree_sha256"),
            "verify": verified,
            "canonical_product_verify": canonical_verified,
        }
    elif args.op == "extract":
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        engine.extract(args.archive, args.destination)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        result = {
            "engine": args.engine,
            "op": args.op,
            "tree_sha256": _tree_for_source(args.engine, engine, product, args.destination),
        }
    elif args.op == "members":
        if args.engine != "v030":
            raise SystemExit("canonical product member listing is a v0.30 operation")
        _require_product_member_surface(engine, require_stats=False)
        members = engine.list_members(args.archive)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        result = {"engine": args.engine, "op": args.op, "members": members}
    else:
        if args.engine != "v030":
            raise SystemExit("canonical product selective-member operation is a v0.30 operation")
        if not args.member:
            raise SystemExit("--member required for member operation")
        raw, stats = _observed_product_member(engine, args.archive, args.member)
        operation_wall_s = time.perf_counter() - started
        operation_peak_rss_kib = _rss_kib()
        result = {
            "engine": args.engine,
            "op": args.op,
            "member": args.member,
            "member_bytes": len(raw),
            "member_sha256": hashlib.sha256(raw).hexdigest(),
            "member_stats": stats,
        }

    result["wall_s"] = operation_wall_s
    result["peak_rss_kib"] = operation_peak_rss_kib
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
