"""O76: source-exact authentic VZIP retained-stream versus regeneration oracle.

Research-only: unchanged CMPCT revision-24 Builder/Reader, no release-performance claims.
The data include full original files, a negative eligibility control, complete archive
bytes and raw alternating fresh-reader measurements.
"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
import os
import random
import statistics
import struct
import tempfile
import time
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def source_payload(case):
    size = 8 * 1024 * 1024 if case == "periodic8m" else 2 * 1024 * 1024
    if case == "repeat2m":
        return b"R" * size
    if case == "periodic8m":
        return bytes(range(256)) * (size // 256)
    rng = random.Random(700_076)
    if case == "mixed2m":
        result = bytearray(b"M" * size)
        for i in range(32):
            pos = (i * 61973 + 47) % (size - 1024)
            result[pos : pos + 1024] = rng.randbytes(1024)
        return bytes(result)
    if case == "random2m":
        return rng.randbytes(size)
    raise ValueError(case)


def make_zip(payload):
    out = io.BytesIO()
    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("payload.bin", payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    raw = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        assert len(infos) == 1
        zi = infos[0]
        assert z.read(zi) == payload
    fields = struct.unpack_from("<IHHHHHIIIHH", raw, zi.header_offset)
    assert fields[0] == 0x04034B50
    stream_begin = zi.header_offset + 30 + fields[-2] + fields[-1]
    assert zi.compress_size >= 96
    begin = stream_begin + 16
    assert begin + 64 < stream_begin + zi.compress_size
    return raw, begin, zi.compress_size


def timed_build(root, archive, limit):
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    Builder(root, deflate_reuse_min=limit, workers=1, reproducible=True).build(archive)
    return {"wall_ns": time.perf_counter_ns() - t0, "cpu_ns": time.process_time_ns() - c0}


def inspect_and_validate(archive, source, begin, destination):
    with CMPCT(archive) as r:
        row = r.by["sample.zip"]
        assert row[6][0] == S_VZIP, f"expected S_VZIP, received {row[6]}"
        recipe = r.recipes[row[6][1]]
        assert len(recipe[2]) == 1
        mode = int(recipe[2][0][2])
        assert r.read_range("sample.zip", begin, 64) == source[begin : begin + 64]
        assert r.read("sample.zip") == source
        t0 = time.perf_counter_ns()
        assert r.verify() == 1
        verify_ns = time.perf_counter_ns() - t0
        r.extractall(destination)
        assert (destination / "sample.zip").read_bytes() == source
        assert digest(r.read("sample.zip")) == digest(source)
    return mode, verify_ns


def fresh_range(archive, begin):
    with CMPCT(archive) as r:
        materialized = {"count": 0, "bytes": 0}
        old_blob = r._blob

        def tracing_blob(idx):
            value = old_blob(idx)
            materialized["count"] += 1
            materialized["bytes"] += len(value)
            return value

        r._blob = tracing_blob
        t0 = time.perf_counter_ns()
        c0 = time.process_time_ns()
        piece = r.read_range("sample.zip", begin, 64)
        wall = time.perf_counter_ns() - t0
        cpu = time.process_time_ns() - c0
    return {"wall_ns": wall, "cpu_ns": cpu, "materialized": materialized, "sha256": digest(piece)}


def median(vals):
    return statistics.median(vals)


def main():
    provenance = {
        "schema": "cmpct-o76-vzip-range-retention-r1",
        "builder_git_blob": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
        "reader_git_blob": "e716233403dabd0966863c45635e18fa5ac6afb8",
        "codec_git_blob": "29526db4203723d83523fc95d074c346b63d7587",
        "source_head": os.getenv("EVIDENCE_HEAD", "LOCAL_UNBOUND"),
        "python": os.sys.version,
    }
    results = []
    cases = ("repeat2m", "periodic8m", "mixed2m", "random2m")
    with tempfile.TemporaryDirectory(prefix="cmpct-o76-") as dirname:
        root = Path(dirname)
        for name in cases:
            source_dir = root / name / "src"
            source_dir.mkdir(parents=True)
            source = source_payload(name)
            original, begin, compressed_size = make_zip(source)
            (source_dir / "sample.zip").write_bytes(original)
            paths = {
                "regenerate": root / name / "regenerate.cmpct",
                "retained": root / name / "retained.cmpct",
            }
            creation = {
                "regenerate": timed_build(source_dir, paths["regenerate"], 65536),
                "retained": timed_build(source_dir, paths["retained"], 0),
            }
            modes = {}
            verify = {}
            for arm, archive in paths.items():
                assert (source_dir / "sample.zip").read_bytes() == original
                modes[arm], verify[arm] = inspect_and_validate(
                    archive, original, begin, root / name / ("extract-" + arm)
                )
            assert modes["retained"] == 0, (name, modes)
            if name == "random2m":
                assert modes["regenerate"] == 0, (name, modes)
            else:
                assert modes["regenerate"] == 2, (name, modes)

            paired = {"regenerate": [], "retained": []}
            for _ in range(3):
                for arm in ("regenerate", "retained", "retained", "regenerate"):
                    result = fresh_range(paths[arm], begin)
                    assert result["sha256"] == digest(original[begin : begin + 64])
                    paired[arm].append(result)
            assert len(paired["regenerate"]) == len(paired["retained"]) == 6
            medians = {
                arm: {
                    "wall_ns": median([x["wall_ns"] for x in paired[arm]]),
                    "cpu_ns": median([x["cpu_ns"] for x in paired[arm]]),
                    "materialized_bytes": median([x["materialized"]["bytes"] for x in paired[arm]]),
                }
                for arm in paths
            }
            size = {arm: paths[arm].stat().st_size for arm in paths}
            ratio = medians["regenerate"]["wall_ns"] / max(medians["retained"]["wall_ns"], 1)
            case_result = {
                "case": name,
                "expanded_source_bytes": len(source),
                "zip_source_bytes": len(original),
                "zip_compressed_stream_bytes": compressed_size,
                "source_sha256": digest(original),
                "selected_physical_range": [begin, 64],
                "selected_range_sha256": digest(original[begin : begin + 64]),
                "modes": modes,
                "complete_archive_bytes": size,
                "complete_archive_sha256": {arm: digest(paths[arm].read_bytes()) for arm in paths},
                "create": creation,
                "verify_wall_ns": verify,
                "fresh_reader_samples": paired,
                "medians": medians,
                "selective_read_wall_ratio_regenerate_over_retained": ratio,
                "additional_retained_stored_bytes": size["retained"] - size["regenerate"],
                "all_roundtrip_sha_exact": True,
            }
            results.append(case_result)
            print(
                f"O76_CASE={name} MODES={modes} STORED={size} "
                f"SELECTIVE_WALL_RATIO={ratio:.3f} "
                f"MATERIALIZED={medians['regenerate']['materialized_bytes']}/"
                f"{medians['retained']['materialized_bytes']}",
                flush=True,
            )

    eligible = [r for r in results if r["modes"] == {"regenerate": 2, "retained": 0}]
    threshold = (
        len(eligible) >= 2
        and all(
            r["selective_read_wall_ratio_regenerate_over_retained"] >= 8
            and r["additional_retained_stored_bytes"] <= 65536
            for r in eligible
        )
    )
    # The scientific result is not coerced into a green performance claim.
    decision = "BOUNDED_RETENTION_HEADROOM" if threshold else "NO_BOUNDED_RETENTION_CLAIM"
    evidence = {"provenance": provenance, "cases": results, "decision": decision}
    Path("o76-evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print("O76_DECISION=" + decision, flush=True)
    print("O76_CASE_COUNT=" + str(len(results)), flush=True)


if __name__ == "__main__":
    main()
