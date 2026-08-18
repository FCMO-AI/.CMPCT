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

rm -rf "$JNI"
mkdir -p "$JNI"

# Footnote: cargo-ndk's Android ABI names intentionally produce Gradle's expected jniLibs directory
# structure. The Rust target triples remain an internal mapping handled by cargo-ndk, so this script
# does not duplicate target/ABI translation logic that could drift between Android toolchains.
# Building cmpct-portable also compiles its cmpct-core dependency; there is one r24 parser and one
# r25 dispatcher, not separate Android-specific archive implementations.
(
  cd "$CRATE"
  cargo ndk \
    --platform 23 \
    -t arm64-v8a \
    -t armeabi-v7a \
    -t x86_64 \
    -t x86 \
    -o "$JNI" \
    build --release
)

for abi in arm64-v8a armeabi-v7a x86_64 x86; do
  test -f "$JNI/$abi/libcmpct_portable.so" || {
    echo "missing portable CMPCT library for $abi" >&2
    exit 1
  }
done

echo "CMPCT portable native Android libraries ready under $JNI"
