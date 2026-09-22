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
    # The helper is release-critical comparator semantics: helper-only changes must schedule ABBA,
    # not merely alter the candidate fingerprint while the evidence lane skips.
    assert HELPER in text
    assert 'materialize_performance_base_native' in text[text.index('latest-head-impact'):text.index('performance:', text.index('latest-head-impact'))]
