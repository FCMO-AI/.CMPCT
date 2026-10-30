"""J24I69 detached hostile tests, synthetic fixtures plus optional real-provider evidence."""
import hashlib
import io
import json
import math
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import j24i69_withinarm_referee as court


class RefereeTests(unittest.TestCase):
    def fixture(self):
        root = {"schema": "cmpct-zip-parity-v1", "repetitions": 7, "timing_statistic": "median", "corpora": {}}
        for corpus in court.CORPORA:
            root["corpora"][corpus] = {"logical_bytes": 10000}
            for mode in court.MODES:
                root["corpora"][corpus][mode] = {
                    eng: {"bytes": 2000, "create_s_median": 0.1, "extract_s_median": 0.1}
                    for eng in court.ENGINES
                }
        self.name = next(iter(court.PROVIDERS))
        self.env = {"base_commit": court.HEADS[self.name][0], "candidate_commit": court.HEADS[self.name][1], "format_revision": "24", "cpu_model": "synthetic"}
        self.corpus = {"tree_sha256": court.CORPUS_HASH, "files": 7713, "logical_bytes": 303738466}
        self.sweeps = {n: json.loads(json.dumps(root)) for n in court.SWEEPS}
        return self

    def provider(self, members=None, duplicates=None):
        entries = {**{n: json.dumps(val).encode() for n, val in self.sweeps.items()}, "corpus.json": json.dumps(self.corpus).encode(), "environment.txt": "\n".join(k + "=" + v for k, v in self.env.items()).encode()}
        if members:
            entries.update(members)
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for k, v in entries.items(): z.writestr(k, v)
            for k, v in duplicates or []: z.writestr(k, v)
        return out.getvalue()

    def call(self, content=None):
        payload = self.provider() if content is None else content
        return court._read_raw_provider(payload, self.name, hashlib.sha256(payload).hexdigest())

    def test_positive(self):
        self.fixture()
        r = self.call()
        self.assertEqual(len(r["effects"]), 128)
        self.assertEqual(len(r["official_cmpct"]), 32)
        self.assertEqual(sum(e["magnitude_crossing"] for e in r["effects"]), 0)

    def test_signed_placebo_and_release_red_are_separate(self):
        self.fixture()
        # The base A->B change breaches magnitude, while candidate aggregate can be neutral.
        self.sweeps["base-b.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = 0.11
        r = self.call()
        e = next(e for e in r["effects"] if (e["arm"], e["corpus"],e["mode"],e["engine"],e["operation"]) == ("base","tiny","library","cmpct","create"))
        self.assertTrue(e["magnitude_crossing"])
        self.assertEqual(e["delta_ms"], 10.0)
        # Official candidate is not a slowdown, even though the same-arm placebo is substantial.
        o = next(e for e in r["official_cmpct"] if e["corpus"] == "tiny" and e["mode"] == "library" and e["operation"] == "create")
        self.assertFalse(o["historical_release_red"])

    def test_both_blocks_positive_does_not_prove_source_change(self):
        self.fixture()
        # A and B both show a gate-sized label effect, although the script receives no
        # mutation or source distinction within either synthetic arm.
        for block in ("a", "b"):
            self.sweeps["candidate-"+block+".json"]["corpora"]["nested"]["cli"]["cmpct"]["create_s_median"] = 0.108
        r = self.call()
        o = next(e for e in r["official_cmpct"] if (e["corpus"],e["mode"],e["operation"]) == ("nested","cli","create"))
        self.assertTrue(o["historical_release_red"])
        self.assertTrue(o["both_blocks_positive_crossing"])
        self.assertTrue(o["both_within_arm_neutral"])

    def test_provider_digest_mismatch(self):
        self.fixture()
        b = self.provider()
        with self.assertRaisesRegex(ValueError, "provider SHA256 mismatch"):
            court._read_raw_provider(b, self.name, "0" * 64)

    def test_discordant_archive_bytes(self):
        self.fixture()
        self.sweeps["candidate-b.json"]["corpora"]["tiny"]["library"]["cmpct"]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "archived bytes"):
            self.call()

    def test_corrupt_source_identity(self):
        self.fixture()
        self.env["base_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "unexpected historical source"):
            self.call()

    def test_corrupt_corpus_identity(self):
        self.fixture()
        self.corpus["tree_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "corpus fingerprint"):
            self.call()

    def test_wrong_repetition_count(self):
        self.fixture()
        self.sweeps["candidate-a.json"]["repetitions"] = 6
        with self.assertRaisesRegex(ValueError, "original benchmark schema"):
            self.call()

    def test_infinite_timing(self):
        self.fixture()
        self.sweeps["candidate-a.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = math.inf
        with self.assertRaisesRegex(ValueError, "non-finite"):
            self.call()

    def test_zero_timing(self):
        self.fixture()
        self.sweeps["candidate-a.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = 0.0
        with self.assertRaisesRegex(ValueError, "non-finite or nonpositive"):
            self.call()

    def test_string_timing(self):
        self.fixture()
        self.sweeps["candidate-a.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = "0.1"
        with self.assertRaisesRegex(ValueError, "timing type"):
            self.call()

    def test_missing_corpus(self):
        self.fixture()
        del self.sweeps["base-b.json"]["corpora"]["combined"]
        with self.assertRaisesRegex(ValueError, "unexpected corpus set"):
            self.call()

    def test_duplicate_zip_member(self):
        self.fixture()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            b = self.provider(duplicates=[("base-a.json", b"{}")])
        with self.assertRaisesRegex(ValueError, "duplicate ZIP member names"):
            self.call(b)

    def test_duplicate_json_object_key_rejected(self):
        self.fixture()
        # The baseline json.loads last-key-wins behavior admits a conflicting metric.
        original = self.provider()
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            entries = {k: z.read(k) for k in z.namelist()}
        span = b'"create_s_median": 0.1'
        assert span in entries["base-a.json"]
        entries["base-a.json"] = entries["base-a.json"].replace(span, b'"create_s_median": 0.2, "create_s_median": 0.1', 1)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for k, v in entries.items():z.writestr(k,v)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            self.call(buf.getvalue())

    def test_boolean_archive_lengths_rejected(self):
        self.fixture()
        # Python bool is a subclass of int; permit it and byte-accounting becomes ambiguous.
        for n in court.SWEEPS:
            self.sweeps[n]["corpora"]["tiny"]["library"]["cmpct"]["bytes"] = True
            self.sweeps[n]["corpora"]["tiny"]["logical_bytes"] = True
        with self.assertRaisesRegex(ValueError, "invalid (logical|archive) bytes"):
            self.call()

    def test_missing_sweep(self):
        self.fixture()
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("corpus.json", "{}")
        with self.assertRaisesRegex(ValueError, "missing original"):
            self.call(b.getvalue())

    def test_inverted_sign_is_not_release_regression(self):
        self.fixture()
        self.sweeps["candidate-a.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = 0.05
        self.sweeps["candidate-b.json"]["corpora"]["tiny"]["library"]["cmpct"]["create_s_median"] = 0.05
        r = self.call()
        o = next(e for e in r["official_cmpct"] if e["corpus"] == "tiny" and e["mode"] == "library" and e["operation"] == "create")
        self.assertLess(o["delta_ms"], -3)
        self.assertFalse(o["historical_release_red"])


if __name__ == "__main__":
    unittest.main()
