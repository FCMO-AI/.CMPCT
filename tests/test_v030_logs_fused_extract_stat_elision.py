import inspect

from experiments import entropygraph_v030_logs_fused_extract as fused


def test_metadata_phase_does_not_restat_every_regular_file():
    source = inspect.getsource(fused._restore_filesystem_metadata)
    assert ".stat(" not in source
    assert "is_file()" in source  # hardlink-owner safety remains intact


def test_extract_checks_write_completion_before_metadata_phase():
    source = inspect.getsource(fused.extract)
    assert "written = target.write_bytes(value)" in source
    assert "written != len(value)" in source
    assert "graph_regular != decoded[\"regular\"]" in source
