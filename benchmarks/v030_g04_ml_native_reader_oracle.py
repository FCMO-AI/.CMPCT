from __future__ import annotations

"""Measure the existing Rust G0-G4 reader against the canonical Python ML reader.

Research-only execution-path oracle. Native samples pass through the fail-closed product bridge and
include its compact native-info output-budget preflight. The benchmark now materializes only the frozen
ML target it actually measures, while checking the accepted historical tree hash before building; this
removes unrelated corpus-generation setup without moving any timed boundary or changing input bytes.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_native_reader_bridge as NATIVE
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20
TARGET = ("neutral_hostile_v1", "09_ml_artifacts")


def _frozen_ml_source(root: Path) -> Path:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_r42_native_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_r42_native_repair")
    repair.install_generation_hooks(neutral)
    neutral.corpus_ml(root)
    repair.normalize_root(root)
    source = root / TARGET[1]
    observed = GENERAL._historical_treehash(source)
    expected = GENERAL._accepted_v029_rows()[TARGET]["tree_sha256"]
    if observed != expected:
        raise RuntimeError(f"frozen ML source drift: {observed} != {expected}")
    return source


def _python_measure(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter(); result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _native_verify_measure(cli: Path, archive: Path) -> tuple[float, dict]:
    started = time.perf_counter(); receipt = NATIVE.verify_g04(cli, archive)
    return time.perf_counter() - started, receipt


def _native_extract_measure(cli: Path, archive: Path, destination: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = NATIVE.extract_g04(cli, archive, destination, max_output_bytes=RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, receipt


def _corrupt_first_physical_payload(source: Path, target: Path) -> None:
    shutil.copy2(source, target)
    stream, _meta, record_start, offsets, _merkle, _tail = RR._g04_open(target)
    try: first = int(record_start) + int(offsets[0])
    finally: stream.close()
    with target.open("r+b") as fh:
        fh.seek(first); header = fh.read(RR.A5.PH.size)
        if len(header) != RR.A5.PH.size: raise RuntimeError("short G0-G4 physical header")
        _codec, _usize, csize, _crc, _sha = RR.A5.PH.unpack(header)
        if int(csize) <= 0: raise RuntimeError("cannot corrupt empty G0-G4 physical payload")
        pos = first + RR.A5.PH.size + min(11, int(csize) - 1); fh.seek(pos); old = fh.read(1)
        if len(old) != 1: raise RuntimeError("short G0-G4 physical payload")
        fh.seek(pos); fh.write(bytes((old[0] ^ 0x01,)))


def run(work_root: Path, native_cli: Path) -> dict:
    if not native_cli.is_file(): raise RuntimeError(f"native CLI not found: {native_cli}")
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    source = _frozen_ml_source(work_root / "corpus")
    source_tree = PRODUCT.treehash(source); archive = work_root / "ml.cmpct"
    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG: raise RuntimeError("ML target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != source_tree: raise RuntimeError("shipping strong verification failed before native A/B")
    warm_verify=NATIVE.verify_g04(native_cli,archive); warm_info=NATIVE.info_g04(native_cli,archive)
    if not warm_verify.get("ok") or warm_verify.get("profile") != NATIVE.CANONICAL_G04_PROFILE: raise RuntimeError("native bridge warm-up did not bind canonical G0-G4")
    if warm_info.get("profile") != NATIVE.CANONICAL_G04_PROFILE or int(warm_info.get("revision",0)) != 25: raise RuntimeError("native info warm-up did not bind canonical G0-G4 revision")
    samples={"python_verify":[],"native_verify":[],"python_extract":[],"native_extract":[]}; receipts=[]
    for i in range(ROUNDS):
        for native in ((True,False) if i%2 else (False,True)):
            if native:
                s,r=_native_verify_measure(native_cli,archive); samples["native_verify"].append(float(s))
                if not r.get("ok") or r.get("profile") != NATIVE.CANONICAL_G04_PROFILE: raise RuntimeError("native bridge verification receipt drift")
                dst=work_root/f"native-extract-{i}"; shutil.rmtree(dst,ignore_errors=True); s,r=_native_extract_measure(native_cli,archive,dst); samples["native_extract"].append(float(s)); receipts.append(dict(r))
                if PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("native extraction tree identity drift")
            else:
                s,r=_python_measure(archive,None); samples["python_verify"].append(float(s))
                if not r.get("ok") or r.get("tree_sha256")!=source_tree: raise RuntimeError("Python verification identity drift")
                dst=work_root/f"python-extract-{i}"; shutil.rmtree(dst,ignore_errors=True); s,r=_python_measure(archive,dst); samples["python_extract"].append(float(s))
                if not r.get("ok") or r.get("tree_sha256")!=source_tree or PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("Python extraction identity drift")
            shutil.rmtree(dst,ignore_errors=True) if 'dst' in locals() else None
    corrupt=work_root/'ml-corrupt.cmpct'; _corrupt_first_physical_payload(archive,corrupt)
    try: NATIVE.verify_g04(native_cli,corrupt); corrupt_rejected=False
    except NATIVE.NativeReaderError: corrupt_rejected=True
    budget=all(int(r.get("declared_regular_bytes",-1))<=int(r.get("caller_max_output_bytes",-2)) and r.get("transactional_native_extract") is True and r.get("budget_preflight")=="native-info-logical-regular-bytes-v1" for r in receipts)
    med={k:float(statistics.median(v)) for k,v in samples.items()}; vi=1-med['native_verify']/max(med['python_verify'],1e-9); ei=1-med['native_extract']/max(med['python_extract'],1e-9)
    gate={"archive_bytes_unchanged":True,"canonical_tree_preserved":True,"native_corruption_rejected":corrupt_rejected,"native_caller_budget_preserved":budget,"verify_materially_faster":vi>=MIN_VERIFY_IMPROVEMENT,"extract_materially_faster":ei>=MIN_EXTRACT_IMPROVEMENT}; gate['passed']=all(gate.values())
    return {"schema":"cmpct-v030-g04-ml-native-reader-v3","target":"neutral_hostile_v1/09_ml_artifacts","shipping_build":built,"native_cli":str(native_cli),"native_bridge":"cmpct-portable-process-v2","native_extract_budget_preflight":"native-info-logical-regular-bytes-v1","native_extract_budget_preflight_timed":True,"rounds":ROUNDS,"samples_s":samples,"medians_s":med,"verify_improvement_fraction":float(vi),"extract_improvement_fraction":float(ei),"native_corruption_rejected":corrupt_rejected,"native_caller_budget_preserved":budget,"contract":{"minimum_verify_improvement_fraction":MIN_VERIFY_IMPROVEMENT,"minimum_extract_improvement_fraction":MIN_EXTRACT_IMPROVEMENT,"archive_bytes_changed":False,"grammar_changed":False,"memory_budget_changed":False,"locality_limit":8.0,"decode_unit_limit_bytes":8*1024*1024,"caller_extract_budget_enforced_before_publication":True},"gate":gate,"promotion_signal":bool(gate['passed']),"release_credit":False,"claim_boundary":"Research-only exact-frozen-input A/B through the existing fail-closed native bridge. A positive result authorizes integration work only; reader/fuzz/native/Android/runtime authority must be re-earned."}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--native-cli',type=Path,required=True); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-g04-ml-native-reader-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-g04-ml-native-reader.json')); a=p.parse_args(); result=run(a.work_root,a.native_cli); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({"medians_s":result['medians_s'],"verify_improvement_fraction":result['verify_improvement_fraction'],"extract_improvement_fraction":result['extract_improvement_fraction'],"native_corruption_rejected":result['native_corruption_rejected'],"native_caller_budget_preserved":result['native_caller_budget_preserved'],"promotion_signal":result['promotion_signal']},indent=2),flush=True)

if __name__=='__main__': main()
