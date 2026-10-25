"""O90: static destination-kind admission regression."""
from pathlib import Path
import os
import pytest
from cmpct.core import Builder

def test_o90_existing_directory_rejected_before_scan(tmp_path):
    source=tmp_path/"source"
    source.mkdir()
    (source/"a.txt").write_bytes(b"hello")
    out=tmp_path/"output"
    out.mkdir()
    builder=Builder(source, workers=1)
    builder.scan=lambda: (_ for _ in ()).throw(AssertionError("scan must not run"))
    with pytest.raises(ValueError, match="archive output must be a regular file"):
        builder.build(out)

def test_o90_nonexistent_output_allowed(tmp_path):
    source=tmp_path/"source"
    source.mkdir()
    (source/"a.txt").write_bytes(b"hello")
    out=tmp_path/"output.cmpct"
    Builder(source,workers=1).build(out)
    assert out.is_file()
