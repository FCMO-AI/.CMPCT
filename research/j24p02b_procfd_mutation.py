#!/usr/bin/env python3
"""J24P02b: hostile same-UID procfd mutation of an otherwise unnamed ZIP inode.

Second, separately preregistered negative test. Stronger attacker than a
directory-entry writer: can access /proc/<PID>/fd/<N> of a same-UID process.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import zipfile

import j24p02_fd_noclobber_oracle as base


def forged_zip():
    hostile = bytes(b ^ 0xA5 for b in base.PAYLOAD)
    assert hostile != base.PAYLOAD and len(hostile) == len(base.PAYLOAD)
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w") as z:
        zi = zipfile.ZipInfo("raw.bin", date_time=(2020, 1, 2, 3, 4, 6))
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.create_system = 3
        zi.external_attr = 0o100644 << 16
        z.writestr(zi, hostile)
    raw = buff.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw), "r") as z:
        assert z.namelist() == ["raw.bin"] and z.testzip() is None
        assert z.read("raw.bin") == hostile
    return hostile, raw


def main():
    if platform.system() != "Linux":
        raise SystemExit("J24P02B_UNSUPPORTED: Linux-only procfs")
    with tempfile.TemporaryDirectory(prefix="cmpct-j24p02b-") as temp:
        directory = Path(temp)
        target = directory / "result.zip"
        fd, original, before = base.unnamed_zip(directory)
        dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            hostile, newraw = forged_zip()
            assert len(hostile) == len(base.PAYLOAD)
            assert not target.exists()
            origsha = base.sha(original)
            assert newraw != original
            # Child process receives only (PID, fd-number, encoded ZIP), never
            # inherits the original descriptor. Its only access route is procfs.
            child_script = """
import os,sys
path='/proc/%s/fd/%s' % (sys.argv[1],sys.argv[2])
raw=bytes.fromhex(sys.argv[3])
try:
    f=os.open(path,os.O_WRONLY|os.O_TRUNC)
except OSError as e:
    print('PROC_FD_UNAVAILABLE:',repr(e),flush=True)
    raise SystemExit(42)
try:
    count=0
    while count<len(raw):
        n=os.write(f,raw[count:])
        if n<=0: raise OSError('short child write')
        count+=n
finally:
    os.close(f)
print('PROC_FD_MUTATED_BYTES='+str(count),flush=True)
"""
            child = subprocess.run([sys.executable, "-c", child_script,
                                    str(os.getpid()), str(fd), newraw.hex()],
                                   close_fds=True, capture_output=True, text=True, timeout=15)
            if child.returncode != 0:
                print("J24P02B_DECISION=UNAVAILABLE_ON_HOST_CHILD_RC_%s" % child.returncode)
                print("J24P02B_CHILD=" + child.stdout + child.stderr)
                return 2  # No false-positive proof.
            assert "PROC_FD_MUTATED_BYTES=" in child.stdout
            now = os.fstat(fd)
            assert (now.st_dev,now.st_ino) == (before.st_dev,before.st_ino)
            os.lseek(fd,0,os.SEEK_SET)
            mutated=os.read(fd,len(newraw)+1)
            assert mutated == newraw
            assert base.sha(mutated) != origsha
            route = base.publish(fd, dfd, target.name)
            published = target.read_bytes()
            current = os.lstat(target)
            assert (current.st_dev,current.st_ino) == (before.st_dev,before.st_ino)
            assert published == newraw
            with zipfile.ZipFile(target) as z:
                assert z.testzip() is None and z.namelist() == ["raw.bin"]
                actual=z.read("raw.bin")
                assert actual==hostile and actual!=base.PAYLOAD
                assert len(actual)==len(base.PAYLOAD)
            print("J24P02B_DECISION=" + json.dumps({
                "classification":"SAME_UID_PROC_FD_CONTENT_MUTATION_CONFIRMED",
                "host":platform.platform(),"uid":os.getuid(),
                "child_inherited_fd":False,"access_via":"/proc/<parent-pid>/fd/<n>",
                "original_zip_sha256":origsha,"published_zip_sha256":base.sha(published),
                "original_inode":before.st_ino,"published_inode":current.st_ino,
                "inode_identical":True,"same_member_name":True,
                "same_logical_size":True,"zip_crc_valid":True,
                "source_content_authentic":False,
                "publish_route":route,
                "scope":"stronger same-UID procfs actor, NOT just directory writer"
            },sort_keys=True),flush=True)
            return 0
        finally:
            os.close(dfd)
            os.close(fd)


if __name__=="__main__":
    raise SystemExit(main())
