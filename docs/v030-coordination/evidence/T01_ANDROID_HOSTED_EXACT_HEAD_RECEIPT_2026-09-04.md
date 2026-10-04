# v0.30 exact-head hosted Android custody receipt — 2026-09-04

Status: **HOSTED ANDROID / SHARED-JNI CUSTODY ONLY — physical ARM64 and strict release authority remain outstanding**

This record persists the substantive hosted Android result that followed the exact-head Android evidence refresh. It advances T01 portability custody without granting the `platform-android` release receipt, because repository law requires a matching physical ARM64 Android result in addition to hosted/emulator evidence.

## Exact source and run

- PR: `#56`
- branch: `agent/v030-authoritative-integration`
- source commit: `74ed6921ee2bc053e0d10abf52ed95f972aefb46`
- workflow: `CMPCT Android`
- workflow run: `33880873159`
- result-bearing job: `101048985866` (`build-and-device-smoke`)
- exact-head checkout/binding: passed
- release-critical fingerprint emitted by the run: `dba253fa1fca9c51997c5d3f6e08e09ea4fc0f984f22a91f8b89225a6abfb455`
- Android emulator: Android 10 / API 29 / x86_64
- connected instrumentation: **10/10 passed**
- CI-topology self-check for `.github/workflows/android.yml`: passed

## Native/package boundary proved

The run built the shared native boundary for every declared Android ABI:

- `arm64-v8a` / `aarch64-linux-android`;
- `armeabi-v7a`;
- `x86_64`;
- `x86`.

The packaged JNI library was checked as relocatable and resolved through `libcmpct_portable.so`; the gate explicitly rejected a direct `libcmpct_core.so` dependency and host-build `/home/` path leakage. The debug APK completed successfully before the emulator acceptance suite ran.

The hosted evidence facts emitted by the workflow were all true:

- hosted Android emulator green;
- all declared ABIs built;
- portable JNI dependency verified;
- canonical r25 portable dispatch green;
- implicit-v4 portable dispatch green;
- Logs inverse portable dispatch green;
- compact-control portable dispatch green.

## Frozen vectors exercised

Canonical Logs portable vector:

- schema: `cmpct-v030-android-logs-vector-v1`;
- archive SHA-256: `85d5e78b911a06436e7cc959c20a8e68477e474cd649d9c3d66e6664a065e042`;
- expected logical entries: `8`;
- strong verification: true;
- inverse edges: `2`;
- gzip and Zstd source presence: true;
- supplementary-Unicode path presence: true.

Compact-control portable vector:

- schema: `cmpct-v030-android-compact-control-vector-v2`;
- archive SHA-256: `31a97d039dbec27c465cb80a4a5a841d357aebe429d13677805b3aeac66add90`;
- complete archive bytes: `4,025,488`;
- source-r24 bytes: `4,027,332`;
- delta vs source r24: **-1,844 B**;
- expected logical entries: `298`;
- strong verification: true;
- physical payload records unchanged: true;
- two authenticated control copies: true.

## Artifact custody

- artifact: `cmpct-android-debug-74ed6921ee2bc053e0d10abf52ed95f972aefb46`;
- artifact id: `9940034248`;
- artifact ZIP SHA-256: `dbdffff80918adea61b222844b4bdd49b32f31788f888dcd1c6c2f0ebb54b65a`;
- uploaded files: `17`;
- archive size reported by Actions: `12,637,855` bytes.

## Interpretation boundary

This receipt proves exact-source hosted/emulator packaging, portable-JNI linkage and Android instrumentation for the stated source and emitted release-critical fingerprint. It does **not** prove physical-device execution, external-competitor domination, compression generalization, runtime/RSS/selective-read performance, reader/recovery fuzz, or final strict release authority.

`docs/PORTABILITY.md` and `docs/V030_RELEASE_GATES.md` require physical ARM64 Android evidence. At the time this receipt was prepared, physical workflow run `33880873202`, job `101048943476`, was still queued on labels `self-hosted`, `linux`, `arm64`, `cmpct-android-physical`; it therefore receives no release credit here.

The strict `platform-android` receipt remains unavailable until the required physical run succeeds on matching hosted evidence and the release lock validates the complete platform facts. **Do not merge, tag, version-bump, or publish v0.30 from this receipt.**
