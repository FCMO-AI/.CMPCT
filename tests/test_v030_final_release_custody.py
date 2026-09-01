from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v030-final-release-authority.yml"

# These are semantic dependencies of the final authority that have previously been easy to omit because the
# release jobs execute through wrapper modules. If one disappears from either scheduling layer, an implementation
# change could inherit an older exact-head receipt until some unrelated tracked file happens to move.
REQUIRED_DEPENDENCIES = (
    "experiments/entropygraph_v030_r25_manifest_admission.py",
    "experiments/entropygraph_v030_fs_implicit_v4.py",
    "experiments/entropygraph_v030_release_product_base.py",
    "experiments/entropygraph_v030_release_product_logs_candidate.py",
    "experiments/entropygraph_v030_r24_dead_dictionary.py",
    "experiments/entropygraph_v030_r24_media_terminal.py",
    "experiments/entropygraph_v030_r24_compact_control_profile.py",
    "experiments/entropygraph_v030_release.py",
    "benchmarks/v030_release_performance.py",
    "benchmarks/v030_external_competitors.py",
)


def _classifier_pattern(text: str) -> re.Pattern[str]:
    matches = re.findall(r"grep -Eq '([^']+)' /tmp/latest-head-files\.txt", text)
    assert len(matches) == 1, "final-release authority must expose one auditable newest-head classifier"
    return re.compile(matches[0])


def test_final_release_trigger_tracks_semantic_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for dependency in REQUIRED_DEPENDENCIES:
        assert f"      - '{dependency}'" in text, f"final-release PR trigger omits {dependency}"


def test_final_release_newest_head_classifier_tracks_same_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    classifier = _classifier_pattern(text)
    for dependency in REQUIRED_DEPENDENCIES:
        assert classifier.fullmatch(dependency), f"final-release newest-head classifier omits {dependency}"
