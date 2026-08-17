"""Byte-preserving parallel scheduler for the CMPNX14 Geometry IR portfolio.

CMPNX14's public build law is conservative and correct: build the accepted v0.29 fallback, build the complete
GIR candidate, then publish whichever complete artifact is smaller.  Those two encoders are causally
independent, so paying them serially is unnecessary wall-clock work.

This facade runs the accepted v0.29 build and the byte-preserving rehabilitated GIR graph build in separate
spawned processes, applies the *same* strict ``gir_bytes < v029_bytes`` selection law, and publishes the
winner with same-filesystem ``os.replace`` rather than rewriting the entire chosen archive through
``shutil.copyfile``.

Footnote: parallelism changes scheduling only.  The child encoders, compressor settings, candidate ranking,
metadata, recovery copy, fallback tie rule and resulting selected bytes are unchanged.  Promotion requires
byte-for-byte identity with the sequential rehabilitated portfolio, not merely equal archive size.
"""
from __future__ import annotations

import hashlib
import multiprocessing as mp
from pathlib import Path
import queue as queue_module
import tempfile
import time

from experiments import entropygraph_v030_gir_rehab as rehab

CHILD_RESULT_TIMEOUT_S = 30 * 60


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _worker(kind: str, root_s: str, out_s: str, queue) -> None:
    root = Path(root_s)
    out = Path(out_s)
    started = time.perf_counter()
    try:
        if kind == "v029":
            stats = rehab.gir.BASE.build(root, out)
        elif kind == "gir":
            # Footnote: importing ``rehab`` in the spawned child installs the already-audited exact-direct-
            # floor reuse before ``_build_gir`` runs.  We do not maintain a second encoder implementation.
            stats = rehab._build_gir(root, out)
        else:  # pragma: no cover - parent owns the fixed worker set
            raise ValueError(f"unknown GIR parallel worker kind: {kind}")
        queue.put({
            "kind": kind,
            "ok": True,
            "elapsed_s": time.perf_counter() - started,
            "stats": stats,
            "archive_bytes": out.stat().st_size,
            "archive_sha256": _sha256(out),
        })
    except BaseException as exc:
        # A child must report a durable failure; silent process death must never be misread as a fallback win.
        queue.put({"kind": kind, "ok": False, "elapsed_s": time.perf_counter() - started, "error": repr(exc)})


def build(root: Path, out: Path) -> dict:
    """Build both complete candidates concurrently and publish the exact sequential winner."""
    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")

    # The temporary portfolio lives beside ``out`` so winner publication is guaranteed to stay on one
    # filesystem.  ``os.replace`` can therefore transfer the already-written winner without a second payload
    # copy and remains atomic with respect to the final path on ordinary local filesystems.
    with tempfile.TemporaryDirectory(prefix=f".{out.name}.gir-parallel-", dir=out.parent) as td:
        temp = Path(td)
        v029_path = temp / "v029.cmpct"
        gir_path = temp / "gir.cmpct"
        queue = ctx.Queue()
        processes = [
            ctx.Process(target=_worker, args=("v029", str(root), str(v029_path), queue)),
            ctx.Process(target=_worker, args=("gir", str(root), str(gir_path), queue)),
        ]
        for process in processes:
            process.start()

        results: list[dict] = []
        try:
            for _ in processes:
                results.append(queue.get(timeout=CHILD_RESULT_TIMEOUT_S))
        except queue_module.Empty as exc:
            for process in processes:
                if process.is_alive():
                    process.terminate()
            raise RuntimeError("parallel GIR portfolio child failed to report before timeout") from exc
        finally:
            for process in processes:
                process.join(timeout=30)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)

        failures = [result for result in results if not result.get("ok")]
        bad_exitcodes = [process.exitcode for process in processes if process.exitcode != 0]
        if failures or bad_exitcodes:
            raise RuntimeError(
                f"parallel GIR portfolio child failure: failures={failures!r}, "
                f"exitcodes={[process.exitcode for process in processes]!r}"
            )

        by_kind = {result["kind"]: result for result in results}
        v029_bytes = int(by_kind["v029"]["archive_bytes"])
        gir_bytes = int(by_kind["gir"]["archive_bytes"])
        if gir_bytes < v029_bytes:
            chosen_path = gir_path
            selected = "gir"
        else:
            chosen_path = v029_path
            selected = "v029-fallback"

        chosen_sha = str(by_kind["gir" if selected == "gir" else "v029"]["archive_sha256"])
        # No copy: the chosen inode is transferred to the destination path.  The losing candidate remains in
        # the private temporary directory and is deleted by cleanup after publication.
        import os
        os.replace(chosen_path, out)
        if out.stat().st_size != (gir_bytes if selected == "gir" else v029_bytes) or _sha256(out) != chosen_sha:
            raise RuntimeError("parallel GIR publication changed selected artifact bytes")

        candidate_bytes = out.stat().st_size
        return {
            "selected": selected,
            "archive_bytes": candidate_bytes,
            "v029_bytes": v029_bytes,
            "gir_graph_bytes": gir_bytes,
            "saving_vs_v029_bytes": v029_bytes - candidate_bytes,
            "smaller_than_v029_pct": (v029_bytes - candidate_bytes) / max(1, v029_bytes) * 100.0,
            "portfolio_create_s": time.perf_counter() - started,
            "v029": by_kind["v029"]["stats"],
            "gir": by_kind["gir"]["stats"],
            "scheduler_mode": "parallel-independent-complete-artifacts",
            "publication_mode": "same-filesystem-os.replace",
            "v029_child_s": float(by_kind["v029"]["elapsed_s"]),
            "gir_child_s": float(by_kind["gir"]["elapsed_s"]),
            "archive_sha256": chosen_sha,
        }


strong_verify = rehab.strong_verify
extract = rehab.extract
treehash = rehab.treehash
MAX_CHUNK = rehab.MAX_CHUNK
MAX_DECODE_UNIT = rehab.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = rehab.MAX_DECODER_MEMORY

if __name__ == "__main__":
    rehab.gir._main()
