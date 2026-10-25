"""O79: read an authenticated r24 VZIP 64-byte range without inflating retained Deflate.

Research oracle ONLY: existing product unchanged, whole virtual ZIP SHA from authenticated
recipe checks the same copied bytes used for the range. No evidence of product promotion.
Preregistered in docs/v031-research/2026-10-25-o79-vzip-whole-recipe-authenticated-range-prereg.md.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import statistics
import tempfile
import time
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, S_VZIP
from cmpct.reader import CMPCT
from v031_o76_vzip_retention_oracle import make_zip, source_payload


def sha(b):
    return hashlib.sha256(b).hexdigest()


def authenticated_zip_range(reader, name, start, length):
    """Research-only whole-recipe SHA proof over captured physical compressed bytes.

    This does NOT require Deflate expansion for mode-0 retained streams. It authenticates
    the entire original ZIP's logical bytes using the SHA already in the signed/indexed
    r24 recipe. All segments are copied once before hashing and extracting the slice:
    no post-verification second mmap read of the selected stream.
    """
    row = reader.by[name]
    assert row[6][0] == S_VZIP, "research court requires an actual VZIP file"
    skref, lens, payloads, want_sha, want_size, want_crc = reader.recipes[row[6][1]]
    end = start + length
    if start < 0 or length < 0 or end > want_size:
        raise ValueError("range outside virtual ZIP")
    sk = reader._blob(skref)
    if len(sk) != sum(lens) or len(lens) != len(payloads) + 1:
        raise IOError("VZIP skeleton shape mismatch")

    h = hashlib.sha256()
    out = []
    pos = 0
    skpos = 0
    hashed = 0
    stream_bytes = 0
    expanded_bytes = 0

    def accept(part):
        nonlocal pos, hashed
        # CPython mmap slices and codec APIs are fresh bytes. Explicit immutable copy
        # binds hashed bytes to returned bytes despite later on-disk source mutations.
        part = bytes(part)
        n = len(part)
        h.update(part)
        hashed += n
        if pos < end and pos + n > start:
            lo = max(start, pos) - pos
            hi = min(end, pos+n) - pos
            out.append(part[lo:hi])
        pos += n

    for i, (rawref, method, mode, streamref, csize, level) in enumerate(payloads):
        literal = sk[skpos:skpos+lens[i]]
        accept(literal)
        skpos += lens[i]
        if method == zipfile.ZIP_STORED:
            segment = reader._blob(rawref)
        else:
            segment = reader._stream(mode, streamref, level)
            stream_bytes += len(segment)
            if mode == 2:
                # For mode-2, this oracle pays all the original recompression cost.
                expanded_bytes += reader.blobs[streamref][1]
        if len(segment) != csize:
            raise IOError("VZIP compressed stream length mismatch")
        accept(segment)

    accept(sk[skpos:skpos+lens[-1]])
    if pos != want_size or hashed != want_size or h.digest() != bytes(want_sha):
        raise IOError("VZIP whole-recipe SHA-256 mismatch")
    piece = b"".join(out)
    if len(piece) != length:
        raise IOError("VZIP range length mismatch")
    return piece, {"logical_zip_bytes_hashed": hashed,
                   "retained_compressed_stream_bytes": stream_bytes,
                   "mode2_expanded_logical_bytes": expanded_bytes}


def sample(path, begin, kind):
    with CMPCT(path) as r:
        t0 = time.perf_counter_ns()
        cpu0 = time.process_time_ns()
        if kind == "sha":
            piece, meter = authenticated_zip_range(r, "sample.zip", begin, 64)
        else:
            piece = r.read_range("sample.zip", begin, 64)
            meter = {}
        wall = time.perf_counter_ns() - t0
        cpu = time.process_time_ns() - cpu0
    return {"wall_ns": wall, "cpu_ns": cpu, "sha256": sha(piece), **meter}


def mutate_to(path, dest, position):
    shutil.copyfile(path, dest)
    raw = bytearray(dest.read_bytes())
    assert 0 <= position < len(raw)
    before = raw[position]
    raw[position] ^= 1
    dest.write_bytes(raw)
    return {"physical_position": position, "from": before, "to": raw[position],
            "changed_archive_sha256": sha(raw)}


def location(reader, idx, within):
    off, us, cs, codec, ml = reader.blobs[idx]
    assert cs > within and within >= 0
    return int(reader.record_base + off + BHDR.size + ml + within)


def probe(path, begin, verified):
    try:
        with CMPCT(path) as r:
            if verified:
                part, meter = authenticated_zip_range(r, "sample.zip", begin, 64)
            else:
                part = r.read_range("sample.zip", begin, 64)
        return {"outcome": "returned", "sha256": sha(part)}
    except Exception as exc:
        return {"outcome": "rejected", "type": type(exc).__name__,
                "reason": str(exc)[:250]}


def run_case(tmp, case):
    root = tmp / case
    src = root / "source"
    src.mkdir(parents=True)
    physical_zip, begin, clen = make_zip(source_payload(case))
    (src/"sample.zip").write_bytes(physical_zip)
    paths = {"mode2": root/"mode2.cmpct", "mode0": root/"mode0.cmpct"}
    for label, limit in (("mode2", 65536), ("mode0", 0)):
        Builder(src, deflate_reuse_min=limit, workers=1, reproducible=True).build(paths[label])
    modes = {}
    for label, p in paths.items():
        with CMPCT(p) as r:
            assert r.verify() == 1
            assert r.read("sample.zip") == physical_zip
            row = r.by["sample.zip"]
            assert row[6][0] == S_VZIP
            modes[label] = int(r.recipes[row[6][1]][2][0][2])
            assert r.read_range("sample.zip", begin, 64) == physical_zip[begin:begin+64]
            got, met = authenticated_zip_range(r, "sample.zip", begin, 64)
            assert got == physical_zip[begin:begin+64]
    assert modes["mode0"] == 0
    assert modes["mode2"] == (0 if case == "random2m" else 2)

    names = ("mode2_regular", "mode0_sha", "mode0_unchecked")
    samples = {x: [] for x in names}
    path_for = {"mode2_regular": paths["mode2"], "mode0_sha": paths["mode0"],
                "mode0_unchecked": paths["mode0"]}
    type_for = {"mode2_regular": "normal", "mode0_sha": "sha", "mode0_unchecked": "normal"}
    expected = sha(physical_zip[begin:begin+64])
    for _ in range(3):
        for arm in ("mode2_regular", "mode0_sha", "mode0_sha", "mode2_regular"):
            x = sample(path_for[arm], begin, type_for[arm])
            assert x["sha256"] == expected
            samples[arm].append(x)
        for _ in range(2):
            x = sample(paths["mode0"], begin, "normal")
            assert x["sha256"] == expected
            samples["mode0_unchecked"].append(x)
    assert all(len(x) == 6 for x in samples.values())
    median = {k: {metric: statistics.median(v[metric] for v in vals)
                  for metric in ("wall_ns", "cpu_ns")} for k, vals in samples.items()}

    mutations = []
    with CMPCT(paths["mode0"]) as r:
        recipe = r.recipes[r.by["sample.zip"][6][1]]
        sk_idx = recipe[0]
        stream_idx = recipe[2][0][3]
        assert recipe[2][0][2] == 0
        off, us, cs, codec, ml = r.blobs[stream_idx]
        assert cs == clen
        stream_selected = location(r, stream_idx, 16)
        stream_other = location(r, stream_idx, cs-12)
        sk_off, sk_us, sk_cs, sk_codec, sk_ml = r.blobs[sk_idx]
        assert sk_cs >= 1
        sk_pos = location(r, sk_idx, 0)
    for key, at in (("selected_stream", stream_selected),
                    ("other_stream", stream_other),
                    ("skeleton", sk_pos)):
        target = root / (key + "-corrupted.cmpct")
        changed = mutate_to(paths["mode0"], target, at)
        strong = probe(target, begin, True)
        weak = probe(target, begin, False)
        assert strong["outcome"] == "rejected", (case, key, strong)
        mutations.append({"case": key, "mutation": changed,
                          "sha_authenticated": strong, "legacy_unchecked": weak})
    # CRC-equipped mode-2 physical blob is the independently rooted positive control
    # for the existing Reader's corruption refusal.
    if modes["mode2"] == 2:
        with CMPCT(paths["mode2"]) as r:
            rawidx = r.recipes[r.by["sample.zip"][6][1]][2][0][0]
            boff, bus, bcs, bcodec, bml = r.blobs[rawidx]
            at = location(r, rawidx, bcs//2)
        target = root/"mode2-corrupted.cmpct"
        changed = mutate_to(paths["mode2"], target, at)
        legacy = probe(target, begin, False)
        assert legacy["outcome"] == "rejected", (case, legacy)
        mutations.append({"case": "mode2_crc_control", "mutation": changed,
                          "legacy_mode2": legacy})
    speed = median["mode2_regular"]["wall_ns"]/max(1,median["mode0_sha"]["wall_ns"])
    return {"case":case, "modes":modes,
            "source_sha256":sha(physical_zip),"source_zip_bytes":len(physical_zip),
            "original_deflate_stream_bytes":clen,
            "selected_range":[begin,64], "selected_sha256":expected,
            "stored_bytes":{k:p.stat().st_size for k,p in paths.items()},
            "stored_sha256":{k:sha(p.read_bytes()) for k,p in paths.items()},
            "samples":samples,"medians":median,
            "authenticated_speed_ratio":speed,
            "mutations":mutations,"all_full_read_verify_exact":True}


def main():
    records=[]
    output=Path("o79-evidence.json")
    with tempfile.TemporaryDirectory(prefix="cmpct-o79-") as d:
        for case in ("repeat2m","periodic8m","mixed2m","random2m"):
            result = run_case(Path(d),case)
            records.append(result)
            output.write_text(json.dumps({"schema":"cmpct-o79-r1","status":"PARTIAL",
                                          "cases":records},indent=2,sort_keys=True)+"\n")
            print("O79_CASE",case,"MODES",result["modes"],
                  "SHA_WALL_RATIO",round(result["authenticated_speed_ratio"],3),
                  "HOSTILE",len(result["mutations"]),flush=True)
    eligible = [r for r in records if r["modes"]=={"mode2":2,"mode0":0}]
    survives = [r for r in eligible if r["authenticated_speed_ratio"] >= 8
                and r["stored_bytes"]["mode0"]-r["stored_bytes"]["mode2"] <= 65536]
    decision = ("SHA_AUTHENTICATED_RETENTION_HEADROOM" if len(survives)>=2 else
                "NO_BOUNDED_SHA_AUTHENTICATED_RETENTION_HEADROOM")
    evidence = {"schema":"cmpct-o79-r1","source_head":os.getenv("EVIDENCE_HEAD","LOCAL_UNBOUND"),
                "historical_source_blobs":{"builder":"663ef0922992b1fbb8f19e6eea88d55c10a56044",
                                           "reader":"e716233403dabd0966863c45635e18fa5ac6afb8",
                                           "codec":"29526db4203723d83523fc95d074c346b63d7587"},
                "host":{"python":os.sys.version,
                        "linux_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                "cases":records,"decision":decision,
                "scope":"research-only installed-product oracle; no native/official release authority"}
    output.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print("O79_DECISION="+decision,flush=True)
    print("O79_CASE_COUNT="+str(len(records)),flush=True)


if __name__=="__main__":
    main()
