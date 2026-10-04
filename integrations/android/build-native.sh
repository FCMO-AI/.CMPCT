#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CRATE="$ROOT/native/cmpct-portable"
JNI="$ROOT/integrations/android/app/src/main/jniLibs"

command -v cargo >/dev/null || { echo "cargo is required" >&2; exit 1; }
command -v cargo-ndk >/dev/null || {
  echo "cargo-ndk is required (install with: cargo install cargo-ndk)" >&2
  exit 1
}
: "${ANDROID_NDK_HOME:?ANDROID_NDK_HOME must point at Android NDK r29 or a compatible installed NDK}"

# Android is a release authority lane, so dependency resolution is part of the candidate rather than ambient CI
# state. Refuse to build unless the shared portable crate carries the repository-pinned Cargo.lock, and bind its
# digest before invoking Cargo. This keeps hosted/physical Android evidence on the same dependency graph as
# desktop/native authority instead of allowing the runner's registry state to define the release candidate.
git -C "$ROOT" ls-files --error-unmatch native/cmpct-portable/Cargo.lock >/dev/null || {
  echo "native/cmpct-portable/Cargo.lock is not tracked" >&2
  exit 1
}
LOCK_BEFORE="$(sha256sum "$CRATE/Cargo.lock" | awk '{print $1}')"

rm -rf "$JNI"
mkdir -p "$JNI"

# Footnote: cargo-ndk's Android ABI names intentionally produce Gradle's expected jniLibs directory
# structure. The Rust target triples remain an internal mapping handled by cargo-ndk, so this script
# does not duplicate target/ABI translation logic that could drift between Android toolchains.
# Building cmpct-portable also compiles its cmpct-core dependency; there is one r24 parser and one
# r25 dispatcher, not separate Android-specific archive implementations. --locked is release custody:
# no Android build may silently resolve a dependency graph different from the committed candidate.
(
  cd "$CRATE"
  cargo ndk \
    --platform 23 \
    -t arm64-v8a \
    -t armeabi-v7a \
    -t x86_64 \
    -t x86 \
    -o "$JNI" \
    build --release --locked
)

LOCK_AFTER="$(sha256sum "$CRATE/Cargo.lock" | awk '{print $1}')"
test "$LOCK_BEFORE" = "$LOCK_AFTER" || {
  echo "Cargo.lock changed during Android native build: $LOCK_BEFORE -> $LOCK_AFTER" >&2
  exit 1
}
git -C "$ROOT" diff --exit-code -- native/cmpct-portable/Cargo.lock

for abi in arm64-v8a armeabi-v7a x86_64 x86; do
  test -f "$JNI/$abi/libcmpct_portable.so" || {
    echo "missing portable CMPCT library for $abi" >&2
    exit 1
  }
done

echo "CMPCT portable native Android libraries ready under $JNI (Cargo.lock $LOCK_AFTER)"
