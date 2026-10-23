"""Diagnose opt-in RAW whole-SHA range cost; not release performance evidence."""
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import tempfile
import time
import tracemalloc

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import CODEC_RAW,S_BLOB

def main():
    groups=[]
    for size in (64*1024,512*1024,2*1024*1024):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input').mkdir()
            raw=random.Random(0xC0FFEE+size).randbytes(size)
            (root/'input'/'payload.bin').write_bytes(raw)
            archive=root/'data.cmpct'
            Builder(root/'input',workers=1).build(archive)
            with CMPCT(archive) as reader:
                row=reader.by['payload.bin']
                # Larger sources can legitimately become chunked under portfolio policy.
                if row[6][0]!=S_BLOB or reader.blobs[row[6][1]][3]!=CODEC_RAW:
                    groups.append({'size':size,'status':'UNSUPPORTED_STORAGE','storage':row[6][0]})
                    continue
                start=size//2
                funcs={
                    'fast_range':lambda:reader.read_range('payload.bin',start,1),
                    'verified_range':lambda:reader.read_raw_range_verified('payload.bin',start,1),
                    'whole_read_crc':lambda:reader.read('payload.bin')[start:start+1],
                }
                observations={n:[] for n in funcs}
                for rep in range(9):
                    order=list(funcs)
                    if rep%2:order.reverse()
                    for mode in order:
                        # Equalize direct-read cache state: otherwise read() wins via a
                        # previously retained 512KiB blob while verified_range always scans.
                        reader.cache.clear()
                        tracemalloc.start()
                        try:
                            w=time.perf_counter_ns();c=time.process_time_ns()
                            result=funcs[mode]()
                            cpu=time.process_time_ns()-c;wall=time.perf_counter_ns()-w
                            _,peak=tracemalloc.get_traced_memory()
                        finally:tracemalloc.stop()
                        assert result==raw[start:start+1]
                        observations[mode].append({'wall_ns':wall,'cpu_ns':cpu,'python_heap_peak_bytes':peak})
                groups.append({
                    'size':size,'status':'MEASURED','archive_bytes':archive.stat().st_size,
                    'observations':observations,
                    'medians':{n:{k:statistics.median(v[k] for v in vals) for k in ('wall_ns','cpu_ns','python_heap_peak_bytes')} for n,vals in observations.items()},
                })
    data={'kind':'RESEARCH_ONLY_NOT_RELEASE','cache_policy':'clear_raw_decode_cache_each_trial','sha256_of_script':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':groups}
    print(json.dumps(data,sort_keys=True,indent=2))
if __name__=='__main__':main()
