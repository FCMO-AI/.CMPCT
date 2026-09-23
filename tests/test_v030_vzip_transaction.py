from __future__ import annotations

import zipfile

from cmpct.codec import sha
import cmpct.vzip_transaction as tx


def test_failed_recipe_discards_all_staged_candidate_mutations(monkeypatch, tmp_path):
    calls = []
    def fake_recipe(_path, add_content):
        add_content(b"first-member", ".bin", b"exact-deflate"); return None
    def real_add(*args):
        calls.append(args); return sha(args[0])
    monkeypatch.setattr(tx, "make_vzip_recipe", fake_recipe)
    assert tx.make_vzip_recipe_transactional(tmp_path / "candidate.bin", real_add) is None
    assert calls == []


def test_successful_recipe_replays_staged_mutations_after_commit_point(monkeypatch, tmp_path):
    calls = []; expected = [b"first", b"second"]
    def fake_recipe(_path, add_content):
        refs = [add_content(expected[0], ".a"), add_content(expected[1], ".b", b"stream")]; return [refs]
    def real_add(raw, hint="", deflate_stream=None):
        calls.append((raw, hint, deflate_stream)); return sha(raw)
    monkeypatch.setattr(tx, "make_vzip_recipe", fake_recipe)
    recipe = tx.make_vzip_recipe_transactional(tmp_path / "candidate.bin", real_add)
    assert recipe == [[sha(expected[0]), sha(expected[1])]]
    assert calls == [(b"first", ".a", None), (b"second", ".b", b"stream")]


def test_cohort_can_stage_every_recipe_before_any_real_mutation(monkeypatch, tmp_path):
    real_calls = []
    def fake_recipe(path, add_content):
        add_content(path.name.encode(), ".bin")
        return None if path.name == "bad.bin" else [path.name]
    def real_add(raw, hint="", deflate_stream=None):
        real_calls.append((raw, hint, deflate_stream)); return sha(raw)
    monkeypatch.setattr(tx, "make_vzip_recipe", fake_recipe)
    good = tx.stage_vzip_recipe(tmp_path / "good.bin")
    bad = tx.stage_vzip_recipe(tmp_path / "bad.bin")
    assert good is not None and bad is None
    # A cohort caller can now discard the successful stage because another member failed,
    # without having touched the real candidate store.
    assert real_calls == []
    assert good.candidates[0][0] == b"good.bin"


def test_stage_retention_budget_rejects_before_recipe_materialization(monkeypatch, tmp_path):
    """Declared logical bytes must gate staging before member payloads are decoded."""
    path = tmp_path / "candidate.bin"
    payload = b"A" * (2 * 1024 * 1024)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("large.bin", payload)

    called = False
    def forbidden_recipe(_path, _add_content):
        nonlocal called; called = True
        raise AssertionError("recipe construction must not run after pre-allocation refusal")
    monkeypatch.setattr(tx, "make_vzip_recipe", forbidden_recipe)

    assert tx.stage_vzip_recipe(path, max_retained_bytes=1024 * 1024) is None
    assert called is False


def test_stage_retention_bound_is_conservative_for_valid_recipe(tmp_path):
    path = tmp_path / "candidate.bin"
    payload = (b"bounded-retention-" * 4096)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload.bin", payload)

    bound = tx._retained_upper_bound(path)
    assert bound == path.stat().st_size + len(payload)
    staged = tx.stage_vzip_recipe(path, max_retained_bytes=bound)
    assert staged is not None
    actual = sum(len(raw) + (0 if stream is None else len(stream)) for raw, _hint, stream, _ref in staged.candidates)
    assert actual <= bound
