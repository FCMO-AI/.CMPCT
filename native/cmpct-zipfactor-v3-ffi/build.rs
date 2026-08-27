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
    // ABI, expose the exact same parser/verifier over an already-resident byte slice so callers do not have to
    // publish and reopen an otherwise transient CMP25Z3 reconstruction. These textual rewrites only split I/O
    // from the existing semantic owner; all parsing, SHA-256, reconstruction and locality logic remains verbatim.
    let parse_old = "fn parse(path: &Path) -> Result<Parsed, String> {\n    let raw = fs::read(path).map_err(|e| format!(\"read archive: {e}\"))?;";
    let parse_new = "fn parse_bytes(raw: &[u8]) -> Result<Parsed, String> {";
    let before_parse = generated.clone();
    let mut generated = generated.replacen(parse_old, parse_new, 1);
    assert_ne!(
        generated, before_parse,
        "preparity parse rewrite did not apply"
    );

    // In the standalone owner `raw` is a Vec<u8>, so its parser correctly passes `&raw` to slice helpers. After
    // the signature rewrite above `raw` is already `&[u8]`; retaining those borrows creates `&&[u8]` and newer
    // Clippy rejects them as needless borrows. Normalize only the rewritten parser body, leaving the standalone
    // source and the path wrapper untouched. This changes no parser semantics or archive bytes.
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

    let verify_old =
        "fn verify(path: &Path) -> Result<(), String> {\n    let parsed = parse(path)?;";
    let verify_new = "fn verify_parsed(parsed: Parsed) -> Result<(), String> {";
    let before_verify = generated.clone();
    generated = generated.replacen(verify_old, verify_new, 1);
    assert_ne!(
        generated, before_verify,
        "preparity verify rewrite did not apply"
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
