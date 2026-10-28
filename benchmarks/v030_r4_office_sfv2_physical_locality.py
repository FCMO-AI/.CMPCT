from __future__ import annotations

"""Physical-I/O falsifier for Office SFV2 selective locality.

SFV2 already proves byte-exact Office stream federation and reports ideal range mapping, but its
research auth hashes whole pools. This experiment does not change federation/discovery/templates.
It adds a fixed 8 KiB Merkle layer over literal.bin and streams.bin and a compact range-auth root,
then serves preregistered 4 KiB package reads with os.pread from only touched pool leaves plus proof
nodes. All added auth/tree bytes are charged to stored size.

Mission lock: no segment-size sweep. Advance only if (1) exact package ranges are reconstructed,
(2) touched-pool corruption is rejected, (3) max cold authenticated physical amplification <=8x,
and (4) augmented SFV2 remains smaller than same-run ordinary v0.30 Office. This is research
packaging, not the final product crypto/index layout and not release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SF
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-sfv2-physical-locality-v1"
MAGIC = b"R4OSF3\0\0"
SEGMENT = 8 * 1024
REQUEST = 4 * 1024
META = struct.Struct("<QII32sQII32s")  # literal(size, leaves, seg, root), stream(...)


def _h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def _merkle(raw: bytes) -> tuple[list[list[bytes]], bytes]:
    leaves = [_h(raw[i:i+SEGMENT]) for i in range(0, len(raw), SEGMENT)] or [_h(b"")]
    levels = [leaves]
    while len(levels[-1]) > 1:
        prev = levels[-1]
        levels.append([_h(prev[i] + (prev[i+1] if i+1 < len(prev) else prev[i])) for i in range(0, len(prev), 2)])
    tree = b"".join(x for level in levels[:-1] for x in level)
    return levels, tree


def _counts(n: int) -> list[int]:
    out = [n]
    while out[-1] > 1:
        out.append((out[-1] + 1) // 2)
    return out


def _offsets(n: int) -> list[int]:
    p = 0; out = []
    for count in _counts(n)[:-1]:
        out.append(p); p += count * 32
    return out


def _verify_leaf(tree_fd: int, leaves: int, root: bytes, idx: int, data: bytes) -> tuple[bool, int]:
    node = _h(data); proof = 0; offsets = _offsets(leaves)
    for level, count in enumerate(_counts(leaves)[:-1]):
        sibling = idx ^ 1
        if sibling >= count:
            sib = node
        else:
            sib = os.pread(tree_fd, 32, offsets[level] + sibling * 32); proof += len(sib)
            if len(sib) != 32: raise ValueError("truncated Merkle proof")
        node = _h(node + sib) if idx % 2 == 0 else _h(sib + node)
        idx //= 2
    return node == root, proof


def _add_range_auth(bundle: Path) -> dict:
    literal = (bundle/"literal.bin").read_bytes(); streams = (bundle/"streams.bin").read_bytes()
    ll, lt = _merkle(literal); sl, st = _merkle(streams)
    (bundle/"literal.tree").write_bytes(lt); (bundle/"streams.tree").write_bytes(st)
    meta = META.pack(len(literal), len(ll[0]), SEGMENT, ll[-1][0], len(streams), len(sl[0]), SEGMENT, sl[-1][0])
    (bundle/"range.meta").write_bytes(meta)
    manifest = (bundle/"manifest.json").read_bytes()
    root = MAGIC + _h(manifest) + _h(meta)
    (bundle/"range.auth").write_bytes(root)
    added = len(lt)+len(st)+len(meta)+len(root)
    return {"added_range_auth_bytes": added, "literal_tree_bytes": len(lt), "streams_tree_bytes": len(st), "range_meta_bytes": len(meta), "range_auth_bytes": len(root), "literal_leaves": len(ll[0]), "stream_leaves": len(sl[0])}


def _logical_slices(template: dict, stream_index: dict, start: int, length: int) -> list[tuple[str,int,int]]:
    end = min(template["size"], start + length); logical = 0; out = []
    for seg in template["segments"]:
        ss, se = logical, logical + seg["n"]; logical = se
        a, b = max(start, ss), min(end, se)
        if b <= a: continue
        within = a - ss
        if seg["k"] == "l": out.append(("literal", int(seg["o"])+within, b-a))
        else:
            s = stream_index[seg["h"]]; out.append(("streams", int(s["o"])+within, b-a))
    return out


def _cold_range(bundle: Path, rel: str, start: int, length: int) -> tuple[bytes, dict]:
    manifest_raw = (bundle/"manifest.json").read_bytes(); meta_raw = (bundle/"range.meta").read_bytes(); auth = (bundle/"range.auth").read_bytes()
    if auth != MAGIC + _h(manifest_raw) + _h(meta_raw): raise ValueError("range root mismatch")
    manifest = json.loads(manifest_raw); t = manifest["templates"][rel]
    if start < 0 or length < 0 or start + length > t["size"]: raise ValueError("bad logical range")
    lsize, lleaves, lseg, lroot, ssize, sleaves, sseg, sroot = META.unpack(meta_raw)
    if lseg != SEGMENT or sseg != SEGMENT: raise ValueError("segment contract mismatch")
    cfg = {"literal": (bundle/"literal.bin", bundle/"literal.tree", lsize, lleaves, lroot), "streams": (bundle/"streams.bin", bundle/"streams.tree", ssize, sleaves, sroot)}
    touched: dict[tuple[str,int], bytes] = {}; proof_bytes = 0; out = bytearray()
    handles = {}
    try:
        for pool, off, n in _logical_slices(t, manifest["stream_index"], start, length):
            data_path, tree_path, size, leaves, root = cfg[pool]
            if pool not in handles:
                handles[pool] = (open(data_path,"rb",buffering=0), open(tree_path,"rb",buffering=0))
            df, tf = handles[pool]
            pos = off; remaining = n
            while remaining:
                idx = pos // SEGMENT; leaf_off = idx * SEGMENT
                key = (pool, idx)
                if key not in touched:
                    raw = os.pread(df.fileno(), min(SEGMENT, size-leaf_off), leaf_off)
                    ok, pb = _verify_leaf(tf.fileno(), leaves, root, idx, raw)
                    if not ok: raise ValueError("pool segment authentication failed")
                    touched[key] = raw; proof_bytes += pb
                raw = touched[key]; inside = pos - leaf_off; take = min(remaining, len(raw)-inside)
                out.extend(raw[inside:inside+take]); pos += take; remaining -= take
    finally:
        for df, tf in handles.values(): df.close(); tf.close()
    data_bytes = sum(len(v) for v in touched.values()); metadata_bytes = len(manifest_raw)+len(meta_raw)+len(auth)
    physical = data_bytes + proof_bytes + metadata_bytes
    return bytes(out), {"requested_bytes": length, "pool_segment_bytes": data_bytes, "proof_bytes": proof_bytes, "cold_metadata_bytes": metadata_bytes, "physical_bytes_touched": physical, "physical_amplification": physical/max(1,length), "unique_pool_leaves": len(touched)}


def _expected_package(source: Path, rel: str, start: int, length: int) -> bytes:
    b = (source/rel).read_bytes(); return b[start:start+length]


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_office_phys_neutral'); repair=V029._load(V029.REPAIR_PATH,'r4_office_phys_repair'); repair.install_generation_hooks(neutral)
    corpus=work/'neutral'; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/'02_office_workspace'; expected=PRODUCT.treehash(source)
    baseline=work/'baseline.cmpct'; PRODUCT.build(source,baseline)
    bundle=work/'sfv2'; sf=SF.build_candidate(source,bundle,work/'sf-work'); verify=SF.extract_candidate(bundle,work/'extract')
    if verify['tree_sha256'] != expected: raise RuntimeError('SFV2 semantic tree mismatch')
    auth_stats=_add_range_auth(bundle); augmented_bytes=sum(p.stat().st_size for p in bundle.iterdir() if p.is_file())
    manifest=json.loads((bundle/'manifest.json').read_bytes()); reads=[]
    for rel,t in manifest['templates'].items():
        n=min(REQUEST,t['size'])
        for start in sorted({0,max(0,t['size']//2-n//2),max(0,t['size']-n)}):
            got,stats=_cold_range(bundle,rel,start,n)
            if got != _expected_package(source,rel,start,n): raise RuntimeError('cold Office package range mismatch')
            reads.append({'path':rel,'start':start,**stats})
    max_amp=max(x['physical_amplification'] for x in reads)

    # Hostile test: corrupt one pool byte that is actually referenced by the first request.
    rel=reads[0]['path']; start=reads[0]['start']; n=reads[0]['requested_bytes']; slices=_logical_slices(manifest['templates'][rel],manifest['stream_index'],start,n)
    pool,off,_=slices[0]; p=bundle/("literal.bin" if pool=='literal' else "streams.bin")
    with open(p,'r+b') as f:
        f.seek(off); old=f.read(1); f.seek(off); f.write(bytes([old[0]^1])); f.flush(); os.fsync(f.fileno())
    corruption_rejected=False
    try: _cold_range(bundle,rel,start,n)
    except ValueError: corruption_rejected=True
    finally:
        with open(p,'r+b') as f: f.seek(off); f.write(old)
    if not corruption_rejected: raise RuntimeError('touched Office pool corruption was not rejected')

    supported = augmented_bytes < baseline.stat().st_size and max_amp <= 8.0 and corruption_rejected
    return {"schema":SCHEMA,"source_commit":os.environ.get('EVIDENCE_HEAD'),"tree_sha256":expected,"baseline_v030_bytes":baseline.stat().st_size,"sfv2_bytes_before_range_auth":sf['stored_bytes'],"augmented_candidate_bytes":augmented_bytes,"added_range_auth_bytes":augmented_bytes-sf['stored_bytes'],"accepted_v029_office_bytes":SF.ACCEPTED_V029_OFFICE,"saving_vs_v030_bytes":baseline.stat().st_size-augmented_bytes,"margin_vs_v029_bytes":SF.ACCEPTED_V029_OFFICE-augmented_bytes,"range_auth":auth_stats,"selective_reads":reads,"max_cold_authenticated_physical_amplification":max_amp,"corruption_rejected":corruption_rejected,"hypothesis":{"exact_semantic_tree":verify['tree_sha256']==expected,"augmented_sfv2_beats_v030":augmented_bytes<baseline.stat().st_size,"cold_authenticated_4k_le_8x":max_amp<=8.0,"touched_pool_corruption_rejected":corruption_rejected,"supported_for_product_prototype":supported},"contract":{"diagnostic_only":True,"release_credit":False,"production_format_changed":False,"production_selector_changed":False,"federation_representation_unchanged":True,"fixed_8k_merkle_no_sweep":True,"actual_file_backed_pread":True,"all_added_tree_root_bytes_charged":True,"whole_manifest_charged_per_cold_read":True,"base_cmpct_outside_container_range_dependency_cone":True,"original_sfv2_auth_retained_and_charged_conservatively":True},"next_if_supported":"replace JSON template lookup with product-shaped authenticated binary index only if needed, then measure recovery blast radius/native reader complexity and compose hardened Office with an evidence-backed Analytics locality mechanism","next_if_falsified":"preserve negative and attribute whether failure comes from manifest size, Merkle leaf granularity, proof traffic, or cross-pool fragmentation before changing representation"}


def main()->None:
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sfv2-physical-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-sfv2-physical.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+'\n'); print(json.dumps({k:d[k] for k in ('baseline_v030_bytes','sfv2_bytes_before_range_auth','augmented_candidate_bytes','added_range_auth_bytes','accepted_v029_office_bytes','saving_vs_v030_bytes','margin_vs_v029_bytes','max_cold_authenticated_physical_amplification','corruption_rejected','hypothesis')}|{'range_auth':d['range_auth']},indent=2))

if __name__=='__main__': main()
