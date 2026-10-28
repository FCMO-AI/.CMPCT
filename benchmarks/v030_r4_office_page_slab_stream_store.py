from __future__ import annotations

"""Office 4 KiB bounded stream-store falsifier.

Causal input
============
The source-sealed H-ATTR v2 referee reproduced the inherited v0.25/v0.29 Office floor
exactly at 5,954,026 B on the same repaired tree.  Current SFV4 is 6,506,050 B.  The
entire coarse deficit is overdetermined by one physical role:

  current raw exact-member streams.bin     5,658,164 B
  frozen v0.25 authenticated stream pool   3,792,128 B   (+1,866,036 B current debt)
  all other current SFV4 bytes               847,886 B
  all other frozen v0.25 bytes             2,161,898 B   (-1,314,012 B current win)

So v0.30 is already substantially better outside the stream pool.  Frozen v0.25 gets
its stream win by optionally applying Zstd-3 to bounded cold stream slabs, while SFV4
stores exact Deflate member streams raw.

Mission lock H-SLAB4
====================
Without changing SFV4's exact Deflate streams, 4 KiB output request, 4 KiB anchor/page,
8x locality law, page seeds, corpus, or selector, replace raw streams.bin by independently
addressable authenticated *4 KiB raw-stream slabs*.  Each slab competes STORE versus
Zstd-3 and pays a conservative 53-byte v0.25-style physical header/authentication tax.
No slab-size or level sweep is allowed: 4 KiB is inherited directly from the already
fixed selective-read unit and level 3 is the frozen v0.25 cold-stream mechanism.

The selective reader receives a lazy slab byte source.  The original Deflate bytes are
not resident in that source: touching a compressed-stream byte loads/decodes its one
slab and charges the full physical slab frame.  Existing sparse anchor/block and page-
seed metadata are charged exactly as before.

Disprove H-SLAB4 if any of the 1,800 Office probes is byte-inexact, any charged read is
>32,768 B, or the complete SFV4 artifact with the *entire* wrapped all-member stream
store plus all sparse/page-seed metadata is not strictly below frozen v0.29 Office.
A pass is still diagnostic: the slab directory/metadata model is estimated by an
explicit conservative frame tax, not yet serialized into canonical authenticated r25;
os.pread, corruption/recovery, fresh CPU/RSS and native parity remain unpaid.
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-page-slab-stream-store-v1"
PAGE = 4096
LIMIT = 8 * PAGE
SLAB = PAGE
ZSTD_LEVEL = 3
SLAB_TAX = 53  # frozen v0.25 PH: codec + usize + csize + CRC32 + SHA-256
MAX_DECODE_SYMBOLS = SEED.MAX_DECODE_SYMBOLS

_z = ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so")
_sz = ctypes.c_size_t
_z.ZSTD_compressBound.argtypes = [_sz]; _z.ZSTD_compressBound.restype = _sz
_z.ZSTD_compress.argtypes = [ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.c_int]; _z.ZSTD_compress.restype = _sz
_z.ZSTD_decompress.argtypes = [ctypes.c_void_p, _sz, ctypes.c_void_p, _sz]; _z.ZSTD_decompress.restype = _sz


def zc(b: bytes, level: int = ZSTD_LEVEL) -> bytes:
    if not b: return b""
    s = ctypes.create_string_buffer(b); cap = int(_z.ZSTD_compressBound(len(b))); d = ctypes.create_string_buffer(cap)
    n = int(_z.ZSTD_compress(d, cap, s, len(b), level)); return d.raw[:n]


def zd(b: bytes, n: int) -> bytes:
    if not n: return b""
    s = ctypes.create_string_buffer(b); d = ctypes.create_string_buffer(n)
    got = int(_z.ZSTD_decompress(d, n, s, len(b)))
    if got != n: raise RuntimeError(f"zstd slab decode length mismatch {got} != {n}")
    return d.raw[:got]


def build_slab_store(raw: bytes) -> tuple[list[dict], int]:
    slabs=[]; stored=0
    for start in range(0, len(raw), SLAB):
        part=raw[start:start+SLAB]; enc=zc(part)
        codec="zstd3" if len(enc) < len(part) else "store"; payload=enc if codec=="zstd3" else part
        rec={"start":start,"raw_bytes":len(part),"codec":codec,"payload":payload,
             "frame_bytes":len(payload)+SLAB_TAX,"raw_sha256":hashlib.sha256(part).hexdigest()}
        slabs.append(rec); stored += rec["frame_bytes"]
    return slabs, stored


class LazySlabBytes:
    """Bytes-like random source backed only by independently decodable stream slabs."""
    def __init__(self, slabs: list[dict], logical_bytes: int):
        self.slabs=slabs; self.logical_bytes=logical_bytes; self.cache={}; self.touched=set()
    def __len__(self): return self.logical_bytes
    def _load(self, i: int) -> bytes:
        if i in self.cache: return self.cache[i]
        r=self.slabs[i]; p=r["payload"]; b=zd(p,r["raw_bytes"]) if r["codec"]=="zstd3" else p
        if len(b)!=r["raw_bytes"] or hashlib.sha256(b).hexdigest()!=r["raw_sha256"]:
            raise RuntimeError("stream slab integrity mismatch")
        self.cache[i]=b; self.touched.add(i); return b
    def __getitem__(self, key):
        if isinstance(key, slice):
            start,stop,step=key.indices(self.logical_bytes)
            if step!=1: return bytes(self[i] for i in range(start,stop,step))
            if start>=stop:return b""
            out=bytearray(); pos=start
            while pos<stop:
                si=pos//SLAB; b=self._load(si); off=pos-si*SLAB; take=min(stop-pos,len(b)-off)
                out += b[off:off+take]; pos += take
            return bytes(out)
        i=int(key)
        if i<0:i+=self.logical_bytes
        if not 0<=i<self.logical_bytes: raise IndexError(i)
        si=i//SLAB; return self._load(si)[i-si*SLAB]
    def physical_bytes_touched(self) -> int:
        return sum(self.slabs[i]["frame_bytes"] for i in self.touched)


class SlabSeedReader(SEED.SeedReader):
    def __init__(self, source: LazySlabBytes, anchors, blocks, seeds, output_bytes):
        super().__init__(source, anchors, blocks, seeds, output_bytes)
        self.slab_source=source
    def payload_bytes(self) -> int:
        return self.slab_source.physical_bytes_touched()


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_office_slab4_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_office_slab4_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"02_office_workspace"
    built=SFV4.build_candidate(source,work/"sfv4",work/"sfv4-work")
    derived=built["derived_inventory"]; streams=built["all_streams"]
    hashes=sorted({rec["stream_hash"] for rec in derived.values()})

    # Price the complete all-member store, not just streams exercised by the derived-file probes.
    stores={}; raw_stream_bytes=0; wrapped_stream_bytes=0; total_slabs=0; zstd_slabs=0
    for h,comp in streams.items():
        slabs,stored=build_slab_store(comp); stores[h]=slabs; raw_stream_bytes += len(comp); wrapped_stream_bytes += stored
        total_slabs += len(slabs); zstd_slabs += sum(r["codec"]=="zstd3" for r in slabs)
    if raw_stream_bytes != int(built["all_member_stream_bytes"]):
        raise RuntimeError("all-member stream accounting mismatch")

    sparse_metadata=seed_metadata=logical_seed_bytes=0; requests=exact_failures=locality_failures=0; max_symbols=0; worst=None; rows=[]
    t0=time.perf_counter()
    for h in hashes:
        comp=streams[h]; raw=zlib.decompress(comp,-15); parsed=DEP.parse_tokens(comp)
        if parsed["output_bytes"]!=len(raw): raise RuntimeError("DEFLATE parser/output mismatch")
        anchors,blocks,sparse_stored=COLD._build_metadata(parsed); seeds,seed_stored,seed_logical=SEED._build_seeds(parsed,anchors,raw)
        sparse_metadata += sparse_stored; seed_metadata += seed_stored; logical_seed_bytes += seed_logical
        row={"stream_sha256":h,"raw_output_bytes":len(raw),"deflate_bytes":len(comp),"wrapped_deflate_store_bytes":sum(r["frame_bytes"] for r in stores[h]),
             "sparse_metadata_bytes":sparse_stored,"seed_metadata_bytes":seed_stored,"requests":0,"locality_failures":0,"exact_failures":0,"worst_combined_bytes":0}
        for start in TRANSFER._starts(len(raw)):
            end=min(start+PAGE,len(raw)); slab_source=LazySlabBytes(stores[h],len(comp)); r=SlabSeedReader(slab_source,anchors,blocks,seeds,len(raw))
            q0=time.perf_counter(); got=r.read(start,end); qwall=time.perf_counter()-q0; exact=got==raw[start:end]
            meta=r.metadata_bytes(); payload=r.payload_bytes(); combined=meta+payload; requests+=1; row["requests"]+=1; max_symbols=max(max_symbols,r.symbols_decoded)
            if not exact: exact_failures+=1; row["exact_failures"]+=1
            if combined>LIMIT: locality_failures+=1; row["locality_failures"]+=1
            row["worst_combined_bytes"]=max(row["worst_combined_bytes"],combined)
            q={"stream_sha256":h,"start":start,"end":end,"request_bytes":end-start,"metadata_bytes_touched":meta,"slab_payload_bytes_touched":payload,
               "combined_bytes_touched":combined,"combined_amplification":combined/max(1,end-start),"slabs_touched":len(slab_source.touched),
               "symbols_decoded":r.symbols_decoded,"wall_s":qwall,"exact":exact}
            if worst is None or combined>worst["combined_bytes_touched"]: worst=q
        rows.append(row)
    probe_wall=time.perf_counter()-t0

    sfv4=int(built["stored_bytes"]); base_without_raw_streams=sfv4-raw_stream_bytes
    candidate=base_without_raw_streams+wrapped_stream_bytes+sparse_metadata+seed_metadata
    margin=SFV4.ACCEPTED_V029_OFFICE-candidate
    supported=exact_failures==0 and locality_failures==0 and margin>0
    return {
      "schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"workload":"02_office_workspace","tree_sha256":PRODUCT.treehash(source),"streams":rows,
      "summary":{"derived_file_count":len(derived),"unique_derived_stream_count":len(hashes),"requests":requests,"request_bytes":PAGE,"limit_bytes":LIMIT,
                 "exact_failures":exact_failures,"locality_failures":locality_failures,"max_symbols_decoded_per_request":max_symbols,"worst_combined":worst,"probe_wall_s":probe_wall},
      "stream_store":{"slab_bytes":SLAB,"zstd_level":ZSTD_LEVEL,"slab_tax_bytes":SLAB_TAX,"all_member_raw_stream_bytes":raw_stream_bytes,
                      "all_member_wrapped_stream_bytes":wrapped_stream_bytes,"stream_store_saving_bytes":raw_stream_bytes-wrapped_stream_bytes,
                      "total_slabs":total_slabs,"zstd_slabs":zstd_slabs,"stored_slabs":total_slabs-zstd_slabs},
      "economics":{"sfv4_bytes_before_locality_metadata":sfv4,"sfv4_nonstream_bytes":base_without_raw_streams,"wrapped_stream_store_bytes":wrapped_stream_bytes,
                   "sparse_anchor_block_metadata_bytes":sparse_metadata,"page_seed_metadata_bytes":seed_metadata,"logical_seed_bytes_before_framing":logical_seed_bytes,
                   "candidate_with_all_locality_metadata_bytes":candidate,"accepted_v029_office_bytes":SFV4.ACCEPTED_V029_OFFICE,"margin_to_v029_bytes":margin},
      "hypothesis":{"bounded_4k_stream_slabs_recover_density_and_locality":supported},
      "contract":{"diagnostic_only":True,"release_credit":False,"fixed_slab_bytes":SLAB,"fixed_zstd_level":ZSTD_LEVEL,"fixed_request_bytes":PAGE,"fixed_limit_bytes":LIMIT,
                  "no_parameter_sweep":True,"reader_source_contains_original_deflate_bytes":False,"slab_integrity_checked":True,"selector_changed":False,"format_changed":False,
                  "remaining_debt":"serialize/authenticate slab directory in canonical r25; os.pread/seeks; hostile corruption/recovery; fresh CPU/RSS; native parity"},
      "next_if_supported":"serialize the 4KiB slab directory/frames into an authenticated cold-reader prototype and measure pread/seeks + fresh CPU/RSS before any selector admission",
      "next_if_falsified":"preserve result; distinguish insufficient 4KiB stream-context gain from slab-I/O locality failure before considering any larger bounded context"
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-slab4-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-slab4.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"summary":d["summary"],"stream_store":d["stream_store"],"economics":d["economics"],"hypothesis":d["hypothesis"]},indent=2))

if __name__=="__main__": main()
