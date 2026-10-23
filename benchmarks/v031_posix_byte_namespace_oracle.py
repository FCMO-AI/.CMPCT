#!/usr/bin/env python3
"""Detached r25 POSIX namespace oracle. NOT a CMPCT product implementation.

Compare version-gated raw byte-key MessagePack against reversible ASCII spelling.
Never admit either wire grammar into r24, whose native parser requires UTF-8 str.
"""
import base64
import hashlib
import json
import os
import random
import tempfile
import zlib

import msgpack

TAG="~Z"

def admissible(raw, kind):
    if kind not in ("segment","xattr") or not isinstance(raw,bytes):
        raise ValueError("unknown byte field")
    if not raw or b"\0" in raw or len(raw)>255:
        raise ValueError("invalid field")
    if kind=="segment" and (b"/" in raw or raw in (b".",b"..")):
        raise ValueError("invalid path segment")

def b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def un64(wire):
    if not wire or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in wire):
        raise ValueError("noncanonical alphabet")
    try: raw=base64.urlsafe_b64decode(wire+"="*((-len(wire))%4))
    except Exception as exc: raise ValueError("invalid base64") from exc
    if b64(raw)!=wire: raise ValueError("noncanonical base64")
    return raw

def text_wire(raw, kind="segment"):
    admissible(raw,kind)
    try: value=raw.decode("utf-8")
    except UnicodeDecodeError: return "~Z1_"+b64(raw)
    if value.startswith(TAG): return "~Z0_"+b64(raw)
    if kind=="segment" and "\\" in value: return "~Z1_"+b64(raw)
    return value

def text_unwire(wire, kind="segment"):
    if not isinstance(wire,str): raise ValueError("expected str")
    if wire.startswith("~Z0_"):
        raw=un64(wire[4:]);admissible(raw,kind)
        if not raw.decode("utf-8").startswith(TAG): raise ValueError("redundant text escape")
    elif wire.startswith("~Z1_"):
        raw=un64(wire[4:]);admissible(raw,kind)
        try: decoded=raw.decode("utf-8")
        except UnicodeDecodeError: decoded=None
        if decoded is not None and not (kind=="segment" and "\\" in decoded):
            raise ValueError("redundant raw escape")
    elif wire.startswith(TAG):
        raise ValueError("unknown tag")
    else:
        raw=wire.encode("utf-8");admissible(raw,kind)
    if text_wire(raw,kind)!=wire: raise ValueError("noncanonical wire")
    return raw

def bytes_wire(raw,kind="segment"):
    admissible(raw,kind)
    try: text=raw.decode("utf-8")
    except UnicodeDecodeError: return [1,raw]
    if kind=="segment" and "\\" in text: return [1,raw]
    return text

def bytes_unwire(wire,kind="segment"):
    if isinstance(wire,str): raw=wire.encode("utf-8")
    elif isinstance(wire,list) and len(wire)==2 and wire[0]==1 and isinstance(wire[1],bytes):
        raw=wire[1]
    else: raise ValueError("unknown binary variant")
    admissible(raw,kind)
    if bytes_wire(raw,kind)!=wire: raise ValueError("noncanonical binary variant")
    return raw

def physical_host_court():
    if os.name!="posix": return {"status":"SKIP","reason":"POSIX-only physical bytes"}
    with tempfile.TemporaryDirectory() as directory:
        root=os.fsencode(directory)
        names=[b"file-\xff",b"file-\xfe",b"caf\xc3\xa9",b"caf\xe9",b"~Z1__w",b"~z1__w",b"a\\b",b"A",b"a"]
        for name in names:
            with open(root+b"/"+name,"wb") as dest: dest.write(b"body:"+name)
        os.mkdir(root+b"/dir-\xff")
        with open(root+b"/dir-\xff/child-\xfe","wb") as dest: dest.write(b"nested")
        os.link(root+b"/file-\xff",root+b"/hard-\xff")
        os.symlink(b"./file-\xff",root+b"/sym-\xff")
        listed=sorted(os.listdir(root))
        assert [text_unwire(text_wire(n)) for n in listed]==listed
        assert [bytes_unwire(bytes_wire(n)) for n in listed]==listed
        assert os.stat(root+b"/hard-\xff").st_ino==os.stat(root+b"/file-\xff").st_ino
        assert os.readlink(root+b"/sym-\xff")==b"./file-\xff"
        xa="UNAVAILABLE"
        try:
            for key in (b"user.invalid-\xff",b"user.slash/name",b"user.path/../fragment",b"user.back\\slash"):
                os.setxattr(root+b"/file-\xff",key,key)
                assert text_unwire(text_wire(key,"xattr"),"xattr")==key
                assert bytes_unwire(bytes_wire(key,"xattr"),"xattr")==key
                assert os.getxattr(root+b"/file-\xff",key)==key
            xa="PASS"
        except OSError as e:xa="UNAVAILABLE:"+str(e.errno)
        return {"status":"PASS","physical_names":len(listed),"hardlink":"PASS","symlink":"PASS","xattrs":xa}

