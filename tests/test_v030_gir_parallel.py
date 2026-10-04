from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_gir_parallel as parallel
from experiments import entropygraph_v030_gir_rehab as rehab


def _rows(count: int) -> bytes:
    return (
        "\n".join(
            f"2026-08-17T15:{index % 60:02d}:00Z level=INFO worker={index % 32:02d} "
            f"tenant=T{index % 380:04d} route=/api/jobs latency={8 + index % 820} request={index:012x}"
            for index in range(count)
        )
        + "\n"
    ).encode()


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "structured.log").write_bytes(_rows(900))
    (source / "opaque.bin").write_bytes(bytes((index * 73 + 19) & 255 for index in range(30_000)))
    return source


def test_parallel_scheduler_matches_sequential_rehab_complete_bytes(
    tmp_path: Path, monkeypatch
) -> None:
    source = _source(tmp_path)
    sequential = tmp_path / "sequential.cmpct"
    concurrent = tmp_path / "parallel.cmpct"

    sequential_stats = rehab.gir.build(source, sequential)

    real_replace = parallel.os.replace
    publications: list[tuple[Path, Path]] = []

    def observed_replace(src, dst):
        publications.append((Path(src), Path(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(parallel.os, "replace", observed_replace)
    parallel_stats = parallel.build(source, concurrent)

    # Footnote: equality of size is not enough. Scheduling and zero-copy publication are admissible only when
    # the exact fallback winner—including framing, metadata, payloads and recovery copy—is byte-identical.
    assert concurrent.read_bytes() == sequential.read_bytes()
    assert parallel_stats["archive_sha256"] == parallel._sha256(sequential)
    assert parallel_stats["selected"] == sequential_stats["selected"]
    assert parallel_stats["archive_bytes"] == sequential_stats["archive_bytes"]
    assert parallel_stats["v029_bytes"] == sequential_stats["v029_bytes"]
    assert parallel_stats["gir_graph_bytes"] == sequential_stats["gir_graph_bytes"]
    assert parallel_stats["saving_vs_v029_bytes"] == sequential_stats["saving_vs_v029_bytes"]
    assert parallel_stats["scheduler_mode"] == "parallel-independent-complete-artifacts"
    assert parallel_stats["publication_mode"] == "same-filesystem-os.replace"
    assert parallel.strong_verify(concurrent)["ok"] is True

    assert len(publications) == 1
    published_from, published_to = publications[0]
    assert published_to == concurrent
    assert published_from.parent.parent == concurrent.parent
    assert not list(tmp_path.glob(f".{concurrent.name}.gir-parallel-*"))


def test_parallel_worker_rejects_unknown_engine_without_creating_archive(tmp_path: Path) -> None:
    source = _source(tmp_path)
    out = tmp_path / "never.cmpct"

    class CaptureQueue:
        def __init__(self) -> None:
            self.value = None

        def put(self, value) -> None:
            self.value = value

    queue = CaptureQueue()
    parallel._worker("unknown", str(source), str(out), queue)
    assert queue.value is not None
    assert queue.value["ok"] is False
    assert "unknown GIR parallel worker kind" in queue.value["error"]
    assert not out.exists()
