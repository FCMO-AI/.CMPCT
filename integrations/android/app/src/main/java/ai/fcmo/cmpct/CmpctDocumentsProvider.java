package ai.fcmo.cmpct;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import android.util.Base64;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Read-only Storage Access Framework view over imported CMPCT archives. */
public final class CmpctDocumentsProvider extends DocumentsProvider {
    private static final ExecutorService STREAMS = Executors.newCachedThreadPool();
    private static final String PREFIX = "a:";
    private static final int COPY_CHUNK = 256 * 1024;

    private static final String[] DEFAULT_ROOT_PROJECTION = new String[] {
            DocumentsContract.Root.COLUMN_ROOT_ID,
            DocumentsContract.Root.COLUMN_DOCUMENT_ID,
            DocumentsContract.Root.COLUMN_TITLE,
            DocumentsContract.Root.COLUMN_FLAGS,
            DocumentsContract.Root.COLUMN_MIME_TYPES
    };

    private static final String[] DEFAULT_DOCUMENT_PROJECTION = new String[] {
            DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE,
            DocumentsContract.Document.COLUMN_FLAGS,
            DocumentsContract.Document.COLUMN_SIZE,
            DocumentsContract.Document.COLUMN_LAST_MODIFIED
    };

    private static final class Id {
        final String archiveId;
        final String path;

        Id(String archiveId, String path) {
            this.archiveId = archiveId;
            this.path = path;
        }
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    static String documentId(String archiveId, String path) {
        String encoded = Base64.encodeToString(
                path.getBytes(StandardCharsets.UTF_8),
                Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING);
        return PREFIX + archiveId + ":" + encoded;
    }

    private static Id parseDocumentId(String documentId) throws FileNotFoundException {
        if (documentId == null || !documentId.startsWith(PREFIX)) {
            throw new FileNotFoundException("Invalid CMPCT document ID");
        }
        int split = documentId.indexOf(':', PREFIX.length());
        if (split < 0) throw new FileNotFoundException("Invalid CMPCT document ID");
        String archiveId = documentId.substring(PREFIX.length(), split);
        if (!archiveId.matches("[0-9a-f]{64}")) {
            throw new FileNotFoundException("Invalid CMPCT archive ID");
        }
        String encoded = documentId.substring(split + 1);
        try {
            String path = new String(
                    Base64.decode(encoded, Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING),
                    StandardCharsets.UTF_8);
            return new Id(archiveId, path);
        } catch (IllegalArgumentException e) {
            throw new FileNotFoundException("Invalid CMPCT path encoding");
        }
    }

    @Override
    public Cursor queryRoots(String[] projection) {
        MatrixCursor result = new MatrixCursor(resolveRootProjection(projection));
        for (ArchiveRegistry.Record record : ArchiveRegistry.all(getContext())) {
            MatrixCursor.RowBuilder row = result.newRow();
            add(row, DocumentsContract.Root.COLUMN_ROOT_ID, record.id);
            add(row, DocumentsContract.Root.COLUMN_DOCUMENT_ID, documentId(record.id, ""));
            add(row, DocumentsContract.Root.COLUMN_TITLE, record.displayName);
            add(row, DocumentsContract.Root.COLUMN_FLAGS,
                    DocumentsContract.Root.FLAG_LOCAL_ONLY |
                    DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD);
            add(row, DocumentsContract.Root.COLUMN_MIME_TYPES, "*/*");
        }
        return result;
    }

    @Override
    public Cursor queryDocument(String documentId, String[] projection) throws FileNotFoundException {
        MatrixCursor result = new MatrixCursor(resolveDocumentProjection(projection));
        Id id = parseDocumentId(documentId);
        ArchiveRegistry.Record record = requireRecord(id.archiveId);
        if (id.path.isEmpty()) {
            addArchiveRoot(result, record);
            return result;
        }
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            int index = archive.findEntry(id.path);
            if (index < 0) throw new FileNotFoundException("CMPCT member no longer exists");
            addEntry(result, record, archive.entry(index));
            return result;
        } catch (IOException e) {
            throw fileNotFound("Unable to read CMPCT archive", e);
        }
    }