def court():
    rng=random.Random(559)
    fixed=[b"file-\xff",b"file-\xfe",b"caf\xc3\xa9",b"caf\xe9",b"~Z1__w",b"~z1__w",b"~Z",b"~Z0_cA",b"a\\b",b"A",b"a",b"CON",b"con",b"a:b"]
    for _ in range(5000):
        raw=bytes(rng.randint(1,255) for i in range(rng.randint(1,80)))
        if b"/" not in raw and b"\0" not in raw and raw not in (b".",b".."): fixed.append(raw)
    corpus=sorted(set(fixed))
    escaped=[text_wire(name) for name in corpus]
    binary=[bytes_wire(name) for name in corpus]
    assert len(set(escaped))==len(corpus)
    assert len({msgpack.packb(w,use_bin_type=True) for w in binary})==len(corpus)
    assert [text_unwire(w) for w in escaped]==corpus
    assert [bytes_unwire(w) for w in binary]==corpus
    assert text_unwire(text_wire(b"dir-\xff"))==b"dir-\xff"
    assert text_unwire(text_wire(b"child-\xfe"))==b"child-\xfe"
    rejected=0
    for wire in ("~Z1_","~Z1_!","~Z1_YQ==","~Z1_YQ","~Z0_YQ","~Z0_","~Z2_Yg","a\\b","/a",".","..",""):
        try: text_unwire(wire)
        except ValueError: rejected+=1
        else: raise AssertionError("bad spelling accepted "+repr(wire))
    for wire in ([1,b"plain"],[1,b"~Z"],[2,b"raw"],[],[1,b"/"],[1,b".."]):
        try: bytes_unwire(wire)
        except ValueError: rejected+=1
        else: raise AssertionError("bad binary variant accepted "+repr(wire))
    pa=msgpack.packb(escaped,use_bin_type=True)
    pb=msgpack.packb(binary,use_bin_type=True)
    # Synthetic near-PATH_MAX path: valid as independent <=255-byte components.
    longparts=[b"\xff"*255]*16
    raw_len=16*255+15
    escaped_len=len("/".join(text_wire(x) for x in longparts).encode("ascii"))
    # Distinct POSIX names may collide on a case-insensitive target platform.
    pair=[text_wire(b"\xff"),text_wire(b"~z1__w")]
    assert pair[0]!=pair[1] and pair[0].casefold()==pair[1].casefold()
    return {"status":"PASS","tier":"independent structural oracle only; NOT full CMPCT",
      "source_sha256":hashlib.sha256(msgpack.packb(corpus,use_bin_type=True)).hexdigest(),
      "names":len(corpus),"host":physical_host_court(),
      "noncanonical_rejected":rejected,"r24_native_path_utf8_only":True,
      "escaped_msgpack_bytes":len(pa),"binary_msgpack_bytes":len(pb),
      "escaped_deflate9_bytes":len(zlib.compress(pa,9)),"binary_deflate9_bytes":len(zlib.compress(pb,9)),
      "near_limit_raw_path_bytes":raw_len,"near_limit_escaped_wire_bytes":escaped_len,
      "casefold_collision":pair,"xattr_slash_is_legal_on_linux":"physical host court",
      "decision":"Neither grammar is promotable to r24. Explicit version-gated byte namespace and separate path/xattr semantics required.",
      "unmeasured":["native parser changes","full archive","Windows","read_range","recovery","CPU/RSS","format25 compatibility"]}

if __name__=="__main__":
    print(json.dumps(court(),sort_keys=True,indent=2))
