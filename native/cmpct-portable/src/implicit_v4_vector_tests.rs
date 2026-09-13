use crate::PortableEntry;
use crate::manifest::{ContentIdentities, FILESYSTEM_MANIFEST, FsKind, FsManifest};

const CONTROL: &[u8] = &[
    148, 4, 149, 205, 1, 160, 210, 196, 101, 54, 0, 205, 3, 232, 205, 3, 232, 144,
    146, 145, 0, 149, 23, 4, 206, 178, 208, 94, 0, 1, 145, 146, 169, 117, 115, 101, 114,
    46, 100, 101, 109, 111, 196, 1, 118, 147, 149, 0, 163, 100, 105, 114, 1, 146, 1, 72,
    192, 149, 3, 178, 47, 122, 122, 45, 97, 108, 112, 104, 97, 45, 104, 97, 114, 100,
    46, 98, 105, 110, 3, 145, 0, 0, 149, 0, 168, 108, 105, 110, 107, 46, 98, 105, 110,
    2, 147, 3, 95, 206, 59, 154, 202, 0, 172, 100, 105, 114, 47, 98, 101, 116, 97,
    46, 98, 105, 110,
];
const ALPHA_SHA: [u8; 32] = [
    20, 196, 126, 47, 46, 193, 62, 104, 158, 159, 116, 75, 189, 31, 242, 151, 218, 61,
    251, 35, 161, 249, 231, 212, 155, 90, 11, 255, 123, 22, 236, 4,
];
const BETA_SHA: [u8; 32] = [
    50, 128, 137, 7, 39, 92, 19, 159, 158, 132, 133, 60, 160, 83, 191, 152, 245, 190,
    61, 124, 249, 27, 55, 1, 241, 104, 47, 34, 245, 13, 166, 75,
];

fn graph() -> (Vec<PortableEntry>, ContentIdentities) {
    let entries = vec![
        PortableEntry {
            path: FILESYSTEM_MANIFEST.into(),
            size: CONTROL.len() as u64,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        },
        PortableEntry {
            path: "dir/alpha.bin".into(),
            size: 100,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        },
        PortableEntry {
            path: "dir/beta.bin".into(),
            size: 68,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        },
    ];
    let mut identities = ContentIdentities::new();
    identities.insert(FILESYSTEM_MANIFEST.into(), (CONTROL.len() as u64, [0; 32]));
    identities.insert("dir/alpha.bin".into(), (100, ALPHA_SHA));
    identities.insert("dir/beta.bin".into(), (68, BETA_SHA));
    (entries, identities)
}

#[test]
fn independent_python_vector_reconstructs_exact_rust_manifest() {
    // These 115 control bytes are the independent Python-generated vector committed at
    // tests/conformance/v030-r25-implicit-v4-native.json. Keeping the test dependency-free means the
    // portable crate can prove cross-language wire parity without a second JSON/base64 parser becoming
    // part of the native acceptance surface.
    let (graph, identities) = graph();
    let manifest = FsManifest::parse_with_identities(CONTROL, &graph, &identities).unwrap();
    let entries = manifest.entries();
    assert_eq!(entries.len(), 5);

    let dir = &entries[0];
    assert_eq!(dir.path, "dir");
    assert!(matches!(dir.kind, FsKind::Directory));
    assert_eq!((dir.metadata.mode, dir.metadata.mtime_ns, dir.metadata.uid, dir.metadata.gid), (488, -1_000_000_000, 1000, 1000));

    let alpha = &entries[1];
    assert_eq!(alpha.path, "dir/alpha.bin");
    assert_eq!((alpha.metadata.mode, alpha.metadata.mtime_ns, alpha.metadata.uid, alpha.metadata.gid), (416, -1_000_000_000, 1000, 1000));
    match alpha.kind {
        FsKind::File { size, sha256 } => {
            assert_eq!(size, 100);
            assert_eq!(sha256, ALPHA_SHA);
        }
        _ => panic!("alpha did not reconstruct as a regular file"),
    }

    let beta = &entries[2];
    assert_eq!(beta.path, "dir/beta.bin");
    assert_eq!((beta.metadata.mode, beta.metadata.mtime_ns, beta.metadata.uid, beta.metadata.gid), (420, 2_000_000_000, 1001, 1000));
    assert_eq!(beta.metadata.xattrs, vec![("user.demo".into(), b"v".to_vec())]);
    match beta.kind {
        FsKind::File { size, sha256 } => {
            assert_eq!(size, 68);
            assert_eq!(sha256, BETA_SHA);
        }
        _ => panic!("beta did not reconstruct as a regular file"),
    }

    let hard = &entries[3];
    assert_eq!(hard.path, "dir/zz-alpha-hard.bin");
    match &hard.kind {
        FsKind::Hardlink { target } => assert_eq!(target, "dir/alpha.bin"),
        _ => panic!("hardlink did not reconstruct from regular-owner index"),
    }

    let link = &entries[4];
    assert_eq!(link.path, "link.bin");
    assert_eq!((link.metadata.mode, link.metadata.mtime_ns, link.metadata.uid, link.metadata.gid), (511, 0, 1000, 1000));
    match &link.kind {
        FsKind::Symlink { target } => assert_eq!(target, "dir/beta.bin"),
        _ => panic!("symlink did not reconstruct"),
    }
}
