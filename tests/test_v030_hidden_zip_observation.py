from __future__ import annotations

import os
import random
import zipfile

from cmpct.hidden_zip import MIN_VERIFIED_REUSE, admission_is_current, observe_hidden_zip_admission


def _payload() -> bytes:
    rng = random.Random(204)
    return bytes(rng.randrange(256) for _ in range(16 * 1024))


def _hidden_zip(path, payload: bytes):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("shared.bin", payload)


def test_two_physical_hidden_archives_can_earn_verified_reuse(tmp_path):
    payload = _payload()
    _hidden_zip(tmp_path / "a.bin", payload)
    _hidden_zip(tmp_path / "b.bin", payload)
    obs = observe_hidden_zip_admission(tmp_path)
    assert [a.rel for a in obs.admitted] == ["a.bin", "b.bin"]
    assert all(a.verified_reuse_bytes >= MIN_VERIFIED_REUSE for a in obs.admitted)
    assert all(admission_is_current(tmp_path, a) for a in obs.admitted)
    assert obs.verification_bytes_read > 0


def test_hardlink_alias_cannot_fake_two_physical_owners(tmp_path):
    payload = _payload()
    first = tmp_path / "a.bin"
    _hidden_zip(first, payload)
    os.link(first, tmp_path / "b.bin")
    obs = observe_hidden_zip_admission(tmp_path)
    assert obs.admitted == ()


def test_explicit_zip_can_supply_reuse_without_becoming_hidden_admission(tmp_path):
    payload = _payload()
    _hidden_zip(tmp_path / "explicit.zip", payload)
    _hidden_zip(tmp_path / "hidden.bin", payload)
    obs = observe_hidden_zip_admission(tmp_path)
    assert [a.rel for a in obs.admitted] == ["hidden.bin"]
    assert obs.admitted[0].verified_reuse_bytes >= MIN_VERIFIED_REUSE


def test_mutation_after_observation_revokes_admission(tmp_path):
    payload = _payload()
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    _hidden_zip(a, payload)
    _hidden_zip(b, payload)
    obs = observe_hidden_zip_admission(tmp_path)
    admission = next(x for x in obs.admitted if x.rel == "a.bin")
    with a.open("ab") as f:
        f.write(b"changed-after-observation")
    assert not admission_is_current(tmp_path, admission)
