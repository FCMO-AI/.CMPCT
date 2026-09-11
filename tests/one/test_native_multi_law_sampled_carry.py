from benchmarks.one.one_g02_native_multi_law_sampled_carry import (
    PHASE_FAMILIES, SAMPLE_MASK, SAMPLED_SUPPORT_DEN, SAMPLED_SUPPORT_NUM,
    _call, _decision_tuple, _oracle_decision, make_sample_case,
)


def test_sampling_law_is_frozen():
    assert SAMPLE_MASK == 3
    assert (SAMPLED_SUPPORT_NUM, SAMPLED_SUPPORT_DEN) == (1, 2)


def test_phase_poison_controls_keep_full_and_sampled_relation_nomination():
    for family in PHASE_FAMILIES:
        data = make_sample_case(family, 64 * 1024)
        oracle = _oracle_decision(data)
        sampled = _decision_tuple(_call("one_gate_sampled", data))
        assert sampled == oracle
        if family.startswith("add8"):
            assert oracle[2]
        else:
            assert oracle[3]
