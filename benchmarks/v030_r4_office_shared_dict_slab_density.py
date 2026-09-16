from __future__ import annotations

"""Density referee: bounded shared context for independently addressable Office slabs.

Source-sealed H-ATTR showed current SFV4 loses 1,866,036 physical bytes specifically
in the exact-member stream path while winning 1,314,012 B outside it.  Frozen v0.25's
stream mechanism obtained that advantage with up to 512 KiB Zstd-3 cold slabs, i.e. it
had much more cross-stream context than a locality-safe 4 KiB frame.

H-DICT8: if a material share of that advantage is cross-stream statistical context,
a single content-trained 8 KiB Zstd dictionary should let independent 4 KiB stream
slabs recover enough density to make the complete locality-metadata-bearing SFV4
candidate beat frozen v0.29 Office.

The dictionary size is preregistered as exactly one quarter of the fixed 32 KiB physical
read budget, not selected by a sweep.  Dictionary bytes are stored once in the archive,
with the same conservative 53-byte authenticated-frame tax used by the slab referee.
This referee grants density evidence only.  A future reader must charge the whole 8 KiB
dictionary on each cold selective read plus every slab frame touched and still stay <=8x.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_page_slab_stream_store as BASE
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

try:
    import zstandard as zstd
except ImportError as exc:  # research-only dependency; workflow pins installation surface
    raise RuntimeError("zstandard package required for H-DICT8 referee") from exc

SCHEMA = "cmpct-v030-r4-office-shared-dict-slab-density-v1"
DICT_BYTES = 8 * 1024
SLAB_BYTES = 4 * 1024
LEVEL = 3
FRAME_TAX = 53


def _samples(streams: dict[str, bytes]) -> list[bytes]:
    out=[]
    for h in sorted(streams):
        b=streams[h]
        for o in range(0,len(b),SLAB_BYTES):
            part=b[o:o+SLAB_BYTES]
            if part: out.append(part)
    return out


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","r4_office_dict8_neutral")
    repair=V029._load(V029.REPAIR_PATH,"r4_office_dict8_repair"); repair.install_generation_hooks(neutral)
    corpus=work/"neutral"; neutral.build(corpus); repair.normalize_root(corpus); source=corpus/"02_office_workspace"
    built=SFV4.build_candidate(source,work/"sfv4",work/"sfv4-work")
    streams=built["all_streams"]

    samples=_samples(streams)
    t0=time.perf_counter(); c0=time.process_time()
    trained=zstd.train_dictionary(DICT_BYTES,samples)
    dict_raw=trained.as_bytes()
    if len(dict_raw)>DICT_BYTES: raise RuntimeError("trained dictionary exceeded preregistered budget")
    zd=zstd.ZstdCompressionDict(dict_raw)
    enc=zstd.ZstdCompressor(level=LEVEL,dict_data=zd)
    dec=zstd.ZstdDecompressor(dict_data=zd)

    raw_stream=wrapped=slabs=dict_slabs=0
    for h in sorted(streams):
        b=streams[h]; raw_stream += len(b)
        for o in range(0,len(b),SLAB_BYTES):
            part=b[o:o+SLAB_BYTES]; comp=enc.compress(part)
            use=len(comp)<len(part); payload=comp if use else part
            if use and dec.decompress(payload,max_output_size=len(part))!=part: raise RuntimeError("dictionary slab roundtrip")
            wrapped += len(payload)+FRAME_TAX; slabs += 1; dict_slabs += int(use)
    dictionary_physical=len(dict_raw)+FRAME_TAX
    wrapped_total=wrapped+dictionary_physical

    sparse=seed=logical_seed=0
    hashes=sorted({rec["stream_hash"] for rec in built["derived_inventory"].values()})
    for h in hashes:
        comp=streams[h]; raw=zlib.decompress(comp,-15); parsed=DEP.parse_tokens(comp)
        anchors,_blocks,s=COLD._build_metadata(parsed); _seeds,se,sl=SEED._build_seeds(parsed,anchors,raw)
        sparse+=s; seed+=se; logical_seed+=sl

    sfv4=int(built["stored_bytes"]); nonstream=sfv4-raw_stream
    candidate=nonstream+wrapped_total+sparse+seed
    cpu=time.process_time()-c0; wall=time.perf_counter()-t0
    return {
      "schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),"workload":"02_office_workspace","tree_sha256":PRODUCT.treehash(source),
      "candidate":{"slab_bytes":SLAB_BYTES,"dictionary_budget_bytes":DICT_BYTES,"dictionary_actual_bytes":len(dict_raw),"zstd_level":LEVEL,"frame_tax_bytes":FRAME_TAX,
                   "dictionary_physical_bytes":dictionary_physical,"slabs":slabs,"dictionary_compressed_slabs":dict_slabs},
      "stream_store":{"raw_stream_bytes":raw_stream,"wrapped_slab_bytes_excluding_dictionary":wrapped,"wrapped_stream_plus_dictionary_bytes":wrapped_total,
                      "saving_bytes":raw_stream-wrapped_total},
      "economics":{"sfv4_bytes":sfv4,"sfv4_nonstream_bytes":nonstream,"sparse_metadata_bytes":sparse,"seed_metadata_bytes":seed,"logical_seed_bytes":logical_seed,
                   "candidate_with_locality_metadata_bytes":candidate,"accepted_v029_office_bytes":SFV4.ACCEPTED_V029_OFFICE,
                   "margin_to_v029_bytes":SFV4.ACCEPTED_V029_OFFICE-candidate,"density_feasible":candidate<SFV4.ACCEPTED_V029_OFFICE,
                   "dictionary_train_and_encode_cpu_s":cpu,"dictionary_train_and_encode_wall_s":wall},
      "hypothesis":{"shared_8k_context_recovers_product_density":candidate<SFV4.ACCEPTED_V029_OFFICE},
      "contract":{"diagnostic_only":True,"release_credit":False,"locality_credit":False,"dictionary_charged_in_archive":True,
                  "future_reader_must_charge_dictionary_per_cold_read":True,"no_parameter_sweep":True,"selector_changed":False,"format_changed":False,
                  "remaining_debt":"cold-reader <=8x with dictionary charged; serialized authenticated directory; pread; corruption/recovery; fresh CPU/RSS; native parity"}
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-dict8-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-dict8.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"candidate":d["candidate"],"stream_store":d["stream_store"],"economics":d["economics"],"hypothesis":d["hypothesis"]},indent=2))

if __name__=="__main__": main()
