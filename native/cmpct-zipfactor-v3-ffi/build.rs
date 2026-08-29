use std::{env, fs, path::PathBuf};

fn main() {
    let manifest = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let source = manifest
        .join("../cmpct-portable/src/bin/cmpct-zipfactor-v3-preparity.rs")
        .canonicalize()
        .expect("canonical preparity source");
    println!("cargo:rerun-if-changed={}", source.display());

    let raw = fs::read_to_string(&source).expect("read preparity verifier source");
    // `include!` inside a module cannot accept the binary crate's leading inner doc comments. Strip only the
    // documentation marker; every executable token remains sourced from the exact preparity verifier.
    let generated = raw
        .lines()
        .map(|line| {
            line.strip_prefix("//!")
                .map_or(line.to_owned(), |rest| format!("//{rest}"))
        })
        .collect::<Vec<_>>()
        .join("\n");

    // The preparity verifier is path-oriented because it is also a standalone CLI. For the in-process research
    // ABI, expose the same parser/verifier over an already-resident byte slice so callers do not have to publish
    // and reopen an otherwise transient CMP25Z3 reconstruction. These textual rewrites split I/O from the semantic
    // owner; parsing, authentication, logical identity, locality and decode-unit checks remain source-owned here.
    let parse_old = "fn parse(path: &Path) -> Result<Parsed, String> {\n    let raw = fs::read(path).map_err(|e| format!(\"read archive: {e}\"))?;";
    let parse_new = "fn parse_bytes(raw: &[u8]) -> Result<Parsed, String> {";
    let before_parse = generated.clone();
    let mut generated = generated.replacen(parse_old, parse_new, 1);
    assert_ne!(
        generated, before_parse,
        "preparity parse rewrite did not apply"
    );

    // In the standalone owner `raw` is a Vec<u8>, so its parser correctly passes `&raw` to slice helpers. After
    // the signature rewrite above `raw` is already `&[u8]`; normalize only the rewritten parser body.
    let parse_start = generated
        .find(parse_new)
        .expect("rewritten preparity parser start");
    let verify_marker = "\nfn verify(path: &Path) -> Result<(), String> {";
    let parse_end = generated[parse_start..]
        .find(verify_marker)
        .map(|offset| parse_start + offset)
        .expect("preparity verifier marker after parser");
    let parse_body = &generated[parse_start..parse_end];
    let normalized_parse_body = parse_body.replace("&raw", "raw");
    assert_ne!(
        normalized_parse_body, parse_body,
        "preparity slice-borrow normalization did not apply"
    );
    generated.replace_range(parse_start..parse_end, &normalized_parse_body);

    // The standalone verifier reconstructs each logical ZIP into a Vec and then hashes that Vec. For the FFI-only
    // timed research path, stream the byte-identical reconstruction directly through SHA-256 while tracking its exact
    // length and local-header offsets. This removes only a transient allocation/copy; every field emitted by
    // `rebuild_zip`, plus size/SHA/locality checks, is retained. The original reconstruction function remains in the
    // generated module as a source-parity reference but is unused by the optimized FFI path.
    let stream_helper = r#"
fn hash_rebuilt_zip(
    template: &Template,
    dynamics: &[(u32, u32, u32, Vec<u8>)],
) -> Result<(u64, [u8; 32]), String> {
    if dynamics.len() != template.rows.len() {
        return Err("dynamic member count mismatch".into());
    }
    fn emit(hasher: &mut Sha256, length: &mut usize, bytes: &[u8]) -> Result<(), String> {
        hasher.update(bytes);
        *length = length
            .checked_add(bytes.len())
            .ok_or_else(|| "reconstructed length overflow".to_string())?;
        Ok(())
    }

    let mut hasher = Sha256::new();
    let mut length = 0usize;
    let mut offsets = Vec::with_capacity(template.rows.len());
    for (row, (crc, csize, usize_, payload)) in template.rows.iter().zip(dynamics) {
        if payload.len() != *csize as usize {
            return Err("compressed payload length mismatch".into());
        }
        offsets.push(u32::try_from(length).map_err(|_| "local offset exceeds u32")?);
        emit(&mut hasher, &mut length, &LOCAL.to_le_bytes())?;
        for v in [row.version, row.flags, row.method, row.mtime, row.mdate] {
            emit(&mut hasher, &mut length, &v.to_le_bytes())?;
        }
        emit(&mut hasher, &mut length, &crc.to_le_bytes())?;
        emit(&mut hasher, &mut length, &csize.to_le_bytes())?;
        emit(&mut hasher, &mut length, &usize_.to_le_bytes())?;
        emit(
            &mut hasher,
            &mut length,
            &u16::try_from(row.name.len()).map_err(|_| "name too long")?.to_le_bytes(),
        )?;
        emit(
            &mut hasher,
            &mut length,
            &u16::try_from(row.local_extra.len()).map_err(|_| "extra too long")?.to_le_bytes(),
        )?;
        emit(&mut hasher, &mut length, &row.name)?;
        emit(&mut hasher, &mut length, &row.local_extra)?;
        emit(&mut hasher, &mut length, payload)?;
    }
    let cd_start = u32::try_from(length).map_err(|_| "central offset exceeds u32")?;
    for ((row, (crc, csize, usize_, _)), offset) in template.rows.iter().zip(dynamics).zip(offsets)
    {
        emit(&mut hasher, &mut length, &CENTRAL.to_le_bytes())?;
        for v in [
            row.made,
            row.needed,
            row.cflags,
            row.cmethod,
            row.cmtime,
            row.cmdate,
        ] {
            emit(&mut hasher, &mut length, &v.to_le_bytes())?;
        }
        emit(&mut hasher, &mut length, &crc.to_le_bytes())?;
        emit(&mut hasher, &mut length, &csize.to_le_bytes())?;
        emit(&mut hasher, &mut length, &usize_.to_le_bytes())?;
        emit(
            &mut hasher,
            &mut length,
            &u16::try_from(row.name.len()).map_err(|_| "name too long")?.to_le_bytes(),
        )?;
        emit(
            &mut hasher,
            &mut length,
            &u16::try_from(row.central_extra.len())
                .map_err(|_| "central extra too long")?
                .to_le_bytes(),
        )?;
        emit(
            &mut hasher,
            &mut length,
            &u16::try_from(row.central_comment.len())
                .map_err(|_| "central comment too long")?
                .to_le_bytes(),
        )?;
        emit(&mut hasher, &mut length, &row.disk.to_le_bytes())?;
        emit(&mut hasher, &mut length, &row.internal_attr.to_le_bytes())?;
        emit(&mut hasher, &mut length, &row.external_attr.to_le_bytes())?;
        emit(&mut hasher, &mut length, &offset.to_le_bytes())?;
        emit(&mut hasher, &mut length, &row.name)?;
        emit(&mut hasher, &mut length, &row.central_extra)?;
        emit(&mut hasher, &mut length, &row.central_comment)?;
    }
    let cd_size = u32::try_from(length).map_err(|_| "central size exceeds u32")? - cd_start;
    let count = u16::try_from(template.rows.len()).map_err(|_| "entry count exceeds u16")?;
    emit(&mut hasher, &mut length, &EOCD.to_le_bytes())?;
    emit(&mut hasher, &mut length, &template.disk.to_le_bytes())?;
    emit(&mut hasher, &mut length, &template.disk_cd.to_le_bytes())?;
    emit(&mut hasher, &mut length, &count.to_le_bytes())?;
    emit(&mut hasher, &mut length, &count.to_le_bytes())?;
    emit(&mut hasher, &mut length, &cd_size.to_le_bytes())?;
    emit(&mut hasher, &mut length, &cd_start.to_le_bytes())?;
    emit(
        &mut hasher,
        &mut length,
        &u16::try_from(template.comment.len())
            .map_err(|_| "comment too long")?
            .to_le_bytes(),
    )?;
    emit(&mut hasher, &mut length, &template.comment)?;
    Ok((
        u64::try_from(length).map_err(|_| "reconstructed length exceeds u64")?,
        hasher.finalize().into(),
    ))
}

"#;
    let before_helper = generated.clone();
    generated = generated.replacen(parse_new, &format!("{stream_helper}{parse_new}"), 1);
    assert_ne!(
        generated, before_helper,
        "streaming ZIP-factor identity helper injection did not apply"
    );
    let rebuild_marker = "fn rebuild_zip(\n";
    let before_dead_code = generated.clone();
    generated = generated.replacen(rebuild_marker, "#[allow(dead_code)]\nfn rebuild_zip(\n", 1);
    assert_ne!(
        generated, before_dead_code,
        "rebuild reference dead-code annotation did not apply"
    );

    let verify_old =
        "fn verify(path: &Path) -> Result<(), String> {\n    let parsed = parse(path)?;";
    let verify_new = "fn verify_parsed(parsed: Parsed) -> Result<(), String> {";
    let before_verify = generated.clone();
    generated = generated.replacen(verify_old, verify_new, 1);
    assert_ne!(
        generated, before_verify,
        "preparity verify rewrite did not apply"
    );

    let identity_old = r#"            let restored = rebuild_zip(&parsed.template, &dynamics)?;
            let (expected_size, expected_sha) = parsed.regular.get(rel).unwrap();
            if restored.len() as u64 != *expected_size || sha(&restored) != *expected_sha {
                return Err(format!("reconstructed identity mismatch: {rel}"));
            }"#;
    let identity_new = r#"            let (restored_size, restored_sha) = hash_rebuilt_zip(&parsed.template, &dynamics)?;
            let (expected_size, expected_sha) = parsed.regular.get(rel).unwrap();
            if restored_size != *expected_size || restored_sha != *expected_sha {
                return Err(format!("reconstructed identity mismatch: {rel}"));
            }"#;
    let before_identity = generated.clone();
    generated = generated.replacen(identity_old, identity_new, 1);
    assert_ne!(
        generated, before_identity,
        "streaming reconstructed-identity rewrite did not apply"
    );

    let main_marker = "\nfn main() {";
    let wrappers = r#"

fn parse(path: &Path) -> Result<Parsed, String> {
    let raw = fs::read(path).map_err(|e| format!("read archive: {e}"))?;
    parse_bytes(&raw)
}

fn verify(path: &Path) -> Result<(), String> {
    verify_parsed(parse(path)?)
}

fn verify_slice(raw: &[u8]) -> Result<(), String> {
    verify_parsed(parse_bytes(raw)?)
}
"#;
    let before_wrappers = generated.clone();
    generated = generated.replacen(main_marker, &format!("{wrappers}{main_marker}"), 1);
    assert_ne!(
        generated, before_wrappers,
        "preparity byte-slice wrappers did not apply"
    );

    let out =
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("zipfactor_v3_preparity.rs");
    fs::write(out, format!("{generated}\n")).expect("write generated preparity source");
}