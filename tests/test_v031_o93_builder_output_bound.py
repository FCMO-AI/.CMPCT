"""O93: installed Builder output-descriptor custody on exact O90 parent.

The O91 research negative is *not* weakened: here its attack must be refused.
"""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import threading

import pytest
from cmpct.core import Builder, CMPCT


def _tree(tmp_path):
    root=tmp_path/"source"
    root.mkdir()
    data=hashlib.shake_256(b"o93-independent-source").digest(4096)
    leaf=root/"leaf.bin"
    leaf.write_bytes(data)
    assert os.stat(leaf).st_nlink==1
    return root,leaf,data


def _synchronized_pivot(builder, callback):
    scanned=threading.Event()
    swapped=threading.Event()
    problems=[]
    original=builder.scan
    def actor():
        try:
            assert scanned.wait(6), "builder never completed authentic scan"
            callback()
        except BaseException as exc:
            problems.append(exc)
        finally:
            swapped.set()
    def scan():
        original()
        scanned.set()
        assert swapped.wait(6), "attacker failed to reach barrier"
        assert not problems,repr(problems)
    builder.scan=scan
    worker=threading.Thread(target=actor,daemon=True)
    worker.start()
    return worker,problems


def test_o93_fresh_and_existing_output_with_reader(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"output.cmpct"
    for initial in (False,True):
        if initial: out.write_bytes(b"independent-previous-archive")
        result=Builder(root,workers=1,reproducible=True).build(out)
        assert result["bytes"]==out.stat().st_size>0
        assert leaf.read_bytes()==data
        with CMPCT(out) as archive:
            archive.verify()
            assert archive.read("leaf.bin")==data
    print("O93_REGULAR_NEW_EXISTING_READER=PASS",flush=True)


@pytest.mark.skipif(os.name=="nt",reason="POSIX symlink/rename adversarial experiment")
def test_o93_reject_symlink_source_pivot_preserves_one_link_bytes(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"output.cmpct"
    out.write_bytes(b"independent-existing-output")
    pending=tmp_path/"pending-link"
    pending.symlink_to(leaf)
    prev=os.stat(out)
    assert (prev.st_dev,prev.st_ino)!=(leaf.stat().st_dev,leaf.stat().st_ino)
    b=Builder(root,workers=1)
    worker,problems=_synchronized_pivot(b,lambda:os.replace(pending,out))
    try:
        with pytest.raises((ValueError,OSError),match="identity|changed"):
            b.build(out)
    finally:
        worker.join(timeout=6)
    assert not worker.is_alive() and not problems,repr(problems)
    assert out.is_symlink() and out.resolve()==leaf.resolve()
    assert leaf.read_bytes()==data and os.stat(leaf).st_nlink==1
    print("O93_REAL_POSTSCAN_SOURCE_PIVOT_REFUSED=PASS",flush=True)


@pytest.mark.skipif(os.name=="nt",reason="POSIX FIFO unavailable")
def test_o93_postscan_fifo_pivot_does_not_block(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"output.cmpct"
    out.write_bytes(b"independent-existing-output")
    marker=tmp_path/"actor.marker"
    child=r"""
import os,sys,threading
from pathlib import Path
from cmpct.core import Builder
root,out,marker=map(Path,sys.argv[1:4])
fifo=out.parent/"pending-fifo"
os.mkfifo(fifo)
scanned=threading.Event()
swapped=threading.Event()
errors=[]
def actor():
    try:
        assert scanned.wait(5)
        os.replace(fifo,out)
        marker.write_text("FIFO_READY")
    except BaseException as e: errors.append(repr(e))
    finally: swapped.set()
b=Builder(root,workers=1)
original=b.scan
def scan():
    original()
    scanned.set()
    assert swapped.wait(5) and not errors, errors
b.scan=scan
t=threading.Thread(target=actor,daemon=True)
t.start()
try:
    b.build(out)
except (ValueError,OSError) as exc:
    assert marker.read_text()=="FIFO_READY"
    print("O93_FIFO_REFUSED="+type(exc).__name__,flush=True)
else:
    raise AssertionError("unacceptable successful FIFO publication")
"""
    done=subprocess.run([sys.executable,"-c",child,str(root),str(out),str(marker)],
                        cwd=tmp_path,capture_output=True,text=True,timeout=7)
    assert done.returncode==0,(done.returncode,done.stdout,done.stderr)
    assert "O93_FIFO_REFUSED=" in done.stdout,done.stdout
    assert marker.read_text()=="FIFO_READY"
    assert stat.S_ISFIFO(os.stat(out).st_mode)
    assert leaf.read_bytes()==data
    print("O93_REAL_POSTSCAN_FIFO_NONBLOCK=PASS",flush=True)


@pytest.mark.skipif(os.name=="nt",reason="POSIX symlink race oracle")
def test_o93_absent_output_exclusive_create_refuses_late_alias(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"new.cmpct"
    assert not out.exists()
    pending=tmp_path/"pending-link"
    pending.symlink_to(leaf)
    b=Builder(root,workers=1)
    worker,problems=_synchronized_pivot(b,lambda:os.replace(pending,out))
    try:
        with pytest.raises((FileExistsError,OSError)):
            b.build(out)
    finally:
        worker.join(timeout=6)
    assert not worker.is_alive() and not problems
    assert out.is_symlink() and out.resolve()==leaf.resolve()
    assert leaf.read_bytes()==data
    print("O93_ABSENT_PATH_EXCLUSIVE_CREATION=PASS",flush=True)


@pytest.mark.skipif(os.name=="nt",reason="POSIX hardlink/symlink/xattr identity controls")
def test_o93_preserves_existing_inode_hardlinks_symlink_and_xattr(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"existing.cmpct"
    out.write_bytes(b"prior-existing")
    alias=tmp_path/"alias.cmpct"
    os.link(out,alias)
    output_link=tmp_path/"output-link"
    output_link.symlink_to(out)
    before=os.stat(out)
    os.chmod(out,0o640)
    supported=False
    if hasattr(os,"setxattr"):
        try:
            os.setxattr(out,b"user.cmpct_o93",b"retain")
            supported=True
        except OSError:
            pass
    result=Builder(root,workers=1,reproducible=True).build(output_link)
    after=os.stat(out)
    assert (after.st_dev,after.st_ino)==(before.st_dev,before.st_ino)
    assert os.stat(alias).st_ino==after.st_ino
    assert output_link.is_symlink()
    assert alias.read_bytes()==out.read_bytes()
    assert stat.S_IMODE(after.st_mode)==0o640
    if supported:
        assert os.getxattr(out,b"user.cmpct_o93")==b"retain"
    with CMPCT(alias) as archive:
        archive.verify()
        assert archive.read("leaf.bin")==data
    assert result["bytes"]==len(out.read_bytes())
    print("O93_INPLACE_INODE_HARDLINK_XATTR=PASS",flush=True)


@pytest.mark.skipif(os.name=="nt",reason="POSIX read-only permission control")
def test_o93_readonly_output_keeps_original_permission_semantics(tmp_path):
    root,leaf,data=_tree(tmp_path)
    out=tmp_path/"readonly.cmpct"
    original=b"must-not-change"
    out.write_bytes(original)
    out.chmod(0o444)
    try:
        with pytest.raises(PermissionError):
            Builder(root,workers=1).build(out)
        assert out.read_bytes()==original
        assert leaf.read_bytes()==data
    finally:
        out.chmod(0o644)
    print("O93_READONLY_OUTPUT_REFUSED=PASS",flush=True)
