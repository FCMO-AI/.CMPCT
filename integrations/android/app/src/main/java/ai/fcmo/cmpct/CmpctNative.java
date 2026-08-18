package ai.fcmo.cmpct;

import java.io.Closeable;
import java.io.IOException;

/** Thin Java ownership layer over the shared CMPCT r24/r25 portable native reader. */
final class CmpctNative {
    static final int KIND_FILE = 0;
    static final int KIND_DIR = 1;
    static final int KIND_SYMLINK = 2;
    static final int KIND_HARDLINK = 3;
    static final int MAX_BRIDGE_READ = 1024 * 1024;

    static {
        // Footnote: cmpct_android is only a JNI shim. It links libcmpct_portable.so so Android uses the
        // same r24 delegation, canonical-r25 admission/recovery checks and range semantics as desktop.
        System.loadLibrary("cmpct_android");
    }

    private CmpctNative() {}

    static final class Entry {
        final int index;
        final String path;
        final int kind;
        final long mode;
        final long size;
        final long mtimeNs;

        Entry(int index, String path, long[] info) throws IOException {
            if (info == null || info.length != 4) {
                throw new IOException("CMPCT native entry metadata has an invalid shape");
            }
            this.index = index;
            this.path = path;
            this.kind = (int) info[0];
            this.mode = info[1];
            this.size = info[2];
            this.mtimeNs = info[3];
        }
    }

    static final class Archive implements Closeable {
        private long handle;

        Archive(String path) throws IOException {
            handle = nativeOpen(path);
            if (handle == 0) {
                throw new IOException("CMPCT native core returned a null archive handle");
            }
        }

        int revision() throws IOException {
            ensureOpen();
            return nativeRevision(handle);
        }

        int entryCount() throws IOException {
            ensureOpen();
            return nativeEntryCount(handle);
        }

        Entry entry(int index) throws IOException {
            ensureOpen();
            return new Entry(index, nativeEntryPath(handle, index), nativeEntryInfo(handle, index));
        }

        int findEntry(String path) throws IOException {
            int count = entryCount();
            for (int i = 0; i < count; i++) {
                if (nativeEntryPath(handle, i).equals(path)) {
                    return i;
                }
            }
            return -1;
        }

        byte[] readRange(int index, long offset, int length) throws IOException {
            ensureOpen();
            if (offset < 0 || length < 0 || length > MAX_BRIDGE_READ) {
                throw new IOException("Invalid CMPCT bridge range request");
            }
            return nativeReadRange(handle, index, offset, length);
        }

        private void ensureOpen() throws IOException {
            if (handle == 0) {
                throw new IOException("CMPCT archive is already closed");
            }
        }

        @Override
        public void close() {
            if (handle != 0) {
                nativeClose(handle);
                handle = 0;
            }
        }
    }

    private static native long nativeOpen(String path) throws IOException;
    private static native void nativeClose(long handle);
    private static native int nativeRevision(long handle) throws IOException;
    private static native int nativeEntryCount(long handle) throws IOException;
    private static native String nativeEntryPath(long handle, int index) throws IOException;
    private static native long[] nativeEntryInfo(long handle, int index) throws IOException;
    private static native byte[] nativeReadRange(long handle, int index, long offset, int length) throws IOException;
}
