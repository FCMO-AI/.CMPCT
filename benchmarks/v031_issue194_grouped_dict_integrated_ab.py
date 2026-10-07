from __future__ import annotations

"""Issue #194 grouped historical-dict ownership integrated A/B.

Research only. The candidate preserves the historical dict[int, list[int]]
weak-index representation and exact COPY/LITERAL scan, changing only ownership:
candidate auditions are ordered by immutable base and one exact dict is reused
for that base. Product/format/reader/admission law is unchanged.
"""

import argparse
import builtins
import contextlib
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import queue
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from cmpct import resemblance as R
from experiments import entropygraph_v029_residual_fast as ACCEPTED
from experiments import entropygraph_v030_discovery_neutral_worker as R3
from experiments import entropygraph_v030_release as RELEASE
from experiments import entropygraph_v030_shared_portfolio as SHARED

SCHEMA = "cmpct-v031-issue194-grouped-historical-dict-integrated-ab-v1"
WORKLOADS = {
    "01_shifted_versions": HOSTILE.shifted_versions,
    "02_false_neighbors": HOSTILE.false_neighbors,
    "03_boundary_churn": HOSTILE.boundary_churn,
    "05_incompressible": HOSTILE.incompressible,
}
REPS = 2
SAMPLE_S = 0.01


class HistoricalDictEncoder:
    """One-base-at-a-time owner for the exact historical weak index."""

    def __init__(self) -> None:
        self.base: bytes | None = None
        self.block: int | None = None
        self.index: dict[int, list[int]] | None = None
        self.build_count = 0

    def _prepare(self, base: bytes, block: int, max_base_index: int) -> None:
        if block < 16:
            raise ValueError("block size too small")
        if len(base) > max_base_index:
            raise ValueError("base exceeds delta index limit")
        index: dict[int, list[int]] = {}
        for offset in range(0, len(base) - block + 1, block):
            s1, s2 = R._weak_init(base[offset:offset + block])
            index.setdefault(R._weak_key(s1, s2), []).append(offset)
        self.base = base
        self.block = block
        self.index = index
        self.build_count += 1

    def encode(
        self,
        base: bytes,
        target: bytes,
        *,
        block: int = 64,
        max_base_index: int = 8 * 1024 * 1024,
    ) -> R.DeltaResult:
        if self.base is not base or self.block != block or self.index is None:
            self._prepare(base, block, max_base_index)
        index = self.index
        if not target:
            return R.DeltaResult(b"", R.DeltaStats(0, 0, 0, 0))
        if len(base) < block or len(target) < block:
            out = bytearray([0])
            R._put_varint(out, len(target))
            out.extend(target)
            return R.DeltaResult(bytes(out), R.DeltaStats(len(target), 0, 0, 1))

        out = bytearray()
        literal = bytearray()
        copied = copy_ops = literal_ops = 0

        def flush_literal() -> None:
            nonlocal literal_ops
            if not literal:
                return
            out.append(0)
            R._put_varint(out, len(literal))
            out.extend(literal)
            literal.clear()
            literal_ops += 1

        pos = 0
        s1, s2 = R._weak_init(target[:block])
        while pos + block <= len(target):
            match_offset = -1
            for offset in index.get(R._weak_key(s1, s2), ()):
                if base[offset:offset + block] == target[pos:pos + block]:
                    match_offset = offset
                    break
            if match_offset >= 0:
                length = block
                limit = min(len(base) - match_offset, len(target) - pos)
                while length < limit and base[match_offset + length] == target[pos + length]:
                    length += 1
                flush_literal()
                out.append(1)
                R._put_varint(out, match_offset)
                R._put_varint(out, length)
                copied += length
                copy_ops += 1
                pos += length
                if pos + block <= len(target):
                    s1, s2 = R._weak_init(target[pos:pos + block])
                continue
            literal.append(target[pos])
            if pos + block < len(target):
                s1, s2 = R._weak_roll(s1, s2, target[pos], target[pos + block], block)
            pos += 1
        literal.extend(target[pos:])
        flush_literal()
        return R.DeltaResult(
            bytes(out),
            R.DeltaStats(len(target) - copied, copied, copy_ops, literal_ops),
        )


@contextlib.contextmanager
def _v028_grouped():
    owner = ACCEPTED.V028
    orig_lsh = owner.lsh_candidates
    orig_delta = owner.delta_encode
    encoder = HistoricalDictEncoder()

    def grouped_lsh(*args, **kwargs):
        rows = list(orig_lsh(*args, **kwargs))
        return sorted(rows, key=lambda e: (e.base, e.target, -e.shared_features))

    owner.lsh_candidates = grouped_lsh
    owner.delta_encode = encoder.encode
    try:
        yield encoder
    finally:
        owner.delta_encode = orig_delta
        owner.lsh_candidates = orig_lsh


