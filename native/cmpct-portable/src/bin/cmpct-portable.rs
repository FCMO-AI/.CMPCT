use cmpct_portable::{PortableArchive, PortableError};
use std::env;
use std::io::{self, Write};
use std::path::PathBuf;

fn usage() -> ! {
    eprintln!(
        "usage:\n  cmpct-portable info <archive>\n  cmpct-portable list <archive>\n  cmpct-portable verify <archive>\n  cmpct-portable read <archive> <member>\n  cmpct-portable member-stats <archive> <member>\n  cmpct-portable extract <archive> <destination>\n  cmpct-portable export-zip <archive> <destination.zip>"
    );
    std::process::exit(2)
}

fn open(path: &str) -> Result<PortableArchive, PortableError> {
    PortableArchive::open(&PathBuf::from(path))
}

fn run() -> Result<(), PortableError> {
    let mut args = env::args().skip(1);
    let Some(command) = args.next() else { usage() };
    let Some(archive_path) = args.next() else {
        usage()
    };
    let archive = open(&archive_path)?;
    match command.as_str() {
        "info" => {
            if args.next().is_some() {
                usage();
            }
            let entries = archive.entries();
            let logical_regular_bytes = entries
                .iter()
                .filter(|entry| entry.kind == 0)
                .try_fold(0u64, |total, entry| {
                    total.checked_add(entry.size).ok_or_else(|| {
                        PortableError::Limit("public regular-file byte total overflow".into())
                    })
                })?;
            println!("profile={}", archive.profile().as_str());
            println!("revision={}", archive.revision());
            println!("entries={}", entries.len());
            println!("logical_regular_bytes={logical_regular_bytes}");
            println!(
                "tail_metadata_authenticated={}",
                archive.tail_metadata_authenticated()
            );
            if let Some(amplification) = archive.declared_member_read_amplification() {
                println!("declared_max_member_read_amplification={amplification:.3}");
            }
        }
        "list" => {
            if args.next().is_some() {
                usage();
            }
            for (index, entry) in archive.entries().iter().enumerate() {
                println!("{index}\t{}\t{}\t{}", entry.kind, entry.size, entry.path);
            }
        }
        "verify" => {
            if args.next().is_some() {
                usage();
            }
            archive.verify()?;
            println!("ok profile={}", archive.profile().as_str());
        }
        "read" => {
            let Some(member) = args.next() else { usage() };
            if args.next().is_some() {
                usage();
            }
            let index = archive
                .entry_index(&member)
                .ok_or_else(|| PortableError::Format(format!("member not found: {member}")))?;
            // Footnote: stdout is intentionally the byte stream. Diagnostics/stats have their own command,
            // keeping this surface safe for shell pipes and CLI-vs-CLI interoperability measurements.
            archive.stream_member(index, io::stdout().lock())?;
        }
        "member-stats" => {
            let Some(member) = args.next() else { usage() };
            if args.next().is_some() {
                usage();
            }
            let index = archive
                .entry_index(&member)
                .ok_or_else(|| PortableError::Format(format!("member not found: {member}")))?;
            let stats = archive.member_stats(index)?;
            println!("profile={}", stats.profile);
            println!("logical_bytes={}", stats.logical_bytes);
            println!("decoded_context_bytes={}", stats.decoded_context_bytes);
            println!("amplification={:.6}", stats.amplification);
        }
        "extract" => {
            let Some(destination) = args.next() else {
                usage()
            };
            if args.next().is_some() {
                usage();
            }
            archive.extract_transactional(&PathBuf::from(destination))?;
        }
        "export-zip" => {
            let Some(destination) = args.next() else {
                usage()
            };
            if args.next().is_some() {
                usage();
            }
            archive.export_zip(&PathBuf::from(destination))?;
        }
        _ => usage(),
    }
    io::stdout().flush()?;
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("cmpct-portable: {error}");
        std::process::exit(1);
    }
}

// Footnote: `revision` is intentionally emitted beside `profile`. Canonical r25 acceptance and Android can
// assert both the exact representation profile and the release grammar revision without re-parsing archive bytes.
// `logical_regular_bytes` is the same public-entry sum used to enforce caller extraction budgets without requiring
// a second full namespace serialization through `list`.
