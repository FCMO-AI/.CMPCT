"""J24K09 micro-economics: metadata-header witness versus optimistic cached control.

RESEARCH/ORACLE ONLY. No product speedup claim; same process, synthetic recipe,
predecoded cached comparison and deliberately unsafe no-witness lower bound.
"""
from __future__ import annotations

import json
import statistics
import time
import zipfile

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, range_vzip
from cmpct.reader import CMPCT


def fixture(n, payload_size=64):
    reader = CMPCT.__new__(CMPCT)
    reader.record_base = 0
    parts = []
    blobs = []
    contents = {0: b"ABCDEFGH"}
    position = 0
    for idx in range(n + 1):
        data = bytes([idx % 251]) * payload_size
        header = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, payload_size,
                           payload_size, 0, 0, b"\\0" * 32)
        blobs.append((position, payload_size, payload_size, CODEC_RAW, 0))
        parts.extend((header, data))
        contents[idx] = data
        position += len(header) + payload_size
    contents[0] = b"ABCDEFGH"
    reader.blobs = blobs
    reader.mm = b"".join(parts)
    recipe = [0, [0] * n + [8],
              [[i, zipfile.ZIP_STORED, 0, i, payload_size, -1]
               for i in range(1, n + 1)],
              b"\\0" * 32, n * payload_size + 8, 0]
    return reader, contents, recipe


def main():
    for n in (64, 512, 4096):
        reader, contents, recipe = fixture(n)
        offset = n * 64 + 6
        def content(idx):
            return contents[idx]
        def stream(*args):
            raise AssertionError("STORED should not invoke Deflate stream")
        def cached_size(method,mode,rawref,streamref):
            return len(contents[rawref])
        versions = {
            "unsafe_no_witness": None,
            "optimistic_predecoded_control": cached_size,
            "physical_bhdr_witness": reader._vzip_physical_stream_size,
        }
        for name, callback in versions.items():
            assert range_vzip(recipe, content, stream, offset, 1, callback) == b"G", name
        measurements = {name: [] for name in versions}
        for cycle in range(6):
            names = ("unsafe_no_witness", "physical_bhdr_witness",
                     "optimistic_predecoded_control",
                     "optimistic_predecoded_control",
                     "physical_bhdr_witness", "unsafe_no_witness")
            for name in names:
                fn = versions[name]
                t0 = time.perf_counter_ns()
                c0 = time.process_time_ns()
                for _ in range(15):
                    assert range_vzip(recipe, content, stream, offset, 1, fn) == b"G"
                measurements[name].append({
                    "wall_ns": (time.perf_counter_ns() - t0) // 15,
                    "cpu_ns": (time.process_time_ns() - c0) // 15,
                })
        med = {name: {
            "wall_ns": statistics.median(x["wall_ns"] for x in values),
            "cpu_ns": statistics.median(x["cpu_ns"] for x in values),
        } for name,values in measurements.items()}
        print("J24K09_MICRO=" + json.dumps({
            "class":"component_oracle_not_product",
            "streams":n, "stream_bytes":64,
            "logical_size":n*64+8,
            "whole_header_bytes":(n+1)*BHDR.size,
            "same_source_same_input":True,
            "unsafe_control_not_valid_product":True,
            "optimistic_control_predecoded":True,
            "medians":med,"raw":measurements
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
