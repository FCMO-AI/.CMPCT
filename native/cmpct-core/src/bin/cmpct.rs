use cmpct_core::Archive;
use serde_json::json;
use std::env;
use std::io::{self, Write};
use std::path::Path;

const MAX_CLI_RANGE_BYTES: u64 = 64 * 1024 * 1024;
const MAX_CLI_READ_BYTES: u64 = 64 * 1024 * 1024;

fn usage() -> ! {
    eprintln!(
        "usage:\n  cmpct-native info ARCHIVE.cmpct\n  cmpct-native list ARCHIVE.cmpct\n  cmpct-native stat ARCHIVE.cmpct MEMBER\n  cmpct-native read ARCHIVE.cmpct MEMBER\n  cmpct-native range ARCHIVE.cmpct MEMBER OFFSET LENGTH"
    );
    std::process::exit(2);
}

fn open(path: &str) -> Archive {
    Archive::open(Path::new(path)).unwrap_or_else(|e| {
        eprintln!("{e}");
        std::process::exit(2);
    })
}

fn parse_u64(value: Option<String>, label: &str) -> u64 {
    value
        .unwrap_or_else(|| usage())
        .parse::<u64>()
        .unwrap_or_else(|_| {
            eprintln!("invalid {label}");
            std::process::exit(2);
        })
}

fn entry_index(archive: &Archive, member: &str) -> usize {
    archive
        .entries()
        .iter()
        .position(|entry| entry.path == member)
        .unwrap_or_else(|| {
            eprintln!("member not found: {member}");
            std::process::exit(3);
        })
}

fn write_member_bytes(archive: &Archive, entry_index: usize, offset: u64, length: u64) {
    let length = usize::try_from(length).unwrap_or_else(|_| {
        eprintln!("requested output exceeds this platform's address space");
        std::process::exit(2);
    });
    let mut output = vec![0u8; length];
    archive
        .read_range(entry_index, offset, &mut output)
        .unwrap_or_else(|e| {
            eprintln!("{e}");
            std::process::exit(4);
        });

    // Footnote: raw stdout keeps the native process surface composable for shell/file-manager
    // adapters and avoids JSON/base64 inflation. Resource caps are checked before allocation.
    io::stdout().write_all(&output).unwrap_or_else(|e| {
        eprintln!("stdout write failed: {e}");
        std::process::exit(5);
    });
}

fn main() {
    let mut args = env::args().skip(1);
    let command = args.next().unwrap_or_else(|| usage());
    let archive_path = args.next().unwrap_or_else(|| usage());

    match command.as_str() {
        "info" => {
            if args.next().is_some() {
                usage();
            }
            let archive = open(&archive_path);
            println!(
                "{}",
                serde_json::to_string(&json!({
                    "revision": archive.revision(),
                    "entries": archive.entries().len(),
                }))
                .expect("serializing fixed native archive info cannot fail")
            );
        }
        "list" => {
            if args.next().is_some() {
                usage();
            }
            let archive = open(&archive_path);
            let entries = archive
                .entries()
                .iter()
                .map(|entry| {
                    json!({
                        "path": entry.path,
                        "kind": entry.kind,
                        "mode": entry.mode,
                        "mtime_ns": entry.mtime_ns,
                        "size": entry.size,
                    })
                })
                .collect::<Vec<_>>();
            println!(
                "{}",
                serde_json::to_string(&entries)
                    .expect("serializing authenticated native entries cannot fail")
            );
        }
        "stat" => {
            let member = args.next().unwrap_or_else(|| usage());
            if args.next().is_some() {
                usage();
            }
            let archive = open(&archive_path);
            let index = entry_index(&archive, &member);
            let entry = &archive.entries()[index];
            println!(
                "{}",
                serde_json::to_string(&json!({
                    "path": entry.path,
                    "kind": entry.kind,
                    "mode": entry.mode,
                    "mtime_ns": entry.mtime_ns,
                    "size": entry.size,
                }))
                .expect("serializing authenticated native entry metadata cannot fail")
            );
        }
        "read" => {
            let member = args.next().unwrap_or_else(|| usage());
            if args.next().is_some() {
                usage();
            }
            let archive = open(&archive_path);
            let index = entry_index(&archive, &member);
            let entry = &archive.entries()[index];
            if entry.kind != 0 {
                eprintln!("member is not a regular file: {member}");
                std::process::exit(3);
            }
            if entry.size > MAX_CLI_READ_BYTES {
                eprintln!("member exceeds the native CLI 64 MiB whole-read limit; use range");
                std::process::exit(2);
            }
            write_member_bytes(&archive, index, 0, entry.size);
        }
        "range" => {
            let member = args.next().unwrap_or_else(|| usage());
            let offset = parse_u64(args.next(), "offset");
            let length = parse_u64(args.next(), "length");
            if args.next().is_some() {
                usage();
            }
            if length > MAX_CLI_RANGE_BYTES {
                eprintln!("requested range exceeds the native CLI 64 MiB output limit");
                std::process::exit(2);
            }

            let archive = open(&archive_path);
            let index = entry_index(&archive, &member);
            let entry = &archive.entries()[index];
            if entry.kind != 0 {
                eprintln!("member is not a regular file: {member}");
                std::process::exit(3);
            }
            let end = offset.checked_add(length).unwrap_or_else(|| {
                eprintln!("requested range overflows logical offsets");
                std::process::exit(2);
            });
            if end > entry.size {
                eprintln!("requested range is outside the logical file");
                std::process::exit(3);
            }
            write_member_bytes(&archive, index, offset, length);
        }
        _ => usage(),
    }
}
