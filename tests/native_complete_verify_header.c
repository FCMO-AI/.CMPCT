/* J24I50 — compile the public C declaration with a real non-Rust translation unit.
 * Python ctypes separately resolves and invokes the exported symbol on fixed bytes.
 */
#include "cmpct.h"

int32_t cmpct_verify_header_contract(const CmpctArchive *archive) {
    size_t verified = 0;
    return cmpct_verify_complete(archive, &verified);
}
