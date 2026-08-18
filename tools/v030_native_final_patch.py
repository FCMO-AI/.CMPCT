#!/usr/bin/env python3
from pathlib import Path
import re


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: exact anchor count {count}, expected {expected}: {old[:120]!r}")
    path.write_text(text.replace(old, new, expected))


def replace_regex(path: Path, pattern: str, repl: str, expected: int = 1, flags: int = 0) -> None:
    text = path.read_text()
    out, count = re.subn(pattern, repl, text, count=expected, flags=flags)
    if count != expected:
        raise SystemExit(f"{path}: regex anchor count {count}, expected {expected}: {pattern!r}")
    path.write_text(out)


root = Path(__file__).resolve().parents[1]

# 1) Android UX: revision 25 must be reachable after ArchiveRegistry's canonical-magic/native-revision preflight.
main = root / "integrations/android/app/src/main/java/ai/fcmo/cmpct/MainActivity.java"
replace_regex(
    main,
    r"if\s*\(\s*archive\.revision\(\)\s*!=\s*24\s*\)",
    "if (archive.revision() != 24 && archive.revision() != 25)",
    expected=1,
)
text = main.read_text()
# Message copy is not part of the admission rule, but leaving an r24-only claim would mislead users.
text = text.replace("revision 24", "release revision 24 or 25")
text = text.replace("Revision 24", "Release revision 24 or 25")
main.write_text(text)

# 2) Rust API lint: the crate is publish=false and the public enum is used as the Rust/CLI handle while its
# low-level profile structs remain deliberately private. Make that intentional instead of letting -D warnings
# turn effective-visibility encapsulation into a release-gate failure.
lib = root / "native/cmpct-portable/src/lib.rs"
replace_exact(
    lib,
    "#[derive(Debug)]\npub enum PortableArchive {",
    "// Footnote: profile structs stay private so external Rust callers cannot bypass the dispatcher. The\n"
    "// crate is publish=false; PortableArchive is a handle, not a promise that low-level variants are stable.\n"
    "#[allow(private_interfaces)]\n#[derive(Debug)]\npub enum PortableArchive {",
)

# Make revision truth visible in CLI diagnostics without changing byte-stream commands.
cli = root / "native/cmpct-portable/src/bin/cmpct-portable.rs"
replace_exact(
    cli,
    '            println!("profile={}", archive.profile().as_str());\n',
    '            println!("profile={}", archive.profile().as_str());\n'
    '            println!("revision={}", archive.revision());\n',
)

# 3) Filesystem metadata: reject impossible xattr names during authenticated preflight rather than silently
# dropping them later because CString cannot represent embedded NUL.
manifest = root / "native/cmpct-portable/src/manifest.rs"
replace_exact(
    manifest,
    '        let name = text(&row[0], "r25 xattr name")?.to_owned();\n'
    '        let Value::Binary(data) = &row[1] else {',
    '        let name = text(&row[0], "r25 xattr name")?.to_owned();\n'
    '        if name.contains(\'\\0\') {\n'
    '            return Err(PortableError::Format("r25 xattr name contains NUL".into()));\n'
    '        }\n'
    '        let Value::Binary(data) = &row[1] else {',
)

# 4) Replace only the final metadata-restoration function. Parsing/reconstruction/extraction logic above it
# remains byte-for-byte untouched.
canonical = root / "native/cmpct-portable/src/canonical.rs"
text = canonical.read_text()
marker = "fn apply_metadata_best_effort(path: &Path, metadata: &FsMetadata, is_symlink: bool) {"
pos = text.find(marker)
if pos < 0 or text.find(marker, pos + 1) >= 0:
    raise SystemExit("canonical.rs: metadata function anchor missing or duplicated")
new_tail = r'''fn apply_metadata_best_effort(path: &Path, metadata: &FsMetadata, is_symlink: bool) {
    if !is_symlink {
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = fs::set_permissions(path, fs::Permissions::from_mode(metadata.mode));
        }
        if let Ok(file) = File::open(path) {
            if let Some(time) = std::time::UNIX_EPOCH
                .checked_add(std::time::Duration::from_nanos(metadata.mtime_ns as u64))
            {
                let _ = file.set_times(std::fs::FileTimes::new().set_modified(time));
            }
        }
    }

    #[cfg(unix)]
    restore_unix_owner(path, metadata, is_symlink);
    #[cfg(any(target_os = "linux", target_os = "android"))]
    restore_linux_xattrs(path, metadata, is_symlink);

    // Footnote: ownership/xattrs are best-effort because unprivileged extraction cannot promise chown or
    // namespace-specific xattr setters. Failures never fabricate metadata and never bypass content integrity;
    // the staged tree is still published only after structural/content restoration succeeds.
}

#[cfg(unix)]
fn restore_unix_owner(path: &Path, metadata: &FsMetadata, is_symlink: bool) {
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;

    let Ok(path) = CString::new(path.as_os_str().as_bytes()) else {
        return;
    };
    unsafe {
        // Footnote: lchown is mandatory for links so metadata restoration never follows an archive-controlled
        // symlink. Regular entries use chown. Both are intentionally best-effort under ordinary app/user IDs.
        if is_symlink {
            let _ = libc::lchown(path.as_ptr(), metadata.uid, metadata.gid);
        } else {
            let _ = libc::chown(path.as_ptr(), metadata.uid, metadata.gid);
        }
    }
}

#[cfg(any(target_os = "linux", target_os = "android"))]
fn restore_linux_xattrs(path: &Path, metadata: &FsMetadata, is_symlink: bool) {
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;

    let Ok(path) = CString::new(path.as_os_str().as_bytes()) else {
        return;
    };
    for (name, value) in &metadata.xattrs {
        let Ok(name) = CString::new(name.as_bytes()) else {
            continue;
        };
        unsafe {
            let ptr = if value.is_empty() {
                std::ptr::null()
            } else {
                value.as_ptr().cast()
            };
            if is_symlink {
                let _ = libc::lsetxattr(
                    path.as_ptr(),
                    name.as_ptr(),
                    ptr,
                    value.len(),
                    0,
                );
            } else {
                let _ = libc::setxattr(
                    path.as_ptr(),
                    name.as_ptr(),
                    ptr,
                    value.len(),
                    0,
                );
            }
        }
    }
}
'''
canonical.write_text(text[:pos] + new_tail)

print("v0.30 final surgical portability patch applied")
