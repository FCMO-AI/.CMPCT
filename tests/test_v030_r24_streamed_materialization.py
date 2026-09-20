from pathlib import Path

from cmpct.builder import Builder
from cmpct.v030_release_materialization import SPOOL_MEMORY_LIMIT, StreamedBuilder, _ORIGINAL_BUILD


def _tree(root: Path) -> Path:
    src=root/'src'; src.mkdir()
    (src/'alpha.txt').write_text('alpha beta gamma\n'*4000)
    (src/'binary.bin').write_bytes(bytes(range(256))*800)
    nested=src/'nested'; nested.mkdir(); (nested/'same.txt').write_text('alpha beta gamma\n'*4000)
    return src


def test_streamed_materialization_is_byte_identical(tmp_path: Path):
    src=_tree(tmp_path); base=tmp_path/'base.cmpct'; streamed=tmp_path/'streamed.cmpct'
    kwargs=dict(workers=4,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    a=_ORIGINAL_BUILD(Builder(src,**kwargs),base)
    b=StreamedBuilder(src,**kwargs).build(streamed)
    assert streamed.read_bytes()==base.read_bytes()
    assert b['bytes']==a['bytes']; assert b['data_bytes']==a['data_bytes']
    assert b['materialization']=='bounded-adaptive-record-spool-v2'
    assert b['spool_memory_limit']==SPOOL_MEMORY_LIMIT==16*1024*1024


def test_release_guard_is_explicitly_scoped(tmp_path: Path):
    src=_tree(tmp_path); ordinary=tmp_path/'ordinary.cmpct'; release=tmp_path/'release.cmpct'
    kwargs=dict(workers=2,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    normal=Builder(src,**kwargs)
    normal_stats=normal.build(ordinary)
    assert 'materialization' not in normal_stats
    owned=Builder(src,**kwargs); owned._v030_release_locality_enabled=True
    owned_stats=owned.build(release)
    assert owned_stats['materialization']=='bounded-adaptive-record-spool-v2'
    assert release.read_bytes()==ordinary.read_bytes()
