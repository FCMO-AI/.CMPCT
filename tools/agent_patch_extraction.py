from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)


def replace_if_present(text: str, old: str, new: str) -> str:
    return text.replace(old, new, 1) if old in text else text


# The behavior-validated extraction patch is already on this branch. Keep this finalizer idempotent and
# fail closed if a later rewrite silently drops either resource bound or the bounded public ABI.
lib_path = Path("native/cmpct-core/src/lib.rs")
lib = lib_path.read_text()
for invariant in (
    "const MAX_EXTRACT_OUTPUT_BYTES: u64 = 64 * 1024 * 1024 * 1024;",
    "pub fn extract_all_bounded(",
    "pub unsafe extern \"C\" fn cmpct_extract_all_bounded(",
):
    if invariant not in lib:
        raise SystemExit(f"missing validated extraction invariant: {invariant}")

# Strict Clippy exposed unsafe ABI functions whose contracts were only implicit. Document the pointer
# validity/lifetime rules instead of suppressing missing_safety_doc; these are part of the C boundary.
safety_docs = {
    "/// Copy an entry path as UTF-8. Passing a null buffer with capacity zero is a size query.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_path(":
        "/// Copy an entry path as UTF-8. Passing a null buffer with capacity zero is a size query.\n///\n/// # Safety\n/// `archive` must be live; `out_len` must be writable; when non-null, `buffer` must be writable for\n/// `capacity` bytes for the duration of the call.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_path(",
    "/// Run complete native structural preflight without extracting payloads.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_preflight(archive: *const Archive) -> c_int {":
        "/// Run complete native structural preflight without extracting payloads.\n///\n/// # Safety\n/// `archive` must be a live pointer returned by `cmpct_open`.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_preflight(archive: *const Archive) -> c_int {",
    "/// Read one bounded logical range. `out_read` is zero on every failure.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_read_range(":
        "/// Read one bounded logical range. `out_read` is zero on every failure.\n///\n/// # Safety\n/// `archive` must be live; `out_read` must be writable; when `length > 0`, `buffer` must be writable\n/// for at least `length` bytes for the duration of the call.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_read_range(",
    "/// Open a sequential logical stream. The archive handle must outlive the stream.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_stream_open(":
        "/// Open a sequential logical stream. The archive handle must outlive the stream.\n///\n/// # Safety\n/// `archive` must be live and remain live until the returned stream is closed; `out` must be writable.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_entry_stream_open(",
    "/// Read the next sequential stream bytes; EOF is `CMPCT_OK` with `out_read == 0`.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_stream_read(":
        "/// Read the next sequential stream bytes; EOF is `CMPCT_OK` with `out_read == 0`.\n///\n/// # Safety\n/// `stream` must be a live handle; `out_read` must be writable; when `capacity > 0`, `buffer` must be\n/// writable for at least `capacity` bytes for the duration of the call.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_stream_read(",
    "#[no_mangle]\npub unsafe extern \"C\" fn cmpct_stream_close(stream: *mut CmpctStream) {":
        "/// Close a stream previously returned by `cmpct_entry_stream_open`.\n///\n/// # Safety\n/// `stream` must be null or a live handle returned by `cmpct_entry_stream_open`, and it must not be\n/// closed more than once.\n#[no_mangle]\npub unsafe extern \"C\" fn cmpct_stream_close(stream: *mut CmpctStream) {",
}
for old, new in safety_docs.items():
    lib = replace_if_present(lib, old, new)
lib_path.write_text(lib)

# `Unavailable` is a real cross-platform contract but cannot be constructed on Unix, where the stock
# zlib ABI is compiled in. Scope the variant to the targets that can actually return it.
deflate_path = Path("native/cmpct-core/src/deflate_regen.rs")
deflate = deflate_path.read_text()
deflate = replace_if_present(
    deflate,
    "    #[error(\"stock zlib regeneration backend is unavailable on this target\")]\n    Unavailable,",
    "    #[cfg(not(unix))]\n    #[error(\"stock zlib regeneration backend is unavailable on this target\")]\n    Unavailable,",
)
deflate_path.write_text(deflate)

# These recovery fields were diagnostic leftovers and had no reader or test consumer. Removing them
# shrinks the recovery result to the only two values that affect trust: the authenticated index and the
# committed data boundary.
recovery_path = Path("native/cmpct-core/src/recovery.rs")
recovery = recovery_path.read_text()
recovery = replace_if_present(recovery, "    pub footer_pos: u64,\n    pub delta_depth: usize,\n", "")
recovery = replace_if_present(recovery, "                footer_pos,\n                delta_depth: depth,\n", "")
# `depth` remains the hard generation bound used by the loop; silence no warnings by changing policy.
recovery_path.write_text(recovery)

# All frozen revision-24 virtual-ZIP modes now use parse_recipe directly. Remove the obsolete stored-only
# compatibility wrapper rather than retaining dead public surface.
vzip_path = Path("native/cmpct-core/src/vzip.rs")
vzip = vzip_path.read_text()
wrapper = '''/// Compatibility name retained for older focused tests. All currently frozen revision-24 stream
/// modes are parsed by the same implementation; the wrapper no longer means "stored-only".
pub fn parse_stored_recipe(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    parse_recipe(value, blob_sizes, entry_logical_size)
}

'''
vzip = replace_if_present(vzip, wrapper, "")
vzip_path.write_text(vzip)

# Keep the complete-member integrity check explicit but Clippy-clean; no behavior changes.
dispatch_path = Path("native/cmpct-core/src/vzip_dispatch.rs")
dispatch = dispatch_path.read_text()
dispatch = replace_if_present(
    dispatch,
    '''    if start == 0 && end == recipe.logical_size {
        if Sha256::digest(&*out).as_slice() != recipe.logical_sha256 {
            return Err(VirtualZipDispatchError::LogicalHash);
        }
    }
''',
    '''    if start == 0
        && end == recipe.logical_size
        && Sha256::digest(&*out).as_slice() != recipe.logical_sha256
    {
        return Err(VirtualZipDispatchError::LogicalHash);
    }
''',
)
dispatch_path.write_text(dispatch)
