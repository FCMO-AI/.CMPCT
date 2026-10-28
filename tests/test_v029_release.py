from pathlib import Path

from experiments import entropygraph_v029_release as release
from experiments import entropygraph_v029_residual_strict as accepted


def test_v029_release_entrypoint_is_exact_attempt5_portfolio(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "a.txt").write_bytes((b"alpha-beta-gamma\n" * 7000) + b"A")
    (root / "b.txt").write_bytes((b"alpha-beta-delta\n" * 7000) + b"B")

    sequential = tmp_path / "accepted.cmpct"
    released = tmp_path / "release.cmpct"
    accepted_stats = accepted.build(root, sequential)
    release_stats = release.build(root, released)

    # Footnote: exact selected bytes are the authority. Matching a high-level selected label would not
    # have caught the earlier stale-scheduler defect, where internally coherent evidence targeted the
    # wrong research portfolio and selected the inherited fallback.
    assert release_stats["release_engine"] == "attempt5-residual-program-packing"
    assert release_stats["canonical_format_revision"] == 24
    assert release_stats["selected"] == accepted_stats["selected"]
    assert released.read_bytes() == sequential.read_bytes()

    restored = tmp_path / "restored"
    release.extract(released, restored)
    assert (restored / "a.txt").read_bytes() == (root / "a.txt").read_bytes()
    assert (restored / "b.txt").read_bytes() == (root / "b.txt").read_bytes()
    release.strong_verify(released)
