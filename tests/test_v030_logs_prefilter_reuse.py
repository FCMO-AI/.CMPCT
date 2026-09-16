from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS


def test_positive_structural_proof_skips_duplicate_prefilter(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    out = tmp_path / "out.cmpct"

    def unexpected_scan(_root: Path) -> dict:
        raise AssertionError("positive shared proof must not trigger a second source prefilter")

    def fake_candidates(_root: Path, temp: Path):
        r24 = temp / "r24.cmpct"
        logs = temp / "logs.cmpct"
        r24.write_bytes(b"r24")
        logs.write_bytes(b"logs")
        return ({"archive_bytes": 3}, {"archive_bytes": 4}, r24, logs, 0.0)

    monkeypatch.setattr(LOGS, "logs_source_prefilter", unexpected_scan)
    monkeypatch.setattr(LOGS, "_parallel_candidates", fake_candidates)
    monkeypatch.setattr(LOGS, "_admission", lambda _r24, _logs: (False, {}))

    result = LOGS._build_logs_terminal_if_eligible(
        root,
        out,
        proven_positive_prefilter={"eligible": True, "sidecar_pairs": LOGS.MIN_SIDECAR_PAIRS},
    )
    assert result is None
    assert not out.exists()


def test_invalid_structural_proof_falls_back_to_local_prefilter(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    out = tmp_path / "out.cmpct"
    calls = []

    def local_scan(seen_root: Path) -> dict:
        calls.append(Path(seen_root))
        return {"eligible": False, "sidecar_pairs": 0}

    monkeypatch.setattr(LOGS, "logs_source_prefilter", local_scan)
    result = LOGS._build_logs_terminal_if_eligible(
        root,
        out,
        proven_positive_prefilter={"eligible": True, "sidecar_pairs": LOGS.MIN_SIDECAR_PAIRS - 1},
    )
    assert result is None
    assert calls == [root]
    assert not out.exists()


def test_public_frontdoor_passes_shared_positive_logs_proof(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    out = tmp_path / "out.cmpct"
    proof = {
        "eligible": True,
        "sidecar_pairs": PRODUCT._LOGS_PROMOTED.MIN_SIDECAR_PAIRS,
        "source": "shared-frontdoor-preflight-v1",
    }
    seen: list[dict | None] = []

    monkeypatch.setattr(
        PRODUCT,
        "_shared_frontdoor_preflight",
        lambda _root: {
            "metadata_error": False,
            "logs_eligible": True,
            "logs_prefilter_proof": proof,
        },
    )

    def fake_terminal(_root: Path, _out: Path, *, proven_positive_prefilter=None):
        seen.append(proven_positive_prefilter)
        return {"selected": "logs-inverse"}

    monkeypatch.setattr(PRODUCT._LOGS_PROMOTED, "_build_logs_terminal_if_eligible", fake_terminal)

    result = PRODUCT.build(root, out)
    assert result == {"selected": "logs-inverse"}
    assert seen == [proof]


def test_public_frontdoor_metadata_error_does_not_trust_shared_logs_proof(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    out = tmp_path / "out.cmpct"
    seen: list[dict | None] = []

    monkeypatch.setattr(
        PRODUCT,
        "_shared_frontdoor_preflight",
        lambda _root: {
            "metadata_error": True,
            "logs_eligible": False,
            "shape": None,
            "media_files": None,
        },
    )

    def fake_terminal(_root: Path, _out: Path, *, proven_positive_prefilter=None):
        seen.append(proven_positive_prefilter)
        return {"selected": "logs-inverse"}

    monkeypatch.setattr(PRODUCT._LOGS_PROMOTED, "_build_logs_terminal_if_eligible", fake_terminal)

    result = PRODUCT.build(root, out)
    assert result == {"selected": "logs-inverse"}
    assert seen == [None]
