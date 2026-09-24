from __future__ import annotations
"""Optional creator-side native Deflate validation cache for the bounded hidden-ZIP lane."""
import ctypes,hashlib,io,os,struct,zipfile

class _Job(ctypes.Structure):
    _fields_=[('stream_offset',ctypes.c_size_t),('stream_len',ctypes.c_size_t),('output_offset',ctypes.c_size_t),('output_len',ctypes.c_size_t),('crc32',ctypes.c_uint32)]

def _payload_range(raw:bytes,info:zipfile.ZipInfo)->tuple[int,int]:
    off=int(info.header_offset)
    if off<0 or off+30>len(raw) or raw[off:off+4]!=b'PK\x03\x04':raise zipfile.BadZipFile('invalid local header')
    nl,xl=struct.unpack_from('<HH',raw,off+26);start=off+30+nl+xl;end=start+int(info.compress_size)
    if end>len(raw):raise zipfile.BadZipFile('compressed payload exceeds source')
    return start,end

def native_validated_deflates(raw:bytes)->dict|None:
    """Return the existing validated-deflate cache shape, or None when native support is unavailable.

    The library path is explicit during the bounded experiment. Absence is a safe fallback, not a
    correctness bypass. Exact stream consumption/length/CRC are enforced natively; this wrapper
    independently keys results by the same exact-stream SHA used by transactional recipe staging.
    """
    path=os.environ.get('CMPCT_HIDDEN_ZIP_BATCH_LIB')
    if not path:return None
    try:lib=ctypes.CDLL(path)
    except OSError:return None
    fn=lib.cmpct_hidden_zip_validate_deflate_batch;fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(_Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];fn.restype=ctypes.c_int
    specs=[];keys=[];offset=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED:continue
            start,end=_payload_range(raw,info);stream=raw[start:end];key=(int(info.compress_size),int(info.file_size),int(info.CRC),hashlib.sha256(stream).digest());keys.append((key,offset,int(info.file_size)));specs.append(_Job(start,end-start,offset,int(info.file_size),int(info.CRC)));offset+=int(info.file_size)
    if not specs:return {}
    jobs=(_Job*len(specs))(*specs);src=ctypes.c_char_p(raw);out=(ctypes.c_ubyte*offset)();hashes=(ctypes.c_ubyte*(32*len(specs)))()
    rc=fn(ctypes.cast(src,ctypes.c_void_p),len(raw),jobs,len(specs),out,offset,hashes,len(hashes))
    if rc!=0:raise zipfile.BadZipFile(f'native Deflate validation rejected candidate ({rc})')
    material=bytes(out);return {key:material[off:off+ln] for key,off,ln in keys}