@contextlib.contextmanager
def _placement_grouped():
    owner = ACCEPTED.BASE.P
    orig_delta = owner.delta_encode
    had_sorted = "sorted" in owner.__dict__
    orig_sorted = owner.__dict__.get("sorted")
    encoder = HistoricalDictEncoder()

    def grouped_sorted(iterable, *args, **kwargs):
        rows = list(iterable)
        if (
            not args
            and kwargs.get("key") is None
            and not kwargs.get("reverse", False)
            and rows
            and all(
                isinstance(row, tuple)
                and len(row) == 2
                and isinstance(row[0], tuple)
                and len(row[0]) == 2
                and all(isinstance(v, int) for v in row[0])
                for row in rows
            )
        ):
            return builtins.sorted(rows, key=lambda row: (row[0][1], row[0][0]))
        return builtins.sorted(rows, *args, **kwargs)

    owner.delta_encode = encoder.encode
    owner.sorted = grouped_sorted
    try:
        yield encoder
    finally:
        owner.delta_encode = orig_delta
        if had_sorted:
            owner.sorted = orig_sorted
        else:
            delattr(owner, "sorted")


def _cpu_s() -> float:
    a = resource.getrusage(resource.RUSAGE_SELF)
    b = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(a.ru_utime + a.ru_stime + b.ru_utime + b.ru_stime)


def _io_blocks() -> tuple[int, int]:
    a = resource.getrusage(resource.RUSAGE_SELF)
    b = resource.getrusage(resource.RUSAGE_CHILDREN)
    return int(a.ru_inblock + b.ru_inblock), int(a.ru_oublock + b.ru_oublock)


def candidate_worker(kind: str, root_s: str, out_s: str, q) -> None:
    root = Path(root_s); out = Path(out_s)
    started = time.perf_counter(); cpu0 = _cpu_s(); io0 = _io_blocks()
    pack_owner = original_choose = position_owner = original_position = None
    try:
        if kind == "v028":
            pack_owner = ACCEPTED.V028
            original_choose = R3._install_pack_cache(pack_owner)
            with _v028_grouped() as encoder:
                stats = ACCEPTED.V028.build(root, out)
                dict_build_count = encoder.build_count
        elif kind == "attempt5":
            pack_owner = ACCEPTED.BASE.P.PARENT.V028
            original_choose = R3._install_pack_cache(pack_owner)
            position_owner = ACCEPTED.BASE.P
            original_position = position_owner._position_independent_candidates
            position_owner._position_independent_candidates = R3._no_position_independent_candidates
            with _placement_grouped() as encoder:
                stats = ACCEPTED.build_graph(root, out)
                dict_build_count = encoder.build_count
        else:
            raise ValueError(kind)
        io1 = _io_blocks()
        q.put({"kind":kind,"ok":True,"elapsed_s":time.perf_counter()-started,
               "cpu_s":_cpu_s()-cpu0,"io_read_blocks":io1[0]-io0[0],"io_write_blocks":io1[1]-io0[1],
               "peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
               "dict_build_count":dict_build_count,"stats":stats})
    except BaseException as exc:
        q.put({"kind":kind,"ok":False,"error":repr(exc)})
    finally:
        if position_owner is not None and original_position is not None:
            position_owner._position_independent_candidates = original_position
        if pack_owner is not None and original_choose is not None:
            pack_owner._choose_pack_plan = original_choose


