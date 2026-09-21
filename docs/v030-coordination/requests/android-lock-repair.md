# Android native lock repair — transient coordination note

Authoritative hosted Android run `35660554699` failed before Gradle assembly because `integrations/android/build-native.sh` executes `cargo build --release --locked` in `native/cmpct-portable`, while that committed lock still resolves `zstd 0.13.3 / zstd-safe 7.3.0 / zstd-sys 2.0.16+zstd.1.5.7`. The authoritative `cmpct-core` manifest now requires exact `zstd = "=0.13.0"`, whose proven archive-identity graph is `zstd-safe 7.0.0 / zstd-sys 2.0.9+zstd.1.5.5`. Cargo therefore correctly refuses to mutate the stale portable lock under `--locked`.

This is dependency-custody failure, not Android product evidence. Repair only the portable lock to the already-proven 1.5.5 graph; do not relax `--locked`. Then remove the temporary lock-reconciliation workflow and this coordination note, rerun hosted Android, and only after hosted evidence is green refresh the physical ARM64 request for the exact candidate/fingerprint.
