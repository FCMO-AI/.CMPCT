from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v030-native-authority.yml"

# Canonical profile isolation executes these semantic-owner sources inside a private release module graph. A
# wrapper-only trigger is insufficient: changing a cloned source can change the native authority's canonical
# comparison semantics while an older receipt still looks green. Keep the release-reader source in both workflow
# scheduling layers and keep this test itself in the same evidence closure.
REQUIRED_DEPENDENCIES = (
    "experiments/entropygraph_v030_profile_isolation.py",
    "experiments/entropygraph_v030_release_reader.py",
    "experiments/entropygraph_v030_release_reader_policy.py",
    "tests/test_v030_native_authority_custody.py",
)


def _classifier_pattern(text: str) -> re.Pattern[str]:
    matches = re.findall(r"grep -Eq '([^']+)' /tmp/latest-head-files\.txt", text)
    assert len(matches) == 1, "native authority must expose one auditable newest-head classifier"
    return re.compile(matches[0])


def test_native_authority_trigger_tracks_cloned_semantic_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for dependency in REQUIRED_DEPENDENCIES:
        assert f"      - '{dependency}'" in text, f"native-authority PR trigger omits {dependency}"


def test_native_authority_newest_head_classifier_tracks_same_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    classifier = _classifier_pattern(text)
    for dependency in REQUIRED_DEPENDENCIES:
        assert classifier.fullmatch(dependency), f"native-authority newest-head classifier omits {dependency}"
