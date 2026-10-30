# Regresion issue #538: `cmpct create` con audio WAV importa numpy y soundfile
# (codec._audio_modules). Ambos deben ser dependencias base, no sólo un extra.
import tomllib
from pathlib import Path


def test_audio_codec_dependencies_are_base_requirements():
    data = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())
    base = " ".join(data["project"]["dependencies"]).lower()
    assert "numpy" in base, "numpy must be a base dependency (codec._audio_modules imports it)"
    assert "soundfile" in base, "soundfile must be a base dependency (codec._audio_modules imports it)"
