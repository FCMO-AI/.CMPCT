"""Third-root physical revision-24 artifact audit for J24I05.

Independent of CMPCT Builder, Reader, source tests and research referee.
Requires python-msgpack and system libzstd; does not import CMPCT.
Usage: python research/j24i05_external_wire_audit.py evidence.zip
"""
import sys,zipfile,json,hashlib,struct,ctypes,ctypes.util,zlib
from pathlib import Path
import msgpack

HDR=struct.Struct("<8sHHQQQ32s")
FTR=struct.Struct("<8sBBBBQQQ32s")
BHDR=struct.Struct("<4sBBHQQII32s")
lib=ctypes.CDLL(ctypes.util.find_library("zstd"))
lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
lib.ZSTD_decompress.restype=ctypes.c_size_t
lib.ZSTD_isError.argtypes=[ctypes.c_size_t]
lib.ZSTD_isError.restype=ctypes.c_uint

def digest(data):
    return hashlib.sha256(data).hexdigest()

def zstd_unframe(data,uncompressed):
    src=ctypes.create_string_buffer(data,len(data))
    dest=ctypes.create_string_buffer(uncompressed)
    size=lib.ZSTD_decompress(dest,uncompressed,src,len(data))
    assert not lib.ZSTD_isError(size) and size==uncompressed,("invalid zstd frame",size)
    return dest.raw[:size]

def physical(wire):
    magic,rev,flags,ic,iu,span,idhash=HDR.unpack_from(wire)
    assert magic==b"CMPCT24\0" and rev==24
    record_start=HDR.size+ic
    assert len(wire)==record_start+span+ic+FTR.size, "unexplained trailing bytes"
    encoded=wire[HDR.size:record_start]
    assert encoded==wire[record_start+span:record_start+span+ic]
    index_bytes=zstd_unframe(encoded,iu)
    assert bytes.fromhex(digest(index_bytes))==idhash
    foot=FTR.unpack_from(wire,len(wire)-FTR.size)
    assert foot[0]==b"CMPTF24\0" and foot[5]==ic and foot[6]==iu and foot[7]==0 and foot[8]==idhash
    index=msgpack.unpackb(index_bytes,raw=False)
    assert index["v"]==24
    blobs=[]
    for off,usize,csize,codec,meta in index["blobs"]:
        frame=wire[record_start+off:]
        mark,actual_codec,flags,res,actual_us,actual_cs,actual_meta,crc,rawhash=BHDR.unpack_from(frame)
        assert mark==b"CMA4" and (actual_codec,actual_us,actual_cs,actual_meta)==(codec,usize,csize,meta)
        payload=frame[BHDR.size+meta:BHDR.size+meta+csize]
        assert len(payload)==csize
        if codec==0: raw=payload
        elif codec==1: raw=zstd_unframe(payload,usize)
        else: raise AssertionError(("unhandled codec in detached RAW/Zstd audit",codec))
        assert len(raw)==usize and bytes.fromhex(digest(raw))==rawhash
        assert zlib.crc32(raw)&0xffffffff==crc
        blobs.append(raw)
    files={row[0]:row for row in index["files"]}
    assert files["owner.bin"][1]==0
    target=None
    if "link" in files:
        row=files["link"]
        assert row[1]==2 and row[6][0]==0
        target=blobs[row[6][1]].decode("utf-8")
        assert len(target.encode())==row[4]
    return {"bytes":len(wire),"sha256":digest(wire),"files":len(files),"blobs":len(blobs),
            "target":target,"logical_bytes":sum(row[4] for row in files.values() if row[1]!=1)}

def verify(artifact):
    with zipfile.ZipFile(artifact) as z:
        names=z.namelist()
        court=json.loads(z.read("cases.json"))
        archives={n:physical(z.read(n)) for n in names if n.startswith("archives/") and n.endswith(".cmpct")}
        errors=[]
        for case in court["cases"]:
            name=case["case"]
            source="archives/"+name+"-source.cmpct"
            output="archives/"+name+"-compacted.cmpct"
            if source not in archives:
                errors.append("missing source "+name)
                continue
            s=archives[source]
            if s["sha256"]!=case["source_sha256"] or s["bytes"]!=case["source_bytes"]:
                errors.append("physical source mismatch "+name)
            if s["target"]!=case["target"]: errors.append("physical symlink target mismatch "+name)
            if case["expected_rejection"]:
                if output in archives or case["output_sha256"] is not None:
                    errors.append("failure published an output "+name)
            else:
                if output not in archives:
                    errors.append("missing positive output "+name)
                    continue
                d=archives[output]
                if d["sha256"]!=case["output_sha256"] or d["target"]!=s["target"]:
                    errors.append("output or target mismatch "+name)
        if len(archives)!=6: errors.append("expected six real source/output archives")
        return {"schema":"j24i05-independent-wire-audit-v1",
                "artifact_zip_sha256":digest(Path(artifact).read_bytes()),
                "archives":archives,"physical_archive_count":len(archives),
                "errors":errors,"status":"PASS" if not errors else "FAIL",
                "limits":"Physical provenance only; does not repeat installed Builder/extractall or verify external sentinel."}

if __name__=="__main__":
    result=verify(sys.argv[1])
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["errors"]: sys.exit(1)
