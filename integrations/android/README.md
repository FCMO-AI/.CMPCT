# CMPCT Android archive handler

Status: **revision-24 read-only preview now passes the Android 10 emulator gate; physical ARM64 and representation-complete device acceptance remain before calling Android support shipped.**

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

## Emulator acceptance achieved

GitHub Actions now builds all four declared ABIs, inspects the packaged JNI ELF dependency table for host-path leakage, boots an Android 10 / API 29 x86_64 emulator, installs the app and runs AndroidX instrumentation tests. The current emulator gate proves:

1. canonical CMPCT MIME routing resolves to the installed handler;
2. generic `application/octet-stream` routing resolves for a `.cmpct` content URI but not for an otherwise-identical `.bin` URI;
3. canonical revision-24 RAW/Zstd/Deflate golden archives open through Android → JNI → the shared Rust core and return byte-exact requested ranges;
4. an imported archive becomes a `DocumentsProvider` root, its regular member is enumerable, and that member streams byte-exactly through the provider pipe;
5. a bad-magic file is rejected before it can become an imported root;
6. the packaged JNI library depends on `libcmpct_core.so` by relocatable basename rather than a build-machine filesystem path.

The emulator gate is intentionally narrower than the production-device gate below. Passing it means the first-party Android routing/provider/native stack is executable, not that every revision-24 representation or every Android file manager is already certified. Micro-solid `S_PACK` reads are currently guarded in native-core CI rather than by a dedicated Android instrumentation vector.

## Remaining acceptance gate before “Android support” may be called shipped

A release candidate still needs at least one physical ARM64 Android device and broader committed sample archives to prove all of the following:

1. tapping/opening a `.cmpct` launches CMPCT from real device file/download providers when MIME/extension routing permits it;
2. importing through the system picker succeeds from representative real `content:` providers;
3. the archive appears as a root in Android's system document UI after process/device restart;
4. nested directories enumerate correctly in system DocumentsUI;
5. supported regular members open in external applications through the provider;
6. multi-chunk, CDC, sparse and micro-solid packed members stream byte-exactly without full-archive extraction;
7. corrupt index/blob input fails closed across the native representations Android exposes;
8. unsupported native representations fail explicitly rather than returning guessed bytes;
9. process restart preserves imported roots;
10. representative archives round-trip byte-exactly after member extraction/streaming.

## Current limitations

The Android layer can only expose representations the shared native core can read. As of revision 24, the Rust core implements ordinary direct RAW/Zstd/WAV-FLAC/raw-Deflate/Zstd-dictionary members, fixed/CDC/sparse range reads, micro-solid `S_PACK` slices, and independently gated virtual-ZIP reconstruction for ZIP_STORED payloads plus retained-exact Deflate stream mode 1. `S_PACK` has a Builder-derived C-ABI regression/seek gate but still needs a builder-independent frozen pack archive for full conformance provenance. Virtual-ZIP Deflate mode 0 has a fixed oracle and an authenticated physical-Deflate component but deliberately remains unsupported at archive dispatch until virtual projection segments can distinguish logical blob slices from exact physical codec-4 payload slices. Virtual-ZIP Deflate mode 2, native sequential-stream APIs, full native extraction, journal recovery, and remaining structural-preflight parity are still native-core work. The provider therefore remains read-only and treats unsupported representations as errors.

Android cannot make every unrelated third-party file manager understand a new format merely by installing this app. The first-party handler + Storage Access Framework solve direct opening/browsing on devices with the app installed; wider recognition still requires MIME-correct senders and, later, upstream archive/file-manager integrations.

## Design footnote

A permanent hidden ZIP copy is intentionally **not** embedded inside `.cmpct` files for compatibility. That would make every archive pay duplicate storage forever. `cmpct export-zip` remains the legacy escape hatch, while platform handlers make the native format progressively ordinary to open.
