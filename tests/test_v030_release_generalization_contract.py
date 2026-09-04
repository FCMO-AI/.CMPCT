from __future__ import annotations

from pathlib import Path

from benchmarks import v030_release_generalization as gate
from benchmarks import v030_release_generalization_canonical as canonical


def test_accepted_v029_row_reconstruction_is_exact() -> None:
    rows = gate._accepted_v029_rows()
    assert len(rows) == 15
    assert sum(row["accepted_v029_bytes"] for row in rows.values()) == 137_499_525
    assert rows[("resemblance_hostile_v1", "01_shifted_versions")]["accepted_v029_bytes"] == 1_723_056
    assert rows[("resemblance_hostile_v1", "03_boundary_churn")]["accepted_v029_bytes"] == 79_876


def test_numeric_revision_floor_does_not_get_easier_on_smaller_v029_substrate() -> None:
    # Footnote: the accepted repair-v6 substrate made v0.29 2,290 B smaller. A naive percentage-only rule would
    # lower the absolute hurdle. The campaign explicitly carries 687,783 B forward, so v0.30 inherits that
    # stricter number rather than reverse-engineering a more convenient threshold from the repaired aggregate.
    assert gate.EXPECTED_V029_TOTAL == 137_499_525
    assert gate.INHERITED_ABSOLUTE_REVISION_FLOOR == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES == 687_783
    assert gate.MIN_RELEASE_SAVING_BYTES >= (gate.EXPECTED_V029_TOTAL + 199) // 200
    assert gate.MIN_IMPROVED_ROWS == 3
    assert gate.MAX_MEMBER_READ_AMP == 8.0


def test_historical_tree_identity_is_independent_of_candidate_product_hash(tmp_path, monkeypatch) -> None:
    # The canonical adapter swaps ``gate.RC`` for the r24/r25 release product only while its run executes. Its
    # user-tree hash intentionally covers a richer semantic domain than the historical v0.28/v0.29 identity.
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "payload.bin").write_bytes(b"cmpct-v030-dual-tree-domain\x00\xff")
    historical = gate._historical_treehash(tmp_path)

    monkeypatch.setattr(canonical.CANON, "treehash", lambda _root: "canonical-user-tree-domain")

    assert gate._historical_treehash(tmp_path) == historical
    assert canonical.CANON.treehash(tmp_path) == "canonical-user-tree-domain"
    assert historical != canonical.CANON.treehash(tmp_path)


def test_canonical_projection_cannot_substitute_staged_r25_floor_for_historical_v029(tmp_path, monkeypatch) -> None:
    # This reproduces the exact class of evidence bug that broke the first canonical-generalization run. The
    # shipping product may expose a staged-r25 research floor, but the frozen gate must use the independently
    # rebuilt original-tree v0.29 bytes supplied by the adapter. The canonical projection must also use the
    # caller-observed complete product wall time rather than trusting a narrower terminal-internal timer.
    product = {
        "selected": "g04-overlay",
        "archive_bytes": 900,
        "format_revision": canonical.CANON.REVISION,
        "format_profile": "geometry-g04",
        "portfolio_create_s": 999.0,
        "v029_research_floor_bytes": 9_999_999,
        "r25": {
            "g04_bytes": 950,
            "g04_selected": "geometry-overlay-g04",
            "prefixgraph_contract_eligible": False,
            "prefixgraph_admitted": False,
            "prefixgraph_reject_reason": "not-smaller",
            "prefixgraph_bytes": None,
            "max_dependency_depth": 0,
            "max_selected_member_read_amplification": 1.25,
            "g04": {"v029": {"portfolio_create_s": 999.0}},
            "prefixgraph_locality": None,
        },
    }
    historical_stats = {"portfolio_create_s": 1.0, "archive_bytes": 1_234}
    complete_product_create_s = 2.0
    revision_queries: list[Path] = []

    def fake_revision_for_archive(archive: Path) -> tuple[int, str]:
        revision_queries.append(Path(archive))
        return canonical.CANON.REVISION, "geometry-g04"

    # This is a projection-contract test, not an archive-parser test.  The production adapter now deliberately
    # derives revision/profile from the published archive so promoted terminals cannot spoof historical stats.
    # Preserve that call boundary while supplying the synthetic archive identity explicitly instead of pointing
    # the stricter adapter at a file that this unit test never created.
    monkeypatch.setattr(canonical.CANON, "_revision_for_archive", fake_revision_for_archive)

    normalized = canonical._normalize_product_stats(
        product,
        1_234,
        historical_stats,
        tmp_path / "unused.cmpct",
        complete_product_create_s,
    )

    assert revision_queries == [tmp_path / "unused.cmpct"]
    assert normalized["v029_bytes"] == 1_234
    assert normalized["v029_bytes"] != product["v029_research_floor_bytes"]
    assert normalized["g04"]["v029"] == historical_stats
    assert normalized["archive_bytes"] == 900
    assert normalized["portfolio_create_s"] == complete_product_create_s
    assert normalized["portfolio_create_s"] != product["portfolio_create_s"]
    assert normalized["max_selected_member_read_amplification"] == 1.25
    assert normalized["historical_v029_measurement"] == "independent-original-tree-build"


def test_r24_locality_measures_largest_regular_user_member(monkeypatch, tmp_path) -> None:
    # Tiny files can legitimately share a large r24 pack. Taking the worst ratio over every tiny member answers a
    # different question than the frozen release contract, which selects the largest regular user-visible member.
    # Keep the actual public read operation observable so this cannot degrade into a build-time proxy.
    class FakeR24:
        def __init__(self, _path):
            self.files = [
                ["tiny.txt", canonical.CANON.R24_CODEC.K_FILE, 0, 0, 1, None, ["blob", 0]],
                ["large.bin", canonical.CANON.R24_CODEC.K_FILE, 0, 0, 100, None, ["blob", 1]],
            ]
            self.blobs = [
                [0, 500, 0, 0, 0],
                [0, 200, 0, 0, 0],
            ]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def _blob(self, idx):
            self.observed_blob_ids.add(int(idx))
            return b"x" * int(self.blobs[idx][1])

        def read(self, name):
            if name == "tiny.txt":
                return self._blob(0)[:1]
            if name == "large.bin":
                return self._blob(1)[:100]
            raise KeyError(name)

        observed_blob_ids: set[int] = set()

    monkeypatch.setattr(canonical.CANON, "CMPCT", FakeR24)

    assert canonical._r24_selected_member_amplification(tmp_path / "fake-r24.cmpct") == 2.0


def test_canonical_adapter_is_scoped_and_restores_historical_harness(monkeypatch, tmp_path) -> None:
    original = gate.RC
    seen = []

    def fake_run(_work_root: Path):
        seen.append(gate.RC)
        return {"rows": [], "totals": {}, "gate": {"passed": True}}

    monkeypatch.setattr(gate, "run", fake_run)
    result = canonical.run(tmp_path)

    assert seen == [canonical.ADAPTER]
    assert gate.RC is original
    assert result["release_facade"] == "cmpct-v030-release-product-v1"
