"""O90: real installed-product output-kind admission, with a hard child watchdog."""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import pytest
from cmpct.core import Builder, CMPCT

POSIX = pytest.mark.skipif(os.name == "nt", reason="POSIX FIFO and symlink court")


def source_tree(tmp_path):
    source=tmp_path/"source"
    source.mkdir()
    data=hashlib.shake_256(b"o90-out-kind").digest(512)
    (source/"data.bin").write_bytes(data)
    return source,data


def run_builder(source,out):
    program="import sys; from pathlib import Path; from cmpct.core import Builder; Builder(Path(sys.argv[1]),workers=1).build(Path(sys.argv[2]))"
    return subprocess.run([sys.executable,"-c",program,str(source),str(out)],
                          text=True,capture_output=True,timeout=8,cwd=str(source.parent))


def reject(source,out,message):
    result=run_builder(source,out)
    assert result.returncode!=0, result.stdout
    assert "ValueError" in result.stderr and message in result.stderr, result.stderr


def test_o90_existing_directory_rejected_before_scan(tmp_path):
    source,data=source_tree(tmp_path)
    out=tmp_path/"output"
    out.mkdir()
    builder=Builder(source,workers=1)
    builder.scan=lambda: (_ for _ in ()).throw(AssertionError("scan must not run"))
    with pytest.raises(ValueError,match="archive output must be a regular file"):
        builder.build(out)
    assert list(out.iterdir())==[]


def test_o90_new_output_allowed(tmp_path):
    source,data=source_tree(tmp_path)
    out=tmp_path/"new.cmpct"
    result=run_builder(source,out)
    assert result.returncode==0,result.stderr
    with CMPCT(out) as archive:
        archive.verify()
        assert archive.read("data.bin")==data


def test_o90_existing_regular_allowed(tmp_path):
    source,data=source_tree(tmp_path)
    out=tmp_path/"existing.cmpct"
    out.write_bytes(b"prior")
    result=run_builder(source,out)
    assert result.returncode==0,result.stderr
    with CMPCT(out) as archive:
        archive.verify()
        assert archive.read("data.bin")==data


def test_o90_in_tree_output_still_rejected(tmp_path):
    source,data=source_tree(tmp_path)
    out=source/"archive.cmpct"
    reject(source,out,"archive output must be outside the source root")
    assert not out.exists()


def test_o90_source_hardlink_still_rejected(tmp_path):
    source,data=source_tree(tmp_path)
    out=tmp_path/"alias.cmpct"
    os.link(source/"data.bin",out)
    result=run_builder(source,out)
    assert result.returncode!=0,result.stdout
    assert out.read_bytes()==data and (source/"data.bin").read_bytes()==data


@POSIX
def test_o90_unconnected_fifo_rejected_without_block(tmp_path):
    source,data=source_tree(tmp_path)
    out=tmp_path/"fifo.cmpct"
    os.mkfifo(out)
    reject(source,out,"archive output must be a regular file")
    assert stat.S_ISFIFO(os.stat(out).st_mode)
    print("O90_REAL_PRODUCT_FIFO_REJECTION=PASS",flush=True)


@POSIX
def test_o90_symlink_fifo_rejected_without_block(tmp_path):
    source,data=source_tree(tmp_path)
    target=tmp_path/"fifo-target"
    os.mkfifo(target)
    out=tmp_path/"fifo-link.cmpct"
    out.symlink_to(target)
    reject(source,out,"archive output must be a regular file")
    assert out.is_symlink()
    print("O90_REAL_PRODUCT_SYMLINK_FIFO_REJECTION=PASS",flush=True)


@POSIX
def test_o90_symlink_regular_preserved(tmp_path):
    source,data=source_tree(tmp_path)
    target=tmp_path/"target.cmpct"
    target.write_bytes(b"prior")
    out=tmp_path/"link.cmpct"
    out.symlink_to(target)
    result=run_builder(source,out)
    assert result.returncode==0,result.stderr
    assert out.is_symlink()
    with CMPCT(target) as archive:
        archive.verify()
        assert archive.read("data.bin")==data


@POSIX
def test_o90_dangling_symlink_rejected(tmp_path):
    source,data=source_tree(tmp_path)
    target=tmp_path/"missing"
    out=tmp_path/"dangling.cmpct"
    out.symlink_to(target)
    reject(source,out,"archive output must not be a dangling symlink")
    assert out.is_symlink() and not target.exists()
