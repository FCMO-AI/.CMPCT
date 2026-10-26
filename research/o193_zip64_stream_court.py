#!/usr/bin/env python3
"""O193: installed-source ZIP64 fallback streaming mechanism court; no >=4GiB claim."""
from __future__ import annotations
import hashlib, inspect, json, os, platform, random, stat, sys, tempfile, time, traceback, zipfile
from pathlib import Path

MIB = 1 << 20
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def run():
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_module

    worktree = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    installed = Path(reader_module.__file__).resolve()
    origin = worktree / "src/cmpct/reader.py"
    assert installed != origin, "not an independently installed Reader"
    source = origin.read_bytes().replace(b"\r\n", b"\n")
    installed_bytes = installed.read_bytes().replace(b"\r\n", b"\n")
    assert installed_bytes == source, "installed Reader differs from exact checkout"
    assert "return self._export_zip_compat_stream(out,level)" in inspect.getsource(CMPCT.export_zip)
    source_sha = hashlib.sha256(source).hexdigest()

    with tempfile.TemporaryDirectory(prefix="o193-zip64-stream-") as td:
        root = Path(td) / "source"
        root.mkdir()
        (root / "sub").mkdir()
        data = random.Random(193).randbytes(6 * MIB + 313)
        (root / "data.bin").write_bytes(data)
        (root / "compressible.txt").write_bytes((b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * 17000) + b"END")
        (root / "sub" / "empty.txt").write_bytes(b"")
        if os.name != "nt":
            os.link(root / "data.bin", root / "data-hardlink.bin")
            os.symlink("data.bin", root / "data-link")
        # This hole-rich logical file is real, but nowhere near 4GiB.
        # A host that does not physically support sparse backing skips it explicitly.
        sparse = root / "sparse.bin"
        with sparse.open("wb") as h:
            h.truncate(64 * MIB + 17)
            h.seek(3 * MIB)
            h.write(b"O193-SPARSE-INTERIOR")
            h.seek(62 * MIB)
            h.write(b"TAIL")
        blocks = getattr(sparse.stat(), "st_blocks", 0)
        real_sparse = bool(blocks and blocks * 512 < sparse.stat().st_size // 2)
        if not real_sparse:
            sparse.unlink()

        archive = Path(td) / "original.cmpct"
        Builder(root, workers=1).build(archive)
        archive_sha_before = SHA(archive)
        result = {
            "schema": "cmpct-o193-streaming-v1",
            "host": platform.platform(),
            "installed_reader_sha256": source_sha,
            "git_head": os.environ.get("GITHUB_SHA"),
            "source_archive_sha256": archive_sha_before,
            "source_archive_bytes": archive.stat().st_size,
            "source_sparse_physical_support": real_sparse,
            "source_sparse_logical_bytes": sparse.stat().st_size if real_sparse else 0,
            "genuine_ge_4gib_court": False,
        }
        with CMPCT(archive) as rd:
            allowed = {row[0]: row for row in rd.files}
            counts = {"calls": 0, "logical_bytes_requested": 0, "max_requested": 0}
            old_read = rd.read
            old_range = rd.read_range

            def forbid_whole_read(name):
                raise AssertionError("streaming fallback invoked whole-file CMPCT.read: " + name)

            def tracked_range(name, start, length):
                assert 0 <= length <= MIB, (name, start, length)
                counts["calls"] += 1
                counts["logical_bytes_requested"] += length
                counts["max_requested"] = max(counts["max_requested"], length)
                return old_range(name, start, length)

            rd.read = forbid_whole_read
            rd.read_range = tracked_range
            out = Path(td) / "stream.zip"
            t0 = time.perf_counter()
            rd._export_zip_compat_stream(out, level=6, chunk_bytes=MIB)
            result["stream_wall_s"] = time.perf_counter() - t0
            result["zip_sha256"] = SHA(out)
            result["zip_bytes"] = out.stat().st_size
            result["reads"] = counts

            with zipfile.ZipFile(out) as z:
                expected_names = [r[0].rstrip("/") + "/" if r[1] == 1 else r[0] for r in rd.files]
                assert z.namelist() == expected_names, (z.namelist(), expected_names)
                meta = []
                for rel, kind, mode, mt, size, h, storage in rd.files:
                    name = rel.rstrip("/") + "/" if kind == 1 else rel
                    info = z.getinfo(name)
                    assert info.create_system == 3
                    assert (info.external_attr >> 16) == (({1:stat.S_IFDIR, 2:stat.S_IFLNK}.get(kind, stat.S_IFREG)|mode)&0xffff), (rel, info.external_attr, kind, mode)
                    ztime, zdate = rd._zip_dos_time(mt)
                    expected_date=(1980+(zdate>>9),(zdate>>5)&15,zdate&31,ztime>>11,(ztime>>5)&63,(ztime&31)*2)
                    assert info.date_time == expected_date, (name,info.date_time,expected_date)
                    if kind == 1:
                        assert info.file_size == 0
                        continue
                    assert info.file_size == size, (name, info.file_size, size)
                    payload_hash=hashlib.sha256()
                    with z.open(name) as zh:
                        while True:
                            chunk = zh.read(MIB)
                            if not chunk:break
                            payload_hash.update(chunk)
                    assert payload_hash.digest() == (bytes(h) if h is not None else rd.file_sha256(rel)), name
                    assert info.compress_type == zipfile.ZIP_DEFLATED, name
                    meta.append({"name": name, "bytes": size, "sha256": payload_hash.hexdigest()})
                result["members"] = meta

            # Repeated exports use the same Reader and do not mutate original CMPCT.
            lv1 = Path(td) / "level1.zip"
            lv9 = Path(td) / "level9.zip"
            rd._export_zip_compat_stream(lv1, level=1, chunk_bytes=256*1024)
            rd._export_zip_compat_stream(lv9, level=9, chunk_bytes=256*1024)
            with zipfile.ZipFile(lv1) as one, zipfile.ZipFile(lv9) as nine:
                s1 = one.getinfo("compressible.txt").compress_size
                s9 = nine.getinfo("compressible.txt").compress_size
                assert s9 <= s1, (s1, s9)
                result["compression_level_control"] = {"level1_compressed_bytes": s1, "level9_compressed_bytes": s9}

            # Corruption refusal must survive streaming, including in the middle of a member.
            mutated = {"done":False}
            def altered(name, start, length):
                raw = old_range(name,start,length)
                if name == "data.bin" and not mutated["done"] and raw:
                    mutated["done"] = True
                    raw = bytes([raw[0] ^ 1]) + raw[1:]
                return raw
            rd.read_range = altered
            try:
                rd._export_zip_compat_stream(Path(td)/"corrupt.zip", level=6)
                raise AssertionError("mutated source was accepted")
            except IOError as exc:
                assert "SHA-256 failure" in str(exc), repr(exc)
            assert mutated["done"]
            result["adversarial_sha_corruption_refused"] = True
            rd.read_range = old_range
            rd.read = old_read
        assert SHA(archive) == archive_sha_before
        result["source_archive_unchanged"] = True
        result["verdict"] = "SMALL_REAL_SOURCE_STREAMING_MECHANISM_PASS_NOT_GIANT_ZIP64_CREDIT"
        return result


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    try:
        v=run()
        rc=0
    except Exception as e:
        v={"schema":"cmpct-o193-streaming-v1","verdict":"FAIL","exception":type(e).__name__,
           "error":str(e),"traceback":traceback.format_exc()[-6000:]}
        rc=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(v,sort_keys=True))
    raise SystemExit(rc)
if __name__=="__main__":
    main()
