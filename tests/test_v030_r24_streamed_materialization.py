from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.v030_release_locality import RELEASE_LOCALITY_MARKER
from cmpct.v030_release_materialization import StreamedBuilder, _ORIGINAL_BUILD


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
    # Materialization is an internal execution strategy, not a new Builder API surface.
    assert b==a


def test_release_guard_is_explicitly_scoped(tmp_path: Path):
    src=_tree(tmp_path); ordinary=tmp_path/'ordinary.cmpct'; release=tmp_path/'release.cmpct'
    kwargs=dict(workers=2,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    normal=Builder(src,**kwargs)
    normal_stats=normal.build(ordinary)
    owned=Builder(src,**kwargs); setattr(owned,RELEASE_LOCALITY_MARKER,True)
    owned_stats=owned.build(release)
    assert owned_stats==normal_stats
    assert release.read_bytes()==ordinary.read_bytes()


def test_encode_failure_after_consumption_publishes_no_archive(tmp_path: Path, monkeypatch):
    src=_tree(tmp_path); out=tmp_path/'must-not-exist.cmpct'
    builder=StreamedBuilder(src,workers=1,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    original=builder._encode_candidate; calls=0

    def fail_after_one(h,c):
        nonlocal calls
        calls+=1
        if calls==2:
            raise RuntimeError('deterministic encode failure')
        return original(h,c)

    monkeypatch.setattr(builder,'_encode_candidate',fail_after_one)
    with pytest.raises(RuntimeError,match='deterministic encode failure'):
        builder.build(out)
    assert calls==2
    assert not out.exists()


def test_missing_output_parent_matches_historical_failure(tmp_path: Path):
    src=_tree(tmp_path)
    kwargs=dict(workers=1,reproducible=True,reproducible_epoch_ns=1_700_000_000_000_000_000)
    with pytest.raises(FileNotFoundError):
        _ORIGINAL_BUILD(Builder(src,**kwargs),tmp_path/'missing-base'/'x.cmpct')
    with pytest.raises(FileNotFoundError):
        StreamedBuilder(src,**kwargs).build(tmp_path/'missing-streamed'/'x.cmpct')
