from pathlib import Path

from experiments.entropygraph_v029_parallel_portfolio import build_parallel
from experiments import entropygraph_v029_mosaic as mosaic


def test_parallel_scheduler_preserves_exact_selected_archive(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.bin").write_bytes((b"alpha-beta-gamma\n" * 7000) + b"tail-a")
    (root / "b.bin").write_bytes((b"alpha-beta-delta\n" * 7000) + b"tail-b")

    sequential = tmp_path / "sequential.cmpct"
    parallel = tmp_path / "parallel.cmpct"
    seq = mosaic.build(root, sequential)
    par = build_parallel(root, parallel)

    assert par["selected"] == seq["selected"]
    assert par["archive_bytes"] == seq["archive_bytes"]
    assert parallel.read_bytes() == sequential.read_bytes()
