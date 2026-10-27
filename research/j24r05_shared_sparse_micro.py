"""J24R05 cheap local mechanism falsifier: no installed Reader/product credit.

Isolates the exact duplicated S_SPARSE reconstruction body at #596 and a shared
iterator variant. It intentionally does not create files or bypass product gates.
Run: python research/j24r05_shared_sparse_micro.py
"""
import bisect
import json
import random
import statistics
import sys
import time


def dual(extents, blobs, start, length):
    end = start + length
    if length == 0:
        return b""
    out = bytearray(length)
    if len(extents) <= 4:
        for off, ln, ids in extents:
            if off >= end:
                break
            if off + ln <= start:
                continue
            q = off
            for idx in ids:
                bs = len(blobs[idx])
                chunk_end = q + bs
                if chunk_end > start and q < end:
                    b = blobs[idx]
                    a = max(start, q) - q
                    z = min(end, chunk_end) - q
                    out[max(q, start) - start:min(chunk_end, end) - start] = b[a:z]
                q = chunk_end
                if q >= end:
                    break
        return bytes(out)
    first = bisect.bisect_right(extents, start, key=lambda extent: extent[0] + extent[1])
    for extent_index in range(first, len(extents)):
        off, ln, ids = extents[extent_index]
        if off >= end:
            break
        extent_end = off + ln
        if extent_end <= start:
            continue
        q = off
        for idx in ids:
            bs = len(blobs[idx])
            chunk_end = q + bs
            if chunk_end > start and q < end:
                b = blobs[idx]
                a = max(start, q) - q
                z = min(end, chunk_end) - q
                out[max(q, start) - start:min(chunk_end, end) - start] = b[a:z]
            q = chunk_end
            if q >= end:
                break
    return bytes(out)


def shared(extents, blobs, start, length):
    end = start + length
    if length == 0:
        return b""
    out = bytearray(length)
    if len(extents) <= 4:
        selected = iter(extents)
    else:
        first = bisect.bisect_right(extents, start, key=lambda extent: extent[0] + extent[1])
        selected = (extents[i] for i in range(first, len(extents)))
    for off, ln, ids in selected:
        if off >= end:
            break
        if off + ln <= start:
            continue
        q = off
        for idx in ids:
            bs = len(blobs[idx])
            chunk_end = q + bs
            if chunk_end > start and q < end:
                b = blobs[idx]
                a = max(start, q) - q
                z = min(end, chunk_end) - q
                out[max(q, start) - start:min(chunk_end, end) - start] = b[a:z]
            q = chunk_end
            if q >= end:
                break
    return bytes(out)


def run():
    results = []
    for count in (1, 2, 4, 5, 16, 129, 4096, 65536):
        extents = [[i * 19, 4, [0]] for i in range(count)]
        blobs = [b"ABCD"]
        last = extents[-1][0] + 3
        for start, length in ((0, last + 1), (0, 1), (last, 1)):
            assert shared(extents, blobs, start, length) == dual(extents, blobs, start, length)
        times = {"dual": [], "shared": []}
        for trial in range(10 if count <= 129 else 6):
            order = [("dual", dual), ("shared", shared)]
            random.Random(99 * count + trial).shuffle(order)
            for name, function in order:
                t0 = time.perf_counter_ns()
                for _ in range(256):
                    assert function(extents, blobs, last, 1) == b"D"
                times[name].append((time.perf_counter_ns() - t0) / 1000000)
        median = {k: statistics.median(v) for k, v in times.items()}
        results.append({"count": count, "median_ms": median,
                        "shared_over_dual": median["shared"] / median["dual"],
                        "raw_ms": times})
    print(json.dumps({"python": sys.version, "claim": "mechanism micro only",
                      "results": results}, sort_keys=True, indent=2))


if __name__ == "__main__":
    run()
