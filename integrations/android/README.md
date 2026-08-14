# CMPCT Android archive handler

Status: **source-complete read-only preview for revision 24; device/emulator acceptance still required before calling Android support shipped.**

This project is the first Android implementation of the portability contract in `docs/PORTABILITY.md`. It deliberately contains **no independent CMPCT parser**. Java/Kotlin-facing behavior goes through a small JNI shim which links the same memory-safe Rust `cmpct-core` used by other native clients.

## What this preview implements

- `ACTION_VIEW` registration for `application/vnd.fcmo.cmpct` and `application/x-cmpct`;
- a bounded `.cmpct` fallback for providers that expose unknown files as `application/octet-stream`;
- Storage Access Framework import from `content:` URIs;
- mandatory `CMPCT24\0` magic validation before native parsing;
- durable app-private archive imports keyed by whole-archive SHA-256;
- a simple tap-to-browse logical archive tree;
- a read-only `DocumentsProvider`, one Android root per imported archive;
- directory enumeration without full archive extraction;
- member MIME projection and `ACTION_VIEW` hand-off to other Android apps;
- member streaming through `cmpct_entry_read_range`, in bounded chunks, without a second parser;
- four Android ABIs: `arm64-v8a`, `armeabi-v7a`, `x86_64`, `x86`.

## Build

Prerequisites:

1. JDK 17;
2. stable Android SDK / API 36 and Android Build Tools compatible with AGP 9.3;
3. Android NDK r29 (`29.0.14206865` in the checked-in Gradle configuration);
4. Rust + the four Android Rust targets;
5. `cargo-ndk` (`cargo install cargo-ndk`);
6. Gradle 9.5 or a current Android Studio installation able to use the pinned AGP version.

Example Rust target setup:

```bash
rustup target add \
  aarch64-linux-android \
  armv7-linux-androideabi \
  x86_64-linux-android \
  i686-linux-android
```

Set `ANDROID_NDK_HOME` to the NDK root, then build from this directory:

```bash
bash build-native.sh
gradle :app:assembleDebug
```

`app:preBuild` also depends on `build-native.sh`, so normal Gradle packaging cannot silently reuse a stale Rust library.

## Acceptance gate before “Android support” may be claimed

The source existing is not the release claim. A release candidate must run on an Android emulator and at least one physical ARM64 device and prove all of the following with committed revision-24 conformance/sample archives:

1. tapping/opening a `.cmpct` launches CMPCT when MIME/extension routing permits it;
2. importing through the system picker succeeds from a `content:` URI;
3. the archive appears as a root in Android's system document UI;
4. nested directories enumerate correctly;
5. a supported regular member opens in another application through the provider;
6. a multi-chunk member streams byte-exactly without full-archive extraction;
7. corrupt index/blob input fails closed;
8. unsupported native representations fail explicitly rather than returning guessed bytes;
9. Android process restart preserves imported roots;
10. the sample archive round-trips byte-exactly after member extraction.

The emulator CI additionally asserts that a generic `application/octet-stream` URI ending in `.cmpct` resolves to CMPCT while an otherwise identical `.bin` URI does not. This protects the extension fallback from becoming a catch-all binary handler.

## Current limitations

The Android layer can only expose representations the shared native core can read. As of revision 24, ordinary direct RAW/Zstd/raw-Deflate/Zstd-dictionary members plus fixed/CDC/sparse range reads are implemented in the Rust core. WAV-FLAC direct members, virtual ZIP reconstruction, native sequential-stream APIs, full native extraction, journal recovery, and remaining structural-preflight parity are still native-core work. The provider therefore remains read-only and treats unsupported representations as errors.

Android cannot make every unrelated third-party file manager understand a new format merely by installing this app. The first-party handler + Storage Access Framework solve direct opening/browsing on devices with the app installed; wider recognition still requires MIME-correct senders and, later, upstream archive/file-manager integrations.

## Design footnote

A permanent hidden ZIP copy is intentionally **not** embedded inside `.cmpct` files for compatibility. That would make every archive pay duplicate storage forever. `cmpct export-zip` remains the legacy escape hatch, while platform handlers make the native format progressively ordinary to open.
