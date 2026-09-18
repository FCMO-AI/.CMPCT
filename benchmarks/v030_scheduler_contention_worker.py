from __future__ import annotations

"""Fresh-process worker for the preregistered v0.30 outer scheduler-contention oracle."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import threading
import time

from experiments import entropygraph_v030_release_candidate as RC


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def _children(pid: int) -> set[int]:
    found=set()
    task_root=Path(f"/proc/{pid}/task")
    try: tasks=list(task_root.iterdir())
    except OSError: return found
    for task in tasks:
        try:
            raw=(task/"children").read_text().strip()
        except OSError:
            continue
        for token in raw.split():
            try: found.add(int(token))
            except ValueError: pass
    return found


def _tree_pids(root: int) -> set[int]:
    seen={root}; todo=[root]
    while todo:
        pid=todo.pop()
        for child in _children(pid):
            if child not in seen:
                seen.add(child); todo.append(child)
    return seen


def _rss_kib(pid: int) -> int:
    try:
        parts=Path(f"/proc/{pid}/statm").read_text().split()
        return int(parts[1]) * int(os.sysconf("SC_PAGE_SIZE")) // 1024
    except (OSError, ValueError, IndexError):
        return 0


class ProcessTreeSampler:
    def __init__(self, interval_s: float=0.01):
        self.interval_s=interval_s
        self.peak_kib=0
        self._stop=threading.Event()
        self._thread=threading.Thread(target=self._run,name="cmpct-contention-rss",daemon=True)
    def _sample(self):
        self.peak_kib=max(self.peak_kib,sum(_rss_kib(pid) for pid in _tree_pids(os.getpid())))
    def _run(self):
        while not self._stop.is_set():
            self._sample(); self._stop.wait(self.interval_s)
        self._sample()
    def __enter__(self):
        self._thread.start(); return self
    def __exit__(self,*_):
        self._stop.set(); self._thread.join(timeout=2)


def _cpu() -> tuple[float,float]:
    me=resource.getrusage(resource.RUSAGE_SELF)
    ch=resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime+ch.ru_utime),float(me.ru_stime+ch.ru_stime)


def _verify(path: Path, expected_tree: str) -> dict:
    result=RC.strong_verify(path)
    if not result.get("ok") or result.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"candidate verification/tree mismatch: {result!r}")
    return result


def _timed(builder, source: Path, out: Path) -> dict:
    started=time.perf_counter()
    stats=builder(source,out)
    return {"wall_s":time.perf_counter()-started,"stats":stats}


def run(mode: str, source: Path, work: Path) -> dict:
    work.mkdir(parents=True,exist_ok=True)
    expected_tree=RC.treehash(source)
    cpu0=_cpu()
    with ProcessTreeSampler() as sampler:
        started=time.perf_counter()
        if mode=="concurrent":
            g04=work/"g04.cmpct"; pg=work/"prefixgraph.cmpct"
            with ThreadPoolExecutor(max_workers=2,thread_name_prefix="cmpct-contention-oracle") as pool:
                gf=pool.submit(_timed,RC.G04.build,source,g04)
                pf=pool.submit(_timed,RC.PG.build,source,pg)
                gr=gf.result(); pr=pf.result()
            build_wall=time.perf_counter()-started
        else:
            out=work/f"{mode}.cmpct"
            builder=RC.G04.build if mode=="g04" else RC.PG.build
            only=_timed(builder,source,out)
            build_wall=time.perf_counter()-started
    cpu1=_cpu()
    common={
        "mode":mode,
        "tree_sha256":expected_tree,
        "wall_s":build_wall,
        "process_tree_peak_rss_kib":sampler.peak_kib,
        "cpu_user_s":cpu1[0]-cpu0[0],
        "cpu_system_s":cpu1[1]-cpu0[1],
        "os_cpu_count":os.cpu_count(),
    }
    if mode!="concurrent":
        path=work/f"{mode}.cmpct"; _verify(path,expected_tree)
        common.update({
            "candidate":mode,
            "candidate_wall_s":only["wall_s"],
            "archive_bytes":path.stat().st_size,
            "physical_sha256":_sha256(path),
        })
        return common

    _verify(g04,expected_tree); _verify(pg,expected_tree)
    g04_bytes=g04.stat().st_size; pg_bytes=pg.stat().st_size
    pg_locality=None; pg_admitted=False
    if pg_bytes < g04_bytes:
        pg_locality=RC._prefixgraph_locality(pg)
        pg_admitted=bool(pg_locality["passed"])
    selected="prefixgraph" if pg_admitted and pg_bytes < g04_bytes else "g04"
    selected_path=pg if selected=="prefixgraph" else g04
    common.update({
        "candidate_walls_s":{"g04":gr["wall_s"],"prefixgraph":pr["wall_s"]},
        "candidate_bytes":{"g04":g04_bytes,"prefixgraph":pg_bytes},
        "candidate_sha256":{"g04":_sha256(g04),"prefixgraph":_sha256(pg)},
        "selected":selected,
        "selected_candidate_wall_s":gr["wall_s"] if selected=="g04" else pr["wall_s"],
        "selected_bytes":selected_path.stat().st_size,
        "selected_sha256":_sha256(selected_path),
        "prefixgraph_locality":pg_locality,
        "prefixgraph_admitted":pg_admitted,
    })
    return common


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("concurrent","g04","prefixgraph"),required=True)
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--work",type=Path,required=True)
    a=ap.parse_args()
    print(json.dumps(run(a.mode,a.source,a.work),separators=(",",":"),default=str),flush=True)


if __name__=="__main__":
    main()
