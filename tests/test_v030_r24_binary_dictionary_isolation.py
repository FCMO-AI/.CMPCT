from pathlib import Path

from benchmarks import v030_r24_binary_dictionary_isolation_oracle as O
from experiments import entropygraph_v030_release_product as P


def test_dictionary_training_hides_release_only_binary_hint_and_restores_it(monkeypatch, tmp_path: Path):
    observed = []

    def fake_train(_self):
        observed.append(bool(getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)))

    monkeypatch.setattr(P.C.Builder, "_train_dictionary", fake_train)
    builder = O._PackingOnlyBinaryBuilder(tmp_path)
    previous = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
    P._R24_CDC_POLICY.medium_binary_pack = True
    try:
        builder._train_dictionary()
        assert observed == [False]
        assert getattr(P._R24_CDC_POLICY, "medium_binary_pack", False) is True
    finally:
        P._R24_CDC_POLICY.medium_binary_pack = previous


def test_candidate_is_only_a_dictionary_training_policy_override():
    # The candidate inherits the exact shipping Builder; it does not override scanning, S_PACK admission,
    # candidate encoding, physical record construction, recovery framing, or reader semantics.
    overridden = {
        name
        for name, value in O._PackingOnlyBinaryBuilder.__dict__.items()
        if callable(value) and not name.startswith("__")
    }
    assert overridden == {"_train_dictionary"}
