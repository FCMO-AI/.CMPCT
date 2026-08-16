from pathlib import Path

lib_path = Path("native/cmpct-core/src/lib.rs")
text = lib_path.read_text()

const_old = "const STREAM_CHUNK_BYTES: usize = 8 * 1024 * 1024;\nconst MAX_SYMLINK_TARGET_BYTES: u64 = 1024 * 1024;"
const_new = "const STREAM_CHUNK_BYTES: usize = 8 * 1024 * 1024;\nconst MAX_EXTRACT_OUTPUT_BYTES: u64 = 64 * 1024 * 1024 * 1024;\nconst MAX_SYMLINK_TARGET_BYTES: u64 = 1024 * 1024;"
if const_old not in text:
    raise SystemExit("constant anchor missing")
text = text.replace(const_old, const_new, 1)

start_marker = "    /// Safely extract the complete logical tree into an absent or empty destination directory.\n    pub fn extract_all("
start = text.index(start_marker)
end = text.index("\n}\n\nfn le_u32", start)
replacement = r'''    fn extraction_materialized_bytes(&self) -> Result<u64, CmpctError> {
        self.entries.iter().try_fold(0u64, |total, entry| {
            // Footnote: hardlinks share an inode and directories carry no payload. Symlink target
            // bytes still count because they are materialized from archive-controlled content.
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

        // Create directory topology without restoring archive modes yet. A valid 0500/0000 parent
        // must not become unwritable before its descendants have been materialized.
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

        // Restore restrictive directory modes only after every descendant exists, deepest-first.
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

# The original function already has #[no_mangle] immediately before its declaration. Reuse that
# attribute for the newly inserted bounded symbol, then restore one attribute for the old symbol.
abi_anchor = 'pub unsafe extern "C" fn cmpct_extract_all(\n    archive: *const Archive,\n    destination: *const c_char,\n) -> c_int {'
if abi_anchor not in text:
    raise SystemExit("ABI anchor missing")
bounded_abi = r'''/// Extract with an explicit archive-wide payload-materialization ceiling.
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

#[no_mangle]
'''
text = text.replace(abi_anchor, bounded_abi + abi_anchor, 1)
lib_path.write_text(text)

header = Path("native/cmpct-core/include/cmpct.h")
h = header.read_text()
h_anchor = "int32_t cmpct_extract_all(const CmpctArchive *archive, const char *destination);"
if h_anchor not in h:
    raise SystemExit("header anchor missing")
h_decl = (
    "int32_t cmpct_extract_all_bounded(\n"
    "    const CmpctArchive *archive,\n"
    "    const char *destination,\n"
    "    uint64_t max_materialized_bytes\n"
    ");\n"
)
h = h.replace(h_anchor, h_decl + h_anchor, 1)
header.write_text(h)

test = Path("tests/native_stream_extract_abi.py")
t = test.read_text()
abi_test_anchor = "    lib.cmpct_extract_all.argtypes = [ctypes.c_void_p, ctypes.c_char_p]\n    lib.cmpct_extract_all.restype = ctypes.c_int32"
if abi_test_anchor not in t:
    raise SystemExit("test ABI anchor missing")
t = t.replace(
    abi_test_anchor,
    "    lib.cmpct_extract_all_bounded.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint64]\n"
    "    lib.cmpct_extract_all_bounded.restype = ctypes.c_int32\n"
    + abi_test_anchor,
    1,
)

tree_anchor = '        (root / "dir" / "small.txt").write_text("small native stream\\n")'
if tree_anchor not in t:
    raise SystemExit("tree anchor missing")
t = t.replace(tree_anchor, tree_anchor + '\n        os.chmod(root / "dir", 0o500)', 1)

extract_anchor = '            destination = Path(td) / "extracted"\n            assert lib.cmpct_extract_all(handle, str(destination).encode()) == 0'
if extract_anchor not in t:
    raise SystemExit("extract anchor missing")
t = t.replace(
    extract_anchor,
    '            limited = Path(td) / "limited"\n'
    '            assert lib.cmpct_extract_all_bounded(handle, str(limited).encode(), 1024) == -4\n'
    '            assert not limited.exists()\n\n'
    + extract_anchor,
    1,
)

mode_anchor = '            assert (destination / "dir" / "small.txt").read_bytes() == (root / "dir" / "small.txt").read_bytes()'
if mode_anchor not in t:
    raise SystemExit("mode anchor missing")
t = t.replace(
    mode_anchor,
    mode_anchor + '\n            assert (os.stat(destination / "dir").st_mode & 0o7777) == 0o500',
    1,
)
test.write_text(t)

# PR #21 recovery was compiling the same guard module twice and used mutable helpers absent from the
# pinned rmpv API. Fix those blockers without weakening any recovery checks.
recovery = Path("native/cmpct-core/src/recovery.rs")
r = recovery.read_text()
r = r.replace('#[path = "msgpack_guard.rs"]\nmod msgpack_guard;\n\n', 'use crate::msgpack_guard;\n\n', 1)
old_map_mut = '''fn map_value_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Value> {
    value
        .as_map_mut()?
        .iter_mut()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
}
'''
new_map_mut = '''fn map_value_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Value> {
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
'''
if old_map_mut not in r:
    raise SystemExit("recovery mutable-map anchor missing")
r = r.replace(old_map_mut, new_map_mut, 1)
r = r.replace('.and_then(Value::as_array_mut)', '.and_then(array_mut)')
recovery.write_text(r)
