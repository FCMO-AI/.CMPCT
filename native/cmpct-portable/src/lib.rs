mod canonical;
mod format;
mod g04;
mod identity;
mod manifest;
mod prefix;
#[doc(hidden)]
pub mod zipfactor;

#[doc(hidden)]
pub use crate::canonical::Canonical25Archive;
use crate::format::safe_relpath;
#[doc(hidden)]
pub use crate::g04::G04Archive;
use crate::identity::{R25Identity, classify};
#[doc(hidden)]
pub use crate::prefix::PrefixArchive;
use cmpct_core::Archive as R24Archive;
use std::ffi::CStr;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::os::raw::{c_char, c_int};
use std::path::{Path, PathBuf};
use std::ptr;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;

const R24_MAGIC: &[u8; 8] = b"CMPCT24\0";
const R24_VERIFY_MATERIALIZE_LIMIT: u64 = 256 * 1024 * 1024;

#[derive(Debug, Error)]
pub enum PortableError {