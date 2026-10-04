from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v030-manifest-admission-custody.yml"

# canonical_final is executed with profile_isolation's private dependency graph. The manifest-admission custody
# lane therefore owns the graph sources, not only the wrapper and filesystem-control modules: otherwise a reader
# or candidate semantic-owner change could break canonical import/writer behavior while this fast D5 boundary
# inherited an older green receipt.
REQUIRED_ISOLATED_GRAPH = (
    "experiments/entropygraph_v030_geometry_overlay_g04.py",
    "experiments/entropygraph_v030_prefixgraph.py",
    "experiments/entropygraph_v030_release_reader.py",
    "experiments/entropygraph_v030_release_reader_policy.py",
    "experiments/entropygraph_v030_release_admission.py",
    "experiments/entropygraph_v030_release_candidate.py",
    "experiments/entropygraph_v030_shared_portfolio.py",
    "tests/test_v030_manifest_admission_custody.py",
)


def _classifier_pattern(text: str) -> re.Pattern[str]:
    matches = re.findall(r"grep -Eq '([^']+)' /tmp/latest-head-files\.txt", text)
    assert len(matches) == 1, "manifest custody must expose one auditable newest-head classifier"
    return re.compile(matches[0])


def test_manifest_custody_trigger_tracks_isolated_graph() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for dependency in REQUIRED_ISOLATED_GRAPH:
        assert f"      - '{dependency}'" in text, f"manifest-custody PR trigger omits {dependency}"


def test_manifest_custody_classifier_tracks_isolated_graph() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    classifier = _classifier_pattern(text)
    for dependency in REQUIRED_ISOLATED_GRAPH:
        assert classifier.fullmatch(dependency), f"manifest-custody newest-head classifier omits {dependency}"
