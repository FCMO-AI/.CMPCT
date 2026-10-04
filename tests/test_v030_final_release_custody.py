from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/v030-final-release-authority.yml"
LOCK = ROOT / "docs/V030_RELEASE_LOCK.json"

# These are semantic dependencies of the expensive final-authority product evidence.
# Candidate-identity custody is intentionally broader and comes from V030_RELEASE_LOCK
# over the accumulated PR candidate; the expensive result jobs stay newest-commit scoped.
REQUIRED_PRODUCT_DEPENDENCIES = (
    "experiments/entropygraph_v030_r25_manifest_admission.py",
    "experiments/entropygraph_v030_fs_implicit_v4.py",
    "experiments/entropygraph_v030_release_product_base.py",
    "experiments/entropygraph_v030_verified_restore.py",
    "experiments/entropygraph_v030_release_product_logs_candidate.py",
    "experiments/entropygraph_v030_r24_dead_dictionary.py",
    "experiments/entropygraph_v030_r24_media_terminal.py",
    "experiments/entropygraph_v030_r24_compact_control_profile.py",
    "experiments/entropygraph_v030_release_reader.py",
    "experiments/entropygraph_v030_release_reader_policy.py",
    "experiments/entropygraph_v030_release.py",
    "benchmarks/v030_release_performance.py",
    "benchmarks/v030_external_competitors.py",
    "tests/test_v030_final_release_custody.py",
)


def _classifier_pattern(text: str) -> re.Pattern[str]:
    matches = re.findall(r"grep -Eq '([^']+)' /tmp/latest-head-files\\.txt", text)
    assert len(matches) == 1, "final-release authority must expose one auditable newest-head classifier"
    return re.compile(matches[0])


def test_final_release_pr_trigger_is_one_cheap_classifier_without_duplicate_paths() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger = text.split("permissions:", 1)[0]
    assert "  pull_request:" in trigger
    assert "    paths:" not in trigger
    assert "    paths-ignore:" not in trigger


def test_accumulated_candidate_custody_is_manifest_derived_and_independent() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    manifest = json.loads(LOCK.read_text(encoding="utf-8"))
    globs = manifest["fingerprint_globs"]

    # The current v0.30 candidate PR is based on v0.29 main, where the release
    # lock does not yet exist. Self-membership makes the accumulated custody
    # job unavoidable on that long-lived candidate and keeps later law edits visible.
    assert "docs/V030_RELEASE_LOCK.json" in globs
    assert ".github/workflows/v030-*.yml" in globs
    assert "tools/check_v030_release_lock.py" in globs

    assert "run_custody: ${{ steps.scope.outputs.run_custody }}" in text
    assert "PR_BASE: ${{ github.event.pull_request.base.sha }}" in text
    assert 'Path("docs/V030_RELEASE_LOCK.json")' in text
    assert 'manifest["fingerprint_globs"]' in text
    assert '"git", "diff", "--name-only", "-z", os.environ["PR_BASE"], "HEAD"' in text
    assert "release-custody:" in text
    assert "python tools/check_v030_release_lock.py --json" in text


def test_final_release_newest_head_classifier_tracks_product_dependencies() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    classifier = _classifier_pattern(text)
    assert "git diff-tree --no-commit-id --name-only -r HEAD" in text
    for dependency in REQUIRED_PRODUCT_DEPENDENCIES:
        assert classifier.fullmatch(dependency), f"final-release newest-head classifier omits {dependency}"


def test_classifier_fetches_full_history_for_accumulated_custody() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    classifier_job = text.split("  latest-head-impact:", 1)[1].split("  release-custody:", 1)[0]
    assert "fetch-depth: 0" in classifier_job
