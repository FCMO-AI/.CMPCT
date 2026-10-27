"""The audio extra is an encoder option, never a requirement for ordinary creation."""
import builtins
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from cmpct import codec
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def pcm_wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x01\x00\x02\x00" * 2048)
    return output.getvalue()


class OptionalAudioTests(unittest.TestCase):
    def test_missing_each_audio_extra_creates_exact_generic_archive(self):
        original_import = builtins.__import__
        for missing in ("numpy", "soundfile"):
            def without_extra(name, *args, **kwargs):
                if name == missing:
                    raise ModuleNotFoundError(name, name=name)
                if name == "numpy":
                    # Reach the second import even on a minimal installation.
                    return object()
                return original_import(name, *args, **kwargs)

            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as td:
                root = Path(td) / "input"
                root.mkdir()
                raw = pcm_wav()
                (root / "sample.wav").write_bytes(raw)
                archive = Path(td) / "output.cmpct"
                with patch("builtins.__import__", side_effect=without_extra):
                    Builder(root, workers=1).build(archive)
                    with CMPCT(archive) as reader:
                        self.assertEqual(reader.read("sample.wav"), raw)
                        self.assertNotIn(codec.CODEC_WAVFLAC, [b[3] for b in reader.blobs])

    def test_missing_native_audio_library_declines_transform(self):
        with patch.object(codec, "_audio_modules", side_effect=OSError("libsndfile unavailable")):
            self.assertIsNone(codec.wavflac_compress(pcm_wav()))

    def test_non_wav_does_not_import_audio(self):
        with patch.object(codec, "_audio_modules", side_effect=AssertionError("unnecessary audio import")):
            self.assertIsNone(codec.wavflac_compress(b"not a WAV"))

    def test_unexpected_audio_failure_is_not_hidden(self):
        with patch.object(codec, "_audio_modules", side_effect=RuntimeError("unexpected bug")):
            with self.assertRaisesRegex(RuntimeError, "unexpected bug"):
                codec.wavflac_compress(pcm_wav())

    def test_decoder_does_not_silently_fallback(self):
        with patch.object(codec, "_audio_modules", side_effect=ImportError("missing decoder")):
            with self.assertRaisesRegex(ImportError, "missing decoder"):
                codec.wavflac_decompress(b"", b"")


if __name__ == "__main__":
    unittest.main()
