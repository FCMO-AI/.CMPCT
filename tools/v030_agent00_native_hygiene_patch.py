from __future__ import annotations

"""One-shot bounded repair for the v0.30 portable Rust Clippy/API gate.

Footnote: this script is intentionally temporary. It performs exact, count-checked substitutions so the CI runner can
repair long Rust modules without a broad rewrite from the connector runtime. The workflow deletes this script before
persisting the verified Rust changes, so it cannot become part of the release candidate.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected exactly one bounded replacement, found {count}: {old[:80]!r}"
        )
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    lib = "native/cmpct-portable/src/lib.rs"
    replace_once(
        lib,
        "use crate::canonical::Canonical25Archive;\n",
        "#[doc(hidden)]\npub use crate::canonical::Canonical25Archive;\n"
        "#[doc(hidden)]\npub use crate::g04::G04Archive;\n"
        "#[doc(hidden)]\npub use crate::prefix::PrefixArchive;\n",
    )
    replace_once(lib, "    ResearchG04(g04::G04Archive),\n", "    ResearchG04(G04Archive),\n")
    replace_once(
        lib,
        "    ResearchPrefixGraph(prefix::PrefixArchive),\n",
        "    ResearchPrefixGraph(PrefixArchive),\n",
    )
    replace_once(
        lib,
        "Ok(Self::ResearchG04(g04::G04Archive::open(path, identity)?))",
        "Ok(Self::ResearchG04(G04Archive::open(path, identity)?))",
    )
    replace_once(
        lib,
        "prefix::PrefixArchive::open(path, identity)?,",
        "PrefixArchive::open(path, identity)?,",
    )
    replace_once(
        lib,
        ".ok_or_else(|| PortableError::Range)?;",
        ".ok_or(PortableError::Range)?;",
    )
    replace_once(
        lib,
        'destination.parent().unwrap_or_else(|| Path::new("."))',
        'destination.parent().unwrap_or(Path::new("."))',
    )

    safety_docs = {
        'pub unsafe extern "C" fn cmpct_portable_open(': """/// Opens an archive through the stable C ABI.
///
/// # Safety
/// `path` must point to a readable NUL-terminated C string and `out` must point to writable storage for one
/// `PortableArchive*`. The returned handle must later be passed to `cmpct_portable_close` exactly once.
// Footnote: the ABI validates nulls, UTF-8, archive grammar and panics; pointer provenance remains the caller's contract.
""",
        'pub unsafe extern "C" fn cmpct_portable_close(': """/// Releases a handle returned by `cmpct_portable_open`.
///
/// # Safety
/// `handle` must be null or a live pointer returned by `cmpct_portable_open` that has not already been closed.
""",
        'pub unsafe extern "C" fn cmpct_portable_revision(': """/// Returns the detected archive revision through the C ABI.
///
/// # Safety
/// `handle` must reference a live `PortableArchive` and `out` must point to writable `u32` storage.
""",
        'pub unsafe extern "C" fn cmpct_portable_entry_count(': """/// Returns the number of logical entries through the C ABI.
///
/// # Safety
/// `handle` must reference a live `PortableArchive` and `out` must point to writable `usize` storage.
""",
        'pub unsafe extern "C" fn cmpct_portable_entry_info(': """/// Copies fixed metadata for one logical entry through the C ABI.
///
/// # Safety
/// `handle` must reference a live `PortableArchive` and `out` must point to writable `PortableEntryInfo` storage.
""",
        'pub unsafe extern "C" fn cmpct_portable_entry_path(': """/// Copies one logical entry path into caller-owned storage.
///
/// # Safety
/// `handle` must reference a live `PortableArchive`; `required` must be writable. If `buffer` is non-null, it must
/// reference at least `capacity` writable bytes and must not alias memory invalidated by this call.
""",
        'pub unsafe extern "C" fn cmpct_portable_entry_read_range(': """/// Reads a bounded logical member range into caller-owned storage.
///
/// # Safety
/// `handle` must reference a live `PortableArchive`; `written` must be writable. `buffer` may be null only when
/// `capacity == 0`; otherwise it must reference at least `capacity` writable bytes for the duration of the call.
""",
        'pub unsafe extern "C" fn cmpct_portable_entry_read(': """/// Materializes one admitted member into caller-owned storage and optionally returns locality statistics.
///
/// # Safety
/// `handle` must reference a live `PortableArchive` and `written` must be writable. A non-null `buffer` must cover
/// `capacity` writable bytes; a non-null `stats` must point to writable `PortableMemberStats` storage.
""",
        'pub unsafe extern "C" fn cmpct_portable_verify(': """/// Performs complete archive verification through the C ABI.
