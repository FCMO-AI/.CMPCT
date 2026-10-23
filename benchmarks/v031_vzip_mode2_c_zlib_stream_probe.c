/* Research-only O1: stream raw Deflate through native system libz; NOT a product Reader. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
#define MAX_SOURCE_BYTES (1024u * 1024u)
#define BUFFER_BYTES 65536u
static int write_bytes(const unsigned char *p, size_t n) {
    return n && fwrite(p, 1, n, stdout) != n ? -1 : 0;
}
int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("%s\n", zlibVersion());
        return 0;
    }
    if (argc != 3) {
        fputs("usage: probe <level 0..9> <chunk 1..65536>\n", stderr);
        return 2;
    }
    char *end = NULL;
    long level = strtol(argv[1], &end, 10);
    if (!*argv[1] || *end || level < 0 || level > 9) return 2;
    end = NULL;
    long chunk = strtol(argv[2], &end, 10);
    if (!*argv[2] || *end || chunk < 1 || chunk > BUFFER_BYTES) return 2;
    unsigned char input[BUFFER_BYTES], output[BUFFER_BYTES];
    z_stream stream = {0};
    int status = deflateInit2(&stream, (int)level, Z_DEFLATED, -15, 8, Z_DEFAULT_STRATEGY);
    if (status != Z_OK) return 3;
    unsigned long long total = 0;
    int code = 0;
    for (;;) {
        size_t n = fread(input, 1, (size_t)chunk, stdin);
        if (n == 0) {
            if (ferror(stdin)) { code = 4; break; }
            for (;;) {
                stream.next_out = output;
                stream.avail_out = BUFFER_BYTES;
                status = deflate(&stream, Z_FINISH);
                if (status != Z_OK && status != Z_STREAM_END) { code = 5; break; }
                if (write_bytes(output, BUFFER_BYTES - stream.avail_out)) { code = 6; break; }
                if (status == Z_STREAM_END) break;
            }
            break;
        }
        total += n;
        if (total > MAX_SOURCE_BYTES) { fputs("source exceeds 1 MiB budget\n", stderr); code = 7; break; }
        stream.next_in = input;
        stream.avail_in = (uInt)n;
        do {
            stream.next_out = output;
            stream.avail_out = BUFFER_BYTES;
            status = deflate(&stream, Z_NO_FLUSH);
            if (status != Z_OK) { code = 8; break; }
            if (write_bytes(output, BUFFER_BYTES - stream.avail_out)) { code = 9; break; }
        } while (!code && (stream.avail_in || !stream.avail_out));
        if (code) break;
    }
    if (deflateEnd(&stream) != Z_OK && !code) code = 10;
    if (fflush(stdout) && !code) code = 11;
    return code;
}
