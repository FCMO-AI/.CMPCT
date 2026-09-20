from pathlib import Path

from cmpct.builder import Builder
from experiments.v030_r24_streamed_materialization import StreamedBuilder


def _tree(root: Path) -> Path:
    src=root/'src'; src.mkdir()
    (src/'alpha.txt').write_text('alpha beta gamma\n'*4000)
    (src/'binary.bin').write_bytes(bytes(range(256))*800)
    nested=src/'nested'; nested.mkdir(); (nested/'same.txt').write_text('alpha beta gamma\n'*4000)
    return src


def test_streamed_materialization_is_byte_identical(tmp_path: Path):
    src=_tree(tmp_path); base=tmp_path/'base.cmpct'; streamed=tmp_path/'streamed.cmpct'
    kwargs=dict(workers=4,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    a=Builder(src,**kwargs).build(base)
    b=StreamedBuilder(src,**kwargs).build(streamed)
    assert streamed.read_bytes()==base.read_bytes()
    assert b['bytes']==a['bytes']
    assert b['data_bytes']==a['data_bytes']
    assert b['materialization']=='bounded-record-spool-v1'
