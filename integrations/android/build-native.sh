#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CRATE="$ROOT/native/cmpct-core"
JNI="$ROOT/integrations/android/app/src/main/jniLibs"

command -v cargo >/dev/null || { echo "cargo is required" >&2; exit 1; }
command -v cargo-ndk >/dev/null || {
  echo "cargo-ndk is required (install with: cargo install cargo-ndk)" >&2
  exit 1
}
: "${ANDROID_NDK_HOME:?ANDROID_NDK_HOME must point at Android NDK r29 or a compatible installed NDK}"

rm -rf "$JNI"
mkdir -p "$JNI"

# Footnote: build all four Android ABIs from the same Rust crate. cargo-ndk maps the Android ABI names
# and API floor to Rust targets/NDK clang correctly, avoiding per-ABI shell logic that could drift.
(
  cd "$CRATE"
  cargo ndk \
    --platform 23 \
    --target aarch64-linux-android \
    --target armv7-linux-androideabi \
    --target x86_64-linux-android \
    --target i686-linux-android \
    --output-dir "$JNI" \
    build --release
)

for abi in arm64-v8a armeabi-v7a x86_64 x86; do
  test -f "$JNI/$abi/libcmpct_core.so" || {
    echo "missing native CMPCT library for $abi" >&2
    exit 1
  }
done

echo "CMPCT native Android libraries ready under $JNI"
