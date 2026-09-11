from __future__ import annotations

"""Causal falsifier for inverting the exact NPY/NPZ ownership boundary.

Instead of storing the exact NPZ as the physical owner and deriving external `features.npy` by
inflating its solid member, this experiment stores the external NPY through the ordinary v0.30
product and reconstructs the original NPZ by regenerating the exact raw-DEFLATE member stream under
the already-existing revision-24 virtual-ZIP stream-mode-2 semantics.

This is a research wrapper only. It does not add a format opcode or modify the shipping selector.
The question is whether the existing semantic can preserve the dual-owner density breakthrough while
moving the external NPY back onto an ordinary product representation with inherited read/locality
machinery.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import struct
import tempfile
import time
import zlib
import zipfile

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.codec import deflate_level_for

SCHEMA = "cmpct-v030-r4-npz-mode2-owner-inversion-v1"
ACCEPTED_V029_ANALYTICS = 6_135_172
GROUP_ROWS = I.GROUP_ROWS
MAGIC = b"R4M2\0\0\0\0"
LFH_FIXED = 30


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _cpu() -> tuple[float, float]:
    me = resource.getrusage(resource.RUSAGE_SELF); ch = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(me.ru_utime + me.ru_stime), float(ch.ru_utime + ch.ru_stime)


def _delta(a: tuple[float,float], b: tuple[float,float]) -> dict:
    s=a[0]-b[0]; c=a[1]-b[1]; return {"self_cpu_s":s,"children_cpu_s":c,"tree_cpu_s":s+c}


def _feature_stream(npz: Path, member: str) -> dict:
    raw = npz.read_bytes()
    with zipfile.ZipFile(npz, "r") as zf:
        info = zf.getinfo(member)
        source = zf.read(member)
    nl, xl = struct.unpack_from("<HH", raw, info.header_offset + 26)
    start = info.header_offset + LFH_FIXED + nl + xl
    end = start + info.compress_size
    stream = raw[start:end]
    if len(stream) != info.compress_size:
        raise RuntimeError("compressed stream framing mismatch")
    level = deflate_level_for(source, stream)
    return {"raw": raw, "source": source, "stream": stream, "start": start, "end": end,
            "level": level, "info": info}


def _regen(raw: bytes, level: int) -> bytes:
    co=zlib.compressobj(int(level), zlib.DEFLATED, -15)
    return co.compress(raw)+co.flush()


def _write_bundle(out: Path, base: Path, tcol: bytes, npy_archive: Path, prefix: bytes, suffix: bytes, manifest: dict) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(base, out/"base.cmpct")
    shutil.copy2(npy_archive, out/"npy.cmpct")
    (out/"owner.tcol").write_bytes(tcol)
    (out/"npz.prefix").write_bytes(prefix); (out/"npz.suffix").write_bytes(suffix)
    mraw=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode(); (out/"manifest.json").write_bytes(mraw)
    pieces=[mraw,(out/"base.cmpct").read_bytes(),(out/"npy.cmpct").read_bytes(),tcol,prefix,suffix]
    auth=MAGIC+b"".join(hashlib.sha256(x).digest() for x in pieces); (out/"auth.bin").write_bytes(auth)
    sizes={p.name:p.stat().st_size for p in out.iterdir() if p.is_file()}
    return {"component_bytes":sizes,"stored_bytes":sum(sizes.values())}


def _build(source: Path, out: Path, work: Path) -> dict:
    tabd=I._discover(source)
    if len(tabd["accepted"])!=1: raise RuntimeError("expected exactly one tabular relation")
    tab=tabd["accepted"][0]
    npzd=DUAL._npz_relation(source); rel=npzd["accepted"]
    csvp=source/tab["csv_path"]; jsonp=source/tab["jsonl_path"]; npyp=source/rel["npy_path"]; npzp=source/rel["npz_path"]
    fields, csv_rows=OWNER._parse_csv(csvp.read_bytes()); jfields, json_rows=OWNER._parse_jsonl(jsonp.read_bytes())
    if fields!=jfields or not OWNER._semantic_equal(fields,csv_rows,json_rows): raise RuntimeError("tabular relation failed")
    tcol,_=FAST._encode(fields,json_rows,GROUP_ROWS,FAST._line_lengths(csvp.read_bytes(),len(json_rows),GROUP_ROWS,header=True),FAST._line_lengths(jsonp.read_bytes(),len(json_rows),GROUP_ROWS,header=False))
    if I._owner_raw(tcol)!=(csvp.read_bytes(),jsonp.read_bytes()): raise RuntimeError("tabular reconstruction mismatch")

    fs=_feature_stream(npzp,rel["member"])
    if fs["source"]!=npyp.read_bytes(): raise RuntimeError("NPZ member != external NPY")
    if fs["level"] is None: raise RuntimeError("feature Deflate stream is not mode-2 reproducible")
    regenerated=_regen(fs["source"],fs["level"])
    if regenerated!=fs["stream"]: raise RuntimeError("mode-2 stream mismatch")
    prefix=fs["raw"][:fs["start"]]; suffix=fs["raw"][fs["end"]:]
    if prefix+regenerated+suffix!=fs["raw"]: raise RuntimeError("NPZ reconstruction mismatch")

    remove={tab["csv_path"],tab["jsonl_path"],rel["npy_path"],rel["npz_path"]}
    stripped=work/"stripped"; I._copy_without(source,stripped,remove)
    base=work/"base.cmpct"; PRODUCT.build(stripped,base)

    npydir=work/"npy-source"; npydir.mkdir(parents=True); shutil.copy2(npyp,npydir/npyp.name)
    npya=work/"npy.cmpct"; b0=_cpu(); w0=time.perf_counter(); npy_stats=dict(PRODUCT.build(npydir,npya)); npy_wall=time.perf_counter()-w0; npy_cpu=_delta(_cpu(),b0)
    sv=dict(PRODUCT.strong_verify(npya));
    if sv.get("ok") is False: raise RuntimeError("NPY owner strong verify failed")

    manifest={"schema":"cmpct-v030-r4-npz-mode2-owner-inversion-bundle-v1","mode2_level":int(fs["level"]),"member":rel["member"],
              "members":{"csv":{"path":tab["csv_path"],"sha256":_sha(csvp.read_bytes()),**I._stat_record(csvp)},"jsonl":{"path":tab["jsonl_path"],"sha256":_sha(jsonp.read_bytes()),**I._stat_record(jsonp)},"npy":{"path":rel["npy_path"],"sha256":_sha(npyp.read_bytes()),**I._stat_record(npyp)},"npz":{"path":rel["npz_path"],"sha256":_sha(fs["raw"]),**I._stat_record(npzp)}},
              "npz_feature_stream_bytes":len(fs["stream"]),"npz_prefix_bytes":len(prefix),"npz_suffix_bytes":len(suffix)}
    bundle=_write_bundle(out,base,tcol,npya,prefix,suffix,manifest)
    return {"stored_bytes":bundle["stored_bytes"],"bundle":bundle,"mode2_level":fs["level"],"feature_stream_bytes":len(fs["stream"]),"npz_nonfeature_bytes":len(prefix)+len(suffix),"npy_owner_stats":npy_stats,"npy_owner_create_wall_s":npy_wall,"npy_owner_create_cpu":npy_cpu}


def _extract(bundle: Path, out: Path) -> dict:
    mraw=(bundle/"manifest.json").read_bytes(); m=json.loads(mraw)
    pieces=[mraw,(bundle/"base.cmpct").read_bytes(),(bundle/"npy.cmpct").read_bytes(),(bundle/"owner.tcol").read_bytes(),(bundle/"npz.prefix").read_bytes(),(bundle/"npz.suffix").read_bytes()]
    if (bundle/"auth.bin").read_bytes()!=MAGIC+b"".join(hashlib.sha256(x).digest() for x in pieces): raise RuntimeError("bundle auth failed")
    PRODUCT.extract(bundle/"base.cmpct",out)
    csv_raw,json_raw=I._owner_raw((bundle/"owner.tcol").read_bytes())
    with tempfile.TemporaryDirectory(prefix="r4-m2-npy-") as td:
        td=Path(td); PRODUCT.extract(bundle/"npy.cmpct",td); npy_raw=(td/Path(m["members"]["npy"]["path"]).name).read_bytes()
    npz_raw=(bundle/"npz.prefix").read_bytes()+_regen(npy_raw,m["mode2_level"])+(bundle/"npz.suffix").read_bytes()
    payloads={"csv":csv_raw,"jsonl":json_raw,"npy":npy_raw,"npz":npz_raw}
    for kind,raw in payloads.items():
        meta=m["members"][kind]
        if _sha(raw)!=meta["sha256"]: raise RuntimeError(f"{kind} hash mismatch")
        p=out/meta["path"]; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(raw); os.chmod(p,int(meta["mode"])); os.utime(p,ns=(int(meta["mtime_ns"]),int(meta["mtime_ns"])))
    return {"tree_sha256":PRODUCT.treehash(out),"base_strong_verify":dict(PRODUCT.strong_verify(bundle/"base.cmpct")),"npy_strong_verify":dict(PRODUCT.strong_verify(bundle/"npy.cmpct"))}


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_m2_neutral"); repair=V029._load(V029.REPAIR_PATH,"r4_m2_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"04_analytics_and_database"; expected=PRODUCT.treehash(source)
    baseline=work/"baseline.cmpct"; b0=_cpu(); w0=time.perf_counter(); PRODUCT.build(source,baseline); baseline_wall=time.perf_counter()-w0; baseline_cpu=_delta(_cpu(),b0)
    cand=work/"candidate"; b0=_cpu(); w0=time.perf_counter(); cs=_build(source,cand,work/"candidate-work"); cand_wall=time.perf_counter()-w0; cand_cpu=_delta(_cpu(),b0)
    verify=_extract(cand,work/"extract")
    if verify["tree_sha256"]!=expected: raise RuntimeError("candidate tree mismatch")
    result={"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"tree_sha256":expected,"baseline_v030_bytes":baseline.stat().st_size,"candidate_bytes":cs["stored_bytes"],"accepted_v029_bytes":ACCEPTED_V029_ANALYTICS,
            "saving_vs_v030_bytes":baseline.stat().st_size-cs["stored_bytes"],"margin_vs_v029_bytes":ACCEPTED_V029_ANALYTICS-cs["stored_bytes"],"baseline_create_wall_s":baseline_wall,"baseline_create_cpu":baseline_cpu,"candidate_create_wall_s":cand_wall,"candidate_create_cpu":cand_cpu,"candidate":cs,"verify":verify,
            "hypothesis":{"mode2_exact_stream_reproducible":True,"owner_inversion_beats_v030":cs["stored_bytes"]<baseline.stat().st_size,"owner_inversion_beats_v029":cs["stored_bytes"]<ACCEPTED_V029_ANALYTICS},
            "contract":{"diagnostic_only":True,"release_credit":False,"existing_v24_mode2_semantics_only":True,"same_semantic_tree_verified":True,"no_locality_claim_for_reconstructed_npz":True,"no_threshold_sweep":True},
            "next_if_supported":"measure external-NPY physical selective I/O and reconstructed-NPZ work; then challenge zlib-version/native reproducibility before product design","next_if_falsified":"preserve raw-NPZ dual-owner seed and continue locality rehabilitation without tuning Genesis thresholds"}
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-mode2-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-mode2.json")); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+"\n"); print(json.dumps({k:d[k] for k in ("baseline_v030_bytes","candidate_bytes","accepted_v029_bytes","saving_vs_v030_bytes","margin_vs_v029_bytes","candidate_create_wall_s","hypothesis")}|{"components":d["candidate"]["bundle"]["component_bytes"],"mode2_level":d["candidate"]["mode2_level"]},indent=2))

if __name__=="__main__": main()
