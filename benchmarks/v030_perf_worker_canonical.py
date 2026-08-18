from __future__ import annotations

"""Fresh-process runtime worker for the canonical v0.30 product surface."""

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
        from experiments import entropygraph_v030_canonical as engine
    else:  # pragma: no cover
        raise ValueError(name)
    return engine


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _require_product_member_surface(engine) -> None:
    missing = [name for name in ("read_member", "list_members") if not callable(getattr(engine, name, None))]
    if missing:
        raise RuntimeError("canonical product member surface unavailable: " + ", ".join(missing))


def _observed_product_member(engine, archive: Path, member: str) -> tuple[bytes, dict]:
    """Call the public product operation while observing its actual decode context in the same process.

    The wrappers are benchmark instrumentation only. They do not select a different reader: ``engine.read_member``
    still performs the operation, but the exact session/CMPCT objects it constructs report what they decoded.
    The worker is a one-shot process, and every monkeypatch is restored in ``finally``.
    """
    _require_product_member_surface(engine)
    if not hasattr(engine, "POLICY") or not hasattr(engine, "CMPCT"):
        raise RuntimeError("canonical product internals do not expose instrumentable reader owners")

    reader_module = engine.POLICY.R
    original_g04 = reader_module._G04Session
    original_pg = reader_module._PGSession
    original_r24 = engine.CMPCT
    observations: list[dict] = []

    class TrackingG04(original_g04):
        def __init__(self, path):
            super().__init__(path)
            self._observed_decoded_record_bytes = 0

        def record(self, record_id):
            before = self.physical_record_reads
            raw = super().record(record_id)
            if self.physical_record_reads > before:
                self._observed_decoded_record_bytes += len(raw)
            return raw

        def close(self):
            observations.append(
                {
                    "representation": "g04-overlay",
                    "decoded_context_bytes": self._observed_decoded_record_bytes,
                    "declared_max_member_read_amplification": self.meta.get("max_geometry_member_read_amplification"),
                    "physical_record_reads": self.physical_record_reads,
                }
            )
            super().close()

    class TrackingPG(original_pg):
        def close(self):
            observations.append(
                {
                    "representation": "prefixgraph",
                    "observed_session_amplification": self.max_member_read_amplification,
                    "max_file_bytes": self.max_file_bytes,
                }
            )
            super().close()

    class TrackingR24(original_r24):
        def __init__(self, path):
            super().__init__(path)
            self._observed_blob_ids: set[int] = set()

        def _blob(self, idx):
            self._observed_blob_ids.add(int(idx))
            return super()._blob(idx)

        def close(self):
            decoded = sum(int(self.blobs[idx][1]) for idx in self._observed_blob_ids)
            observations.append(
                {
                    "representation": "canonical-r24",
                    "decoded_context_bytes": decoded,
                    "decoded_blob_count": len(self._observed_blob_ids),
                }
            )
            super().close()

    reader_module._G04Session = TrackingG04
    reader_module._PGSession = TrackingPG
    engine.CMPCT = TrackingR24
    try:
        raw = bytes(engine.read_member(archive, member))
    finally:
        reader_module._G04Session = original_g04
        reader_module._PGSession = original_pg
        engine.CMPCT = original_r24

    if len(observations) != 1:
        raise RuntimeError(f"canonical member operation produced ambiguous locality observations: {observations!r}")
    stats = dict(observations[0])
    logical = len(raw)
    if stats["representation"] == "prefixgraph":
        amp = stats.get("observed_session_amplification")
        if amp is None:
            raise RuntimeError("PrefixGraph product member operation omitted locality accounting")
        stats["decoded_context_bytes"] = None
        stats["max_member_read_amplification"] = float(amp)
    else:
        decoded = stats.get("decoded_context_bytes")
        if decoded is None:
            raise RuntimeError("canonical product member operation omitted decoded-context accounting")
        stats["max_member_read_amplification"] = max(logical, int(decoded)) / max(1, logical)

    declared = stats.get("declared_max_member_read_amplification")
    if declared is not None and stats["max_member_read_amplification"] > float(declared) + 1e-12:
        raise RuntimeError(
            "observed canonical member locality exceeds the archive/build declaration: "
            f"observed={stats['max_member_read_amplification']} declared={declared}"
        )
    stats["logical_bytes"] = logical
    stats["locality_observed_from_actual_product_operation"] = True
    return raw, stats


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
    started = time.perf_counter()
    if args.op == "pack":
        if args.source is None:
            raise SystemExit("--source required for pack")
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        stats = engine.build(args.source, args.archive)
        result = {
            "engine": args.engine,
            "op": args.op,
            "archive_bytes": args.archive.stat().st_size,
            "tree_sha256": engine.treehash(args.source),
            "build_stats": stats,
        }
    elif args.op == "verify":
        verified = engine.strong_verify(args.archive)
        if not verified.get("ok"):
            raise RuntimeError(f"{args.engine} strong verification failed: {verified!r}")
        result = {"engine": args.engine, "op": args.op, "tree_sha256": verified.get("tree_sha256"), "verify": verified}
    elif args.op == "extract":
        if args.destination is None:
            raise SystemExit("--destination required for extract")
        if args.destination.exists():
            shutil.rmtree(args.destination)
        engine.extract(args.archive, args.destination)
        result = {"engine": args.engine, "op": args.op, "tree_sha256": engine.treehash(args.destination)}
    elif args.op == "members":
        if args.engine != "v030":
            raise SystemExit("canonical product member listing is a v0.30 operation")
        _require_product_member_surface(engine)
        result = {"engine": args.engine, "op": args.op, "members": engine.list_members(args.archive)}
    else:
        if args.engine != "v030":
            raise SystemExit("canonical product selective-member operation is a v0.30 operation")
        if not args.member:
            raise SystemExit("--member required for member operation")
        raw, stats = _observed_product_member(engine, args.archive, args.member)
        result = {
            "engine": args.engine,
            "op": args.op,
            "member": args.member,
            "member_bytes": len(raw),
            "member_sha256": hashlib.sha256(raw).hexdigest(),
            "member_stats": stats,
        }
        # Footnote: a missing locality field is a hard error above. The benchmark never substitutes 0.0x, and
        # r24 fallback is instrumented through the same public canonical read_member operation rather than being
        # mislabeled not-applicable.

    result["wall_s"] = time.perf_counter() - started
    result["peak_rss_kib"] = _rss_kib()
    print(json.dumps(result, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
