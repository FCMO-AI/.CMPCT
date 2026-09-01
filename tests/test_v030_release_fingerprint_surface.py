from __future__ import annotations

from tools import check_v030_release_lock as lock


def test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs() -> None:
    """Release-critical oracle/platform source must invalidate stale v0.30 receipts when it changes."""
    manifest = lock.load_manifest()
    _fingerprint, rows = lock.fingerprint(manifest)
    covered = set(rows)

    required = {
        "tests/generate_v030_canonical_goldens.py",
        "tests/generate_v030_implicit_goldens.py",
        "tests/conformance/v030-r25-canonical.json",
        "tests/conformance/v030-r25-implicit-v4.json",
        "tests/native_v030_canonical.py",
        "tests/native_v030_implicit_manifest.py",
        "integrations/android/app/build.gradle",
        "integrations/android/app/src/androidTest/java/ai/fcmo/cmpct/CmpctAndroidImplicitManifestTest.java",
    }
    missing = required - covered
    assert not missing, f"release fingerprint omits release-critical custody inputs: {sorted(missing)}"

    # Footnote: Android build output is deliberately not source truth. The physical/hosted workflows rebuild it
    # from the fingerprinted Gradle/JNI/Java/native inputs; hashing app/build or generated jniLibs would make the
    # candidate identity depend on whichever runner happened to build it last.
    assert not any("/build/" in rel for rel in rows if rel.startswith("integrations/android/"))
    assert not any("/jniLibs/" in rel for rel in rows if rel.startswith("integrations/android/"))
