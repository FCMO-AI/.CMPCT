from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'zip-parity.yml'
HELPER = 'tools/materialize_performance_base_native.py'


def test_r24_parity_materializes_historical_native_before_corpus():
    text = WORKFLOW.read_text()
    base = text.index('- name: Materialize base engine worktree')
    corpus = text.index('- name: Generate one immutable release corpus')
    call = text.index('python tools/materialize_performance_base_native.py')
    assert base < call < corpus
    assert '--receipt benchmark-artifacts/base-native.json' in text[call:corpus]
    assert 'native-ownership.txt' in text[call:corpus]


def test_helper_changes_are_performance_impacting():
    text = WORKFLOW.read_text()
    # Invocation + both event path filters must name the exact helper path; otherwise a helper-only
    # comparator-semantic change can legitimately avoid scheduling this release evidence lane.
    assert text.count(HELPER) >= 3
    # The deep newest-head gate must independently classify the helper as performance-impacting.
    classifier = text[text.index('latest-head-impact'):text.index('performance:', text.index('latest-head-impact'))]
    assert 'materialize_performance_base_native' in classifier
