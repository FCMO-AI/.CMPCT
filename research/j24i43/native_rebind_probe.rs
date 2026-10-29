//! J24I43: deterministic physical rename/rebind ownership discriminator, Linux.
use cmpct_core::Archive;
use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 4, "probe AUTHENTIC CMPCT_MUTANT SCRATCH_DIR");
    let source = PathBuf::from(&args[1]);
    let mutant = PathBuf::from(&args[2]);
    let root = PathBuf::from(&args[3]);
    fs::create_dir_all(&root).unwrap();
    let initial = root.join("active.cmpct");
    let detached = root.join("held-inode.cmpct");
    if initial.exists() { fs::remove_file(&initial).unwrap(); }
    if detached.exists() { fs::remove_file(&detached).unwrap(); }
    fs::copy(&source, &initial).unwrap();
    // Keep the original inode open, then change only the path's inode.
    let owned = Archive::open(&initial).expect("open authentic archive before rebind");
    assert_eq!(owned.entries().len(), 1);
    fs::rename(&initial, &detached).expect("rename original inode");
    fs::copy(&mutant, &initial).expect("install hostile file at original path");
    assert_eq!(owned.verify_complete().expect("owned original inode must survive path rebind"), 1);
    let replaced = Archive::open(&initial).expect("mutant index remains self-checksummed");
    assert!(replaced.verify_complete().is_err(), "rebound path's corrupted stream must be rejected");
    println!("J24I43_REBIND_PASS original_fd_survived=true new_path_rejected=true");
}
