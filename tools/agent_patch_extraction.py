from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)


lib_path = Path("native/cmpct-core/src/lib.rs")
text = lib_path.read_text()
text = replace_once(
    text,
    "const STREAM_CHUNK_BYTES: usize = 8 * 1024 * 1024;\nconst MAX_SYMLINK_TARGET_BYTES: u64 = 1024 * 1024;",
    "const STREAM_CHUNK_BYTES: usize = 8 * 1024 * 1024;\nconst MAX_EXTRACT_OUTPUT_BYTES: u64 = 64 * 1024 * 1024 * 1024;\nconst MAX_SYMLINK_TARGET_BYTES: u64 = 1024 * 1024;",
    "extraction budget constant",
)

start_marker = "    /// Safely extract the complete logical tree into an absent or empty destination directory.\n    pub fn extract_all("
start = text.index(start_marker)
end = text.index("\n}\n\nfn le_u32", start)
replacement = r'''    fn extraction_materialized_bytes(&self) -> Result<u64, CmpctError> {
        self.entries.iter().try_fold(0u64, |total, entry| {
            // Hardlinks reuse already-materialized file bytes and directories carry no payload.
            // Symlink targets still count because archive-controlled bytes are materialized on disk.
            let bytes = match entry.kind {
                KIND_FILE | KIND_SYMLINK => entry.size,
                KIND_DIR | KIND_HARDLINK => 0,
                _ => return Err(CmpctError::Unsupported),
            };
            total.checked_add(bytes).ok_or(CmpctError::MemberLimit)
        })
    }

    /// Extract the complete tree with an explicit archive-wide materialization budget.
    pub fn extract_all_bounded(
        &self,
        destination: &Path,
        max_materialized_bytes: u64,
    ) -> Result<(), CmpctError> {
        self.preflight()?;
        if self.extraction_materialized_bytes()? > max_materialized_bytes {
            return Err(CmpctError::MemberLimit);
        }

        if destination.exists() {
            if !destination.is_dir() {
                return Err(CmpctError::Extraction(
                    "destination exists and is not a directory".into(),
                ));
            }
            if fs::read_dir(destination)?.next().is_some() {
                return Err(CmpctError::Extraction(
                    "destination must be empty to preserve no-follow extraction safety".into(),
                ));
            }
        } else {
            fs::create_dir_all(destination)?;
        }

        // Build directory topology before restoring archived permissions. Restrictive modes such as
        // 0500 or 0000 must not make a parent unwritable before its descendants are populated.
        for entry in &self.entries {
            if entry.kind == KIND_DIR {
                fs::create_dir_all(destination.join(&entry.path))?;
            }
        }

        for (index, entry) in self.entries.iter().enumerate() {
            let output = destination.join(&entry.path);
            match entry.kind {
                KIND_FILE => {
                    if let Some(parent) = output.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    let mut target = File::create(&output)?;
                    self.copy_entry_to(index, &mut target)?;
                    target.sync_all()?;
                    apply_mode(&output, entry.mode)?;
                }
                KIND_SYMLINK => {
                    if entry.size > MAX_SYMLINK_TARGET_BYTES {
                        return Err(CmpctError::MemberLimit);
                    }
                    let len = usize::try_from(entry.size).map_err(|_| CmpctError::MemberLimit)?;
                    let mut bytes = vec![0u8; len];
                    self.read_range(index, 0, &mut bytes)?;
                    if let Some(expected) = self.expected_entry_hash(index)? {
                        if Sha256::digest(&bytes).as_slice() != expected {
                            return Err(CmpctError::MemberHash);
                        }
                    }
                    let target = String::from_utf8(bytes).map_err(|_| {
                        CmpctError::Extraction(format!(
                            "symlink target for {} is not UTF-8",
                            entry.path
                        ))
                    })?;
                    validate_symlink_target(&entry.path, &target)?;
                    if let Some(parent) = output.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    create_symlink(&target, &output)?;
                }
                KIND_DIR | KIND_HARDLINK => {}
                _ => return Err(CmpctError::Unsupported),
            }
        }

        for (index, entry) in self.entries.iter().enumerate() {
            if entry.kind != KIND_HARDLINK {
                continue;
            }
            let resolved = self.resolve_entry_index(index)?;
            let target_entry = self.entries.get(resolved).ok_or(CmpctError::Range)?;
            if target_entry.kind != KIND_FILE {
                return Err(CmpctError::Extraction(
                    "hardlink does not resolve to a regular file".into(),
                ));
            }
            let source = destination.join(&target_entry.path);
            let output = destination.join(&entry.path);
            if let Some(parent) = output.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::hard_link(source, output)?;
        }

        // Restore restrictive directory modes only after every descendant exists, deepest first.
        let mut directories: Vec<&Entry> = self
            .entries
            .iter()
            .filter(|entry| entry.kind == KIND_DIR)
            .collect();
        directories.sort_by_key(|entry| std::cmp::Reverse(entry.path.matches('/').count()));
        for entry in directories {
            apply_mode(&destination.join(&entry.path), entry.mode)?;
        }
        Ok(())
    }

    /// Extract using the native handler's conservative default ceiling. Callers that deliberately
    /// materialize larger trees can opt into a larger explicit budget through the bounded ABI.
    pub fn extract_all(&self, destination: &Path) -> Result<(), CmpctError> {
        self.extract_all_bounded(destination, MAX_EXTRACT_OUTPUT_BYTES)
    }'''
text = text[:start] + replacement + text[end:]