def baseline_worker(kind: str, root_s: str, out_s: str, q) -> None:
    root = Path(root_s); out = Path(out_s)
    started = time.perf_counter(); cpu0 = _cpu_s(); io0 = _io_blocks()
    pack_owner = original_choose = position_owner = original_position = None
    try:
        if kind == "v028":
            pack_owner = ACCEPTED.V028
            original_choose = R3._install_pack_cache(pack_owner)
            stats = ACCEPTED.V028.build(root, out)
        elif kind == "attempt5":
            pack_owner = ACCEPTED.BASE.P.PARENT.V028
            original_choose = R3._install_pack_cache(pack_owner)
            position_owner = ACCEPTED.BASE.P
            original_position = position_owner._position_independent_candidates
            position_owner._position_independent_candidates = R3._no_position_independent_candidates
            stats = ACCEPTED.build_graph(root, out)
        else:
            raise ValueError(kind)
        io1 = _io_blocks()
        q.put({"kind":kind,"ok":True,"elapsed_s":time.perf_counter()-started,
               "cpu_s":_cpu_s()-cpu0,"io_read_blocks":io1[0]-io0[0],"io_write_blocks":io1[1]-io0[1],
               "peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),"stats":stats})
    except BaseException as exc:
        q.put({"kind":kind,"ok":False,"error":repr(exc)})
    finally:
        if position_owner is not None and original_position is not None:
            position_owner._position_independent_candidates = original_position
        if pack_owner is not None and original_choose is not None:
            pack_owner._choose_pack_plan = original_choose


def _run_child(worker, kind: str, source: Path, out: Path) -> dict:
    ctx = mp.get_context("spawn"); q = ctx.Queue()
    p = ctx.Process(target=worker, args=(kind, str(source), str(out), q)); p.start()
    try:
        row = q.get(timeout=R3.CHILD_RESULT_TIMEOUT_S)
    except queue.Empty as exc:
        p.terminate()
        raise RuntimeError("Issue194 child did not report") from exc
    finally:
        p.join(timeout=30)
        if p.is_alive():
            p.terminate(); p.join(timeout=5)
    if p.exitcode != 0 or not row.get("ok"):
        raise RuntimeError(f"Issue194 child failure: exit={p.exitcode}, row={row!r}")
    payload = out.read_bytes()
    row["archive_bytes"] = len(payload)
    row["archive_sha256"] = hashlib.sha256(payload).hexdigest()
    return row


def _child_ab(source: Path, work: Path, kind: str) -> dict:
    rows = []
    for rep in range(REPS):
        order = ("baseline","candidate") if rep % 2 == 0 else ("candidate","baseline")
        pair = {"order": order}
        for arm in order:
            out = work / f"{kind}-{rep}-{arm}.cmpct"
            pair[arm] = _run_child(baseline_worker if arm=="baseline" else candidate_worker, kind, source, out)
        if pair["baseline"]["archive_sha256"] != pair["candidate"]["archive_sha256"]:
            raise RuntimeError(f"{kind} grouped ownership changed child archive identity")
        pair["wall_ratio"] = pair["candidate"]["elapsed_s"] / max(1e-12,pair["baseline"]["elapsed_s"])
        pair["cpu_ratio"] = pair["candidate"]["cpu_s"] / max(1e-12,pair["baseline"]["cpu_s"])
        pair["rss_ratio"] = pair["candidate"]["peak_rss_kib"] / max(1,pair["baseline"]["peak_rss_kib"])
        rows.append(pair)
    return {"kind":kind,"pairs":rows,
            "wall_ratio_median":statistics.median(r["wall_ratio"] for r in rows),
            "cpu_ratio_median":statistics.median(r["cpu_ratio"] for r in rows),
            "rss_ratio_max":max(r["rss_ratio"] for r in rows),
            "archive_identity_exact":True}


def _pid_children(pid: int) -> list[int]:
    try: raw = Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
    except OSError: return []
    return [int(x) for x in raw.split()] if raw else []


def _vmrss_kib(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"): return int(line.split()[1])
    except OSError: pass
    return 0


def _tree_rss_kib(root_pid: int) -> int:
    todo=[root_pid]; seen=set(); total=0
    while todo:
        pid=todo.pop()
        if pid in seen: continue
        seen.add(pid); total += _vmrss_kib(pid); todo.extend(_pid_children(pid))
    return total


def _product_arm(arm: str, source: Path, out: Path, result: Path) -> None:
    original = SHARED.V030_SCHED._worker
    if arm == "candidate":
        SHARED.V030_SCHED._worker = candidate_worker
    cpu0 = _cpu_s(); io0 = _io_blocks(); started = time.perf_counter()
    try:
        stats = RELEASE.build(source, out)
        build_wall_s = time.perf_counter() - started
        build_cpu_s = _cpu_s() - cpu0
        io1 = _io_blocks()
        verify = RELEASE.strong_verify(out)
    finally:
        SHARED.V030_SCHED._worker = original
    payload = out.read_bytes()
    result.write_text(json.dumps({
        "arm":arm,"wall_s":build_wall_s,"cpu_s":build_cpu_s,
        "io_read_blocks":io1[0]-io0[0],"io_write_blocks":io1[1]-io0[1],
        "archive_bytes":len(payload),"archive_sha256":hashlib.sha256(payload).hexdigest(),
        "verify":verify,"stats":stats},sort_keys=True)+"\n")


def _run_product_process(arm: str, source: Path, work: Path, tag: str) -> dict:
    out=work/f"{tag}-{arm}.cmpct"; result=work/f"{tag}-{arm}.json"
    cmd=[sys.executable,"-m","benchmarks.v031_issue194_grouped_dict_integrated_ab",
         "--product-arm",arm,"--source",str(source),"--archive",str(out),"--result",str(result)]
    p=subprocess.Popen(cmd); peak=0; samples=0
    while p.poll() is None:
        peak=max(peak,_tree_rss_kib(p.pid)); samples+=1; time.sleep(SAMPLE_S)
    if p.returncode != 0: raise RuntimeError(f"product arm failed: {arm}, rc={p.returncode}")
    row=json.loads(result.read_text()); row["whole_tree_peak_rss_kib"]=peak; row["rss_samples"]=samples
    return row


def _product_ab(source: Path, work: Path) -> dict:
    rows=[]
    for rep in range(REPS):
        order=("baseline","candidate") if rep%2==0 else ("candidate","baseline")
        pair={"order":order}
        for arm in order: pair[arm]=_run_product_process(arm,source,work,f"product-{rep}")
        if pair["baseline"]["archive_sha256"] != pair["candidate"]["archive_sha256"]:
            raise RuntimeError("grouped ownership changed final product archive identity")
        if pair["baseline"]["verify"].get("tree_sha256") != pair["candidate"]["verify"].get("tree_sha256"):
            raise RuntimeError("grouped ownership changed final verified tree identity")
        pair["wall_ratio"]=pair["candidate"]["wall_s"]/max(1e-12,pair["baseline"]["wall_s"])
        pair["cpu_ratio"]=pair["candidate"]["cpu_s"]/max(1e-12,pair["baseline"]["cpu_s"])
        pair["rss_ratio"]=pair["candidate"]["whole_tree_peak_rss_kib"]/max(1,pair["baseline"]["whole_tree_peak_rss_kib"])
        rows.append(pair)
    return {"pairs":rows,
            "wall_ratio_median":statistics.median(r["wall_ratio"] for r in rows),
            "cpu_ratio_median":statistics.median(r["cpu_ratio"] for r in rows),
            "rss_ratio_max":max(r["rss_ratio"] for r in rows),
            "final_archive_identity_exact":True}


def _source(work: Path, name: str) -> Path:
    root=work/"corpus"; root.mkdir(parents=True,exist_ok=True); WORKLOADS[name](root); return root/name


def run(work: Path, *, product: bool) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    rows=[]
    for name in WORKLOADS:
        row_work=work/name; row_work.mkdir(); source=_source(row_work,name)
        child={kind:_child_ab(source,row_work,kind) for kind in ("v028","attempt5")}
        product_row=_product_ab(source,row_work) if product else None
        rows.append({"name":name,"tree_sha256":HOSTILE.tree_hash(source),"child":child,"product":product_row})
    exact=all(child["archive_identity_exact"] for row in rows for child in row["child"].values()) and all(
        row["product"] is None or row["product"]["final_archive_identity_exact"] for row in rows)
    by_name={row["name"]:row for row in rows}
    structured=[by_name[n]["child"][k]["wall_ratio_median"] for n in ("01_shifted_versions","03_boundary_churn") for k in ("v028","attempt5")]
    false_neighbor_max=max(by_name["02_false_neighbors"]["child"][k]["wall_ratio_median"] for k in ("v028","attempt5"))
    rss_max=max(row["child"][k]["rss_ratio_max"] for row in rows for k in ("v028","attempt5"))
    passed_child=exact and min(structured)<=0.90 and false_neighbor_max<=1.05 and rss_max<=1.10
    return {"schema":SCHEMA,
            "prereg":"historical grouped-dict preregistration bound by docs/v031-coordination/2026-10-04-issue194-source-stat-falsifier.json",
            "source_reconciliation":"docs/v031-coordination/2026-10-04-issue194-source-stat-falsifier.json",
            "rows":rows,"exact_identity":exact,"passed_child_gate":passed_child,
            "decision":"ADVANCE_OR_NARROW_FROM_PRODUCT_AB" if passed_child and product else "ADVANCE_TO_PRODUCT_AB" if passed_child else "RETIRE_OR_NARROW_GROUPED_DICT_OWNERSHIP",
            "claim_boundary":"Research execution-ownership evidence only; no format/reader/admission/release change.",
            "product_credit":False,"release_credit":False}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v031-issue194-grouped-dict"))
    p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v031-issue194-grouped-dict.json"))
    p.add_argument("--product",action="store_true")
    p.add_argument("--product-arm",choices=("baseline","candidate"))
    p.add_argument("--source",type=Path); p.add_argument("--archive",type=Path); p.add_argument("--result",type=Path)
    args=p.parse_args()
    if args.product_arm:
        if args.source is None or args.archive is None or args.result is None:
            raise SystemExit("--product-arm requires --source --archive --result")
        _product_arm(args.product_arm,args.source,args.archive,args.result); return
    result=run(args.work_root,product=args.product)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result["passed_child_gate"]:
        raise SystemExit("Issue194 grouped historical-dict child gate failed")


if __name__ == "__main__":
    main()