    @Override
    public Cursor queryChildDocuments(
            String parentDocumentId, String[] projection, String sortOrder) throws FileNotFoundException {
        MatrixCursor result = new MatrixCursor(resolveDocumentProjection(projection));
        Id parent = parseDocumentId(parentDocumentId);
        ArchiveRegistry.Record record = requireRecord(parent.archiveId);
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            int count = archive.entryCount();
            for (int i = 0; i < count; i++) {
                CmpctNative.Entry entry = archive.entry(i);
                if (parentOf(entry.path).equals(parent.path)) addEntry(result, record, entry);
            }
            return result;
        } catch (IOException e) {
            throw fileNotFound("Unable to enumerate CMPCT archive", e);
        }
    }

    @Override
    public String getDocumentType(String documentId) throws FileNotFoundException {
        Id id = parseDocumentId(documentId);
        if (id.path.isEmpty()) return DocumentsContract.Document.MIME_TYPE_DIR;
        ArchiveRegistry.Record record = requireRecord(id.archiveId);
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            int index = archive.findEntry(id.path);
            if (index < 0) throw new FileNotFoundException("CMPCT member no longer exists");
            CmpctNative.Entry entry = archive.entry(index);
            return entry.kind == CmpctNative.KIND_DIR
                    ? DocumentsContract.Document.MIME_TYPE_DIR
                    : MimeTypes.forPath(entry.path);
        } catch (IOException e) {
            throw fileNotFound("Unable to inspect CMPCT member", e);
        }
    }

    @Override
    public boolean isChildDocument(String parentDocumentId, String documentId) {
        try {
            Id parent = parseDocumentId(parentDocumentId);
            Id child = parseDocumentId(documentId);
            if (!parent.archiveId.equals(child.archiveId)) return false;
            if (parent.path.isEmpty()) return !child.path.isEmpty();
            return child.path.startsWith(parent.path + "/");
        } catch (FileNotFoundException e) {
            return false;
        }
    }

    @Override
    public ParcelFileDescriptor openDocument(
            String documentId, String mode, CancellationSignal signal) throws FileNotFoundException {
        if (mode == null || !mode.startsWith("r")) {
            throw new FileNotFoundException("CMPCT Android preview is read-only");
        }
        Id id = parseDocumentId(documentId);
        if (id.path.isEmpty()) throw new FileNotFoundException("Cannot open archive root as a file");
        ArchiveRegistry.Record record = requireRecord(id.archiveId);

        final int entryIndex;
        final long size;
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            entryIndex = archive.findEntry(id.path);
            if (entryIndex < 0) throw new FileNotFoundException("CMPCT member no longer exists");
            CmpctNative.Entry entry = archive.entry(entryIndex);
            if (entry.kind != CmpctNative.KIND_FILE) {
                throw new FileNotFoundException("Only regular CMPCT members can be streamed");
            }
            size = entry.size;
        } catch (IOException e) {
            throw fileNotFound("Unable to open CMPCT member", e);
        }

        try {
            ParcelFileDescriptor[] pipe = ParcelFileDescriptor.createPipe();
            STREAMS.execute(() -> streamMember(record, entryIndex, size, pipe[1], signal));
            return pipe[0];
        } catch (IOException e) {
            throw fileNotFound("Unable to create CMPCT member stream", e);
        }
    }

    private static void streamMember(
            ArchiveRegistry.Record record,
            int entryIndex,
            long size,
            ParcelFileDescriptor writeSide,
            CancellationSignal signal) {
        try (ParcelFileDescriptor ignored = writeSide;
             FileOutputStream out = new FileOutputStream(writeSide.getFileDescriptor());
             CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            long offset = 0;
            while (offset < size) {
                if (signal != null && signal.isCanceled()) return;
                int wanted = (int) Math.min(COPY_CHUNK, size - offset);
                byte[] bytes = archive.readRange(entryIndex, offset, wanted);
                if (bytes.length == 0) throw new IOException("CMPCT native stream ended before member size");
                out.write(bytes);
                offset += bytes.length;
            }
            out.flush();
        } catch (IOException ignored) {
            // Footnote: pipe readers observe an early EOF when a codec/integrity error occurs. Android's
            // DocumentsProvider API has no reliable asynchronous exception channel after openDocument
            // returns; native integrity failures therefore terminate the stream instead of emitting bytes.
        }
    }

    private ArchiveRegistry.Record requireRecord(String archiveId) throws FileNotFoundException {
        ArchiveRegistry.Record record = ArchiveRegistry.get(getContext(), archiveId);
        if (record == null) throw new FileNotFoundException("CMPCT archive is not imported");
        return record;
    }

    private static void addArchiveRoot(MatrixCursor cursor, ArchiveRegistry.Record record) {
        MatrixCursor.RowBuilder row = cursor.newRow();
        add(row, DocumentsContract.Document.COLUMN_DOCUMENT_ID, documentId(record.id, ""));
        add(row, DocumentsContract.Document.COLUMN_DISPLAY_NAME, record.displayName);
        add(row, DocumentsContract.Document.COLUMN_MIME_TYPE, DocumentsContract.Document.MIME_TYPE_DIR);
        add(row, DocumentsContract.Document.COLUMN_FLAGS, 0);
        add(row, DocumentsContract.Document.COLUMN_SIZE, null);
        add(row, DocumentsContract.Document.COLUMN_LAST_MODIFIED, record.file.lastModified());
    }

    private static void addEntry(
            MatrixCursor cursor, ArchiveRegistry.Record record, CmpctNative.Entry entry) {
        MatrixCursor.RowBuilder row = cursor.newRow();
        add(row, DocumentsContract.Document.COLUMN_DOCUMENT_ID, documentId(record.id, entry.path));
        add(row, DocumentsContract.Document.COLUMN_DISPLAY_NAME, baseName(entry.path));
        add(row, DocumentsContract.Document.COLUMN_MIME_TYPE,
                entry.kind == CmpctNative.KIND_DIR
                        ? DocumentsContract.Document.MIME_TYPE_DIR
                        : MimeTypes.forPath(entry.path));
        add(row, DocumentsContract.Document.COLUMN_FLAGS, 0);
        add(row, DocumentsContract.Document.COLUMN_SIZE,
                entry.kind == CmpctNative.KIND_DIR ? null : entry.size);
        add(row, DocumentsContract.Document.COLUMN_LAST_MODIFIED, entry.mtimeNs / 1_000_000L);
    }

    private static String parentOf(String path) {
        int slash = path.lastIndexOf('/');
        return slash < 0 ? "" : path.substring(0, slash);
    }

    private static String baseName(String path) {
        int slash = path.lastIndexOf('/');
        return slash < 0 ? path : path.substring(slash + 1);
    }

    private static String[] resolveRootProjection(String[] projection) {
        return projection == null ? DEFAULT_ROOT_PROJECTION : projection;
    }

    private static String[] resolveDocumentProjection(String[] projection) {
        return projection == null ? DEFAULT_DOCUMENT_PROJECTION : projection;
    }

    private static void add(MatrixCursor.RowBuilder row, String column, Object value) {
        // RowBuilder.add(columnName, value) ignores columns absent from a caller-supplied projection,
        // which lets one implementation serve both default and narrow system queries safely.
        try {
            row.add(column, value);
        } catch (IllegalArgumentException ignored) {
            // Column not requested by this projection.
        }
    }

    private static FileNotFoundException fileNotFound(String message, Exception cause) {
        FileNotFoundException out = new FileNotFoundException(message + ": " + cause.getMessage());
        out.initCause(cause);
        return out;
    }
}
