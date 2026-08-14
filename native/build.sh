#!/usr/bin/env sh
set -eu
# Encoder-only CDC accelerator. Readers never depend on this shared library.
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CC=${CC:-cc}
OUT=${1:-"$HERE/../src/cmpct/libcmpct_cdc.so"}
"$CC" -O3 -shared -fPIC "$HERE/cmpct_cdc.c" -o "$OUT"
printf 'built %s\n' "$OUT"