///
/// # Safety
/// `handle` must reference a live `PortableArchive` for the complete duration of the call.
""",
    }
    file = ROOT / lib
    text = file.read_text(encoding="utf-8")
    for signature, docs in safety_docs.items():
        marker = "#[unsafe(no_mangle)]\n" + signature
        count = text.count(marker)
        if count != 1:
            raise SystemExit(f"{lib}: safety-doc target count for {signature!r} is {count}")
        text = text.replace(marker, docs + marker, 1)
    file.write_text(text, encoding="utf-8")

    replace_once(
        "native/cmpct-portable/src/format.rs",
        """pub(crate) fn sint(
    value: &Value,
    label: &str,
    minimum: i64,
    maximum: i64,
) -> Result<i64, PortableError> {
    value
        .as_i64()
        .filter(|value| *value >= minimum && *value <= maximum)
        .ok_or_else(|| PortableError::Format(format!("{label} integer declaration")))
}

""",
        "",
    )

    canonical = "native/cmpct-portable/src/canonical.rs"
    replace_once(canonical, "pub(crate) struct Canonical25Archive {", "pub struct Canonical25Archive {")
    replace_once(
        canonical,
        """        if let Ok(file) = File::open(path) {
            if let Some(time) = std::time::UNIX_EPOCH
                .checked_add(std::time::Duration::from_nanos(metadata.mtime_ns as u64))
            {
                let _ = file.set_times(std::fs::FileTimes::new().set_modified(time));
            }
        }
""",
        """        if let Ok(file) = File::open(path)
            && let Some(time) = std::time::UNIX_EPOCH
                .checked_add(std::time::Duration::from_nanos(metadata.mtime_ns as u64))
        {
            let _ = file.set_times(std::fs::FileTimes::new().set_modified(time));
        }
""",
    )

    g04 = "native/cmpct-portable/src/g04.rs"
    replace_once(g04, "pub(crate) struct G04Archive {", "pub struct G04Archive {")
    replace_once(
        g04,
        """        if let (Some(left), Some(right)) = (&primary, &tail) {
            if left.meta_sha != right.meta_sha || left.merkle != right.merkle {
                return Err(PortableError::Integrity(
                    "conflicting authenticated G0-G4 metadata copies".into(),
                ));
            }
        }
""",
        """        if let (Some(left), Some(right)) = (&primary, &tail)
            && (left.meta_sha != right.meta_sha || left.merkle != right.merkle)
        {
            return Err(PortableError::Integrity(
                "conflicting authenticated G0-G4 metadata copies".into(),
            ));
        }
""",
    )

    prefix = "native/cmpct-portable/src/prefix.rs"
    replace_once(prefix, "pub(crate) struct PrefixArchive {", "pub struct PrefixArchive {")
    replace_once(
        prefix,
        """        if let (Some(left), Some(right)) = (&primary, &tail) {
            if left.meta_sha != right.meta_sha {
                return Err(PortableError::Integrity(
                    "conflicting authenticated PrefixGraph metadata copies".into(),
                ));
            }
        }
""",
        """        if let (Some(left), Some(right)) = (&primary, &tail)
            && left.meta_sha != right.meta_sha
        {
            return Err(PortableError::Integrity(
                "conflicting authenticated PrefixGraph metadata copies".into(),
            ));
        }
""",
    )
    replace_once(
        prefix,
        """fn parse_meta(
    value: &Value,
) -> Result<(Vec<PortableEntry>, Vec<PrefixRecord>, [u8; 32]), PortableError> {
""",
        """type ParsedPrefixMeta = (Vec<PortableEntry>, Vec<PrefixRecord>, [u8; 32]);

fn parse_meta(value: &Value) -> Result<ParsedPrefixMeta, PortableError> {
""",
    )
    replace_once(
        prefix,
        """    if let Some(value) = optional_field(map, "max_file_bytes") {
        if uint(value, "PrefixGraph max_file_bytes", MAX_FILE_BYTES)? > MAX_FILE_BYTES {
            return Err(PortableError::Limit(
                "PrefixGraph file-size declaration exceeds policy".into(),
            ));
        }
    }
""",
        """    if let Some(value) = optional_field(map, "max_file_bytes")
        && uint(value, "PrefixGraph max_file_bytes", MAX_FILE_BYTES)? > MAX_FILE_BYTES
    {
        return Err(PortableError::Limit(
            "PrefixGraph file-size declaration exceeds policy".into(),
        ));
    }
""",
    )
    replace_once(
        prefix,
        """    if let Some(value) = optional_field(map, "max_member_read_amplification") {
        if number(value, "PrefixGraph read amplification")? > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(
                "PrefixGraph read-amplification declaration exceeds policy".into(),
            ));
        }
    }
""",
        """    if let Some(value) = optional_field(map, "max_member_read_amplification")
        && number(value, "PrefixGraph read amplification")? > MAX_MEMBER_READ_AMP
    {
        return Err(PortableError::Limit(
            "PrefixGraph read-amplification declaration exceeds policy".into(),
        ));
    }
""",
    )


if __name__ == "__main__":
    main()