abi_anchor = '''/// Extract the complete archive into an absent or empty UTF-8 destination directory.
#[no_mangle]
pub unsafe extern "C" fn cmpct_extract_all(
'''
bounded_abi = '''/// Extract with an explicit archive-wide payload-materialization ceiling.
///
/// # Safety
/// `archive` must be live and `destination` must point to a valid NUL-terminated UTF-8 string.
#[no_mangle]
pub unsafe extern "C" fn cmpct_extract_all_bounded(
    archive: *const Archive,
    destination: *const c_char,
    max_materialized_bytes: u64,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    if destination.is_null() {
        return CmpctStatus::Null as c_int;
    }
    let destination = match CStr::from_ptr(destination).to_str() {
        Ok(destination) => destination,
        Err(_) => return CmpctStatus::Utf8 as c_int,
    };
    match archive.extract_all_bounded(Path::new(destination), max_materialized_bytes) {
        Ok(()) => CmpctStatus::Ok as c_int,
        Err(error) => error_status(&error) as c_int,
    }
}

/// Extract the complete archive into an absent or empty UTF-8 destination directory.
///
/// # Safety
/// `archive` must be live and `destination` must point to a valid NUL-terminated UTF-8 string.
#[no_mangle]
pub unsafe extern "C" fn cmpct_extract_all(
'''
text = replace_once(text, abi_anchor, bounded_abi, "bounded extraction ABI")
lib_path.write_text(text)

header = Path("native/cmpct-core/include/cmpct.h")
h = header.read_text()
h = replace_once(
    h,
    "int32_t cmpct_extract_all(const CmpctArchive *archive, const char *destination);",
    "int32_t cmpct_extract_all_bounded(\n    const CmpctArchive *archive,\n    const char *destination,\n    uint64_t max_materialized_bytes\n);\nint32_t cmpct_extract_all(const CmpctArchive *archive, const char *destination);",
    "C ABI header",
)
header.write_text(h)

test = Path("tests/native_stream_extract_abi.py")
t = test.read_text()
t = replace_once(
    t,
    "    lib.cmpct_extract_all.argtypes = [ctypes.c_void_p, ctypes.c_char_p]\n    lib.cmpct_extract_all.restype = ctypes.c_int32",
    "    lib.cmpct_extract_all_bounded.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint64]\n    lib.cmpct_extract_all_bounded.restype = ctypes.c_int32\n    lib.cmpct_extract_all.argtypes = [ctypes.c_void_p, ctypes.c_char_p]\n    lib.cmpct_extract_all.restype = ctypes.c_int32",
    "bounded ABI test binding",
)
t = replace_once(
    t,
    '        os.symlink("../target.txt", root / "dir" / "symlink.txt")',
    '        os.symlink("../target.txt", root / "dir" / "symlink.txt")\n        # Build the complete source fixture before making the directory intentionally non-writable.\n        # The regression is about extraction ordering, not whether fixture setup can write into 0500.\n        os.chmod(root / "dir", 0o500)',
    "restrictive directory fixture",
)
t = replace_once(
    t,
    '            destination = Path(td) / "extracted"\n            assert lib.cmpct_extract_all(handle, str(destination).encode()) == 0',
    '            limited = Path(td) / "limited"\n            assert lib.cmpct_extract_all_bounded(handle, str(limited).encode(), 1024) == -4\n            assert not limited.exists()\n\n            destination = Path(td) / "extracted"\n            assert lib.cmpct_extract_all(handle, str(destination).encode()) == 0',
    "pre-materialization limit regression",
)
t = replace_once(
    t,
    '            assert (destination / "dir" / "small.txt").read_bytes() == (root / "dir" / "small.txt").read_bytes()',
    '            assert (destination / "dir" / "small.txt").read_bytes() == (root / "dir" / "small.txt").read_bytes()\n            assert (os.stat(destination / "dir").st_mode & 0o7777) == 0o500',
    "directory mode restoration regression",
)
test.write_text(t)

# Current branch recovery code still uses mutable rmpv helpers that are unavailable in the pinned API,
# and imports the declaration guard as a second module. Fix those compile blockers without weakening it.
recovery = Path("native/cmpct-core/src/recovery.rs")
r = recovery.read_text()
r = r.replace('#[path = "msgpack_guard.rs"]\nmod msgpack_guard;\n\n', 'use crate::msgpack_guard;\n\n', 1)
r = replace_once(
    r,
    '''fn map_value_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Value> {
    value
        .as_map_mut()?
        .iter_mut()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
}
''',
    '''fn map_value_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Value> {
    let Value::Map(map) = value else {
        return None;
    };
    map.iter_mut()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
}

fn array_mut(value: &mut Value) -> Option<&mut Vec<Value>> {
    let Value::Array(values) = value else {
        return None;
    };
    Some(values)
}
''',
    "recovery mutable MessagePack helpers",
)
r = r.replace('.as_array_mut()', '.pipe(array_mut)') if False else r
r = r.replace('candidate.as_array_mut().ok_or(RecoveryError::Malformed)?', 'array_mut(candidate).ok_or(RecoveryError::Malformed)?')
r = r.replace('.and_then(Value::as_array_mut)', '.and_then(array_mut)')
recovery.write_text(r)

recovery_test = Path("native/cmpct-core/tests/recovery_golden.rs")
rt = recovery_test.read_text()
anchor = '#[path = "../src/recovery.rs"]\nmod recovery;\n'
if '#[path = "../src/msgpack_guard.rs"]\nmod msgpack_guard;\n' not in rt:
    rt = replace_once(rt, anchor, '#[path = "../src/msgpack_guard.rs"]\nmod msgpack_guard;\n\n' + anchor, "recovery test guard module")
recovery_test.write_text(rt)
