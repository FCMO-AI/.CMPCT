"""G04 explicit retained-attempt5 ownership experiment.

Unlike the first retained-intermediate oracle, this module performs no global monkeypatching. The v0.29
portfolio explicitly returns the exact attempt-5 artifact, then G04 consumes that artifact directly.
"""
from __future__ import annotations
import os, tempfile, time
from pathlib import Path
from experiments import entropygraph_v029_parallel_portfolio_handoff as HOFF
from experiments import entropygraph_v030_geometry_overlay_g04 as G04


def build(root: Path, out: Path) -> dict:
    started=time.perf_counter(); out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-g04-explicit-",dir=out.parent) as td:
        t=Path(td); base=t/"accepted-v029.cmpct"; graph=t/"attempt5-prefallback.cmpct"; overlay=t/"g04-overlay.cmpct"
        base_stats=HOFF.build_parallel_with_attempt5(root,base,graph); base_bytes=base.stat().st_size; graph_bytes=graph.stat().st_size
        source_format,_source,meta,graph_records=G04.strict._read_source_records(graph)
        users=G04.O._record_member_lengths(meta,len(graph_records)); records=[]; transforms=[]; auditions=[]
        for rid,record in enumerate(graph_records):
            chosen,transform,stats=G04._audition_record(rid,record,users[rid]); records.append(chosen); transforms.append(transform); auditions.append(stats)
        annotated=dict(meta); annotated["overlay_source_format"]=source_format
        write_stats=G04._write_overlay(annotated,records,transforms,overlay); verified=G04.strong_verify(overlay); expected=G04.O.treehash(root)
        if not verified.get("ok") or verified.get("tree_sha256") != expected: raise RuntimeError("explicit-handoff G04 verification failed")
        overlay_bytes=overlay.stat().st_size; chosen,selected=(overlay,"geometry-overlay-g04") if overlay_bytes < base_bytes else (base,"v029-fallback")
        chosen_sha=G04.H(chosen.read_bytes()); os.replace(chosen,out)
        if G04.H(out.read_bytes()) != chosen_sha: raise RuntimeError("publication changed selected bytes")
        transformed=[r for r in auditions if r.get("selected") != "none"]
        return {"selected":selected,"archive_bytes":out.stat().st_size,"v029_bytes":base_bytes,"pre_overlay_graph_bytes":graph_bytes,"overlay_bytes":overlay_bytes,
                "saving_vs_v029_bytes":base_bytes-out.stat().st_size,"tree_sha256":expected,"create_s":time.perf_counter()-started,
                "transformed_records":len(transformed),"write":write_stats,"attempt5_retention":base_stats["retained_attempt5"],
                "attempt5_graph_build_count":base_stats["attempt5_graph_build_count"],"ownership":"explicit-artifact-handoff",
                "global_monkeypatches":0,"release_credit":False}

strong_verify=G04.strong_verify
treehash=G04.treehash
