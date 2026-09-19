"""Explicit-artifact variant of the accepted v0.29 parallel portfolio.

Research seam only. It preserves the accepted two-child construction and smaller-artifact tournament while
exporting the already-built attempt-5 candidate by same-filesystem hardlink before winner publication.
This removes the global-function interception used by the first G04 reuse oracle. Promotion should fold
this narrow capability into the authoritative scheduler rather than keep a duplicate scheduler.
"""
from __future__ import annotations
import multiprocessing as mp, os, queue as queue_module, tempfile, time
from pathlib import Path
from experiments import entropygraph_v029_parallel_portfolio as S


def build_parallel_with_attempt5(root: Path, out: Path, retained: Path) -> dict:
    if S.accepted._logical_file_count(root) <= 1:
        raise RuntimeError("explicit attempt5 handoff is multi-file only; preserve single-file fast reject")
    out.parent.mkdir(parents=True, exist_ok=True); retained.parent.mkdir(parents=True, exist_ok=True)
    if os.stat(out.parent).st_dev != os.stat(retained.parent).st_dev:
        raise RuntimeError("attempt5 handoff requires same filesystem; payload-copy fallback forbidden")
    if retained.exists(): raise FileExistsError(retained)
    started=time.perf_counter(); ctx=mp.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix=".cmpct-mosaic-handoff-", dir=out.parent) as td:
        t=Path(td); v028=t/"v028.cmpct"; a5=t/"attempt5.cmpct"; q=ctx.Queue()
        ps=[ctx.Process(target=S._worker,args=("v028",str(root),str(v028),q)),ctx.Process(target=S._worker,args=("attempt5",str(root),str(a5),q))]
        for p in ps: p.start()
        rows=[]
        try:
            for _ in ps: rows.append(q.get(timeout=S.CHILD_RESULT_TIMEOUT_S))
        except queue_module.Empty as exc:
            for p in ps:
                if p.is_alive(): p.terminate()
            raise RuntimeError("parallel handoff child timeout") from exc
        finally:
            for p in ps:
                p.join(timeout=30)
                if p.is_alive(): p.terminate(); p.join(timeout=5)
        if any(not r.get("ok") for r in rows) or any(p.exitcode != 0 for p in ps):
            raise RuntimeError(f"parallel handoff child failure rows={rows!r} exitcodes={[p.exitcode for p in ps]!r}")
        vb,ab=v028.stat().st_size,a5.stat().st_size
        retain_started=time.perf_counter(); os.link(a5,retained)
        # A hardlink writes no archive payload bytes, but it deliberately extends the lifetime of the existing
        # attempt-5 inode. Keep those two costs separate: zero rewrite I/O is not zero temporary disk occupancy.
        retention={"mode":"same-filesystem-hardlink","payload_write_bytes":0,"retained_disk_occupancy_bytes":ab,"bytes":ab,
                   "sha256":S._sha256(retained),"retain_s":time.perf_counter()-retain_started}
        chosen,selected=(a5,"mosaic") if ab < vb else (v028,"v028-fallback")
        durability=S._durable_replace(chosen,out); by={r["kind"]:r for r in rows}
        return {"selected":selected,"archive_bytes":out.stat().st_size,"archive_sha256":S._sha256(out),"parallel_create_s":time.perf_counter()-started,
                "v028_child_s":by["v028"]["elapsed_s"],"attempt5_child_s":by["attempt5"]["elapsed_s"],"v028_bytes":vb,"attempt5_graph_bytes":ab,
                "scheduler_mode":"parallel-independent-portfolio-explicit-handoff","selection_durability":durability,"accepted_engine":S.ACCEPTED_ENGINE,
                "retained_attempt5":retention}
