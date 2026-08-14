use cmpct_core::Archive;
use serde_json::json;
use std::env;
use std::io::{self, Write};
use std::path::Path;

const MAX_CLI_RANGE_BYTES: u64 = 64 * 1024 * 1024;

fn usage() -> ! {
    eprintln!(
        "usage:\n  cmpct-native info ARCHIVE.cmpct\n  cmpct-native list ARCHIVE.cmpct\n  cmpct-native range ARCHIVE.cmpct MEMBER OFFSET LENGTH"
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
            let Some((entry_index, entry)) = archive
                .entries()
                .iter()
                .enumerate()
                .find(|(_, entry)| entry.path == member)
            else {
                eprintln!("member not found: {member}");
                std::process::exit(3);
            };
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
            let length = usize::try_from(length).unwrap_or_else(|_| {
                eprintln!("requested range exceeds this platform's address space");
                std::process::exit(2);
            });
            let mut output = vec![0u8; length];
            archive
                .read_range(entry_index, offset, &mut output)
                .unwrap_or_else(|e| {
                    eprintln!("{e}");
                    std::process::exit(4);
                });

            // Footnote: range writes raw bytes to stdout so shell/file-manager adapters can consume
            // member data without JSON/base64 inflation or importing the Python encoder stack.
            io::stdout().write_all(&output).unwrap_or_else(|e| {
                eprintln!("stdout write failed: {e}");
                std::process::exit(5);
            });
        }
        _ => usage(),
    }
}
