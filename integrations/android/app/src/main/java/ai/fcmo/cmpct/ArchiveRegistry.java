package ai.fcmo.cmpct;

import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/** Durable registry of CMPCT archives imported into app-private storage. */
final class ArchiveRegistry {
    private static final String PREFS = "cmpct_archives";
    private static final byte[] MAGIC_R24 = new byte[] {'C','M','P','C','T','2','4',0};
    private static final byte[] MAGIC_R25_G04 = new byte[] {'C','M','P','2','5','G','4',0};
    private static final byte[] MAGIC_R25_PREFIX = new byte[] {'C','M','P','2','5','P','G',0};
    private static final int MAGIC_LENGTH = 8;

    static final class Record {
        final String id;
        final String displayName;
        final File file;

        Record(String id, String displayName, File file) {
            this.id = id;
            this.displayName = displayName;
            this.file = file;
        }
    }

    private ArchiveRegistry() {}

    static Record importArchive(Context context, Uri uri) throws IOException {
        File directory = archiveDirectory(context);
        File staging = File.createTempFile("cmpct-import-", ".tmp", directory);
        MessageDigest digest;
        try {
            digest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException impossible) {
            throw new IOException("SHA-256 is unavailable", impossible);
        }

        byte[] first = new byte[MAGIC_LENGTH];
        int firstUsed = 0;
        long total = 0;
        try (InputStream raw = context.getContentResolver().openInputStream(uri)) {
            if (raw == null) throw new IOException("Android provider did not expose readable archive bytes");
            try (BufferedInputStream in = new BufferedInputStream(raw);
                 FileOutputStream out = new FileOutputStream(staging)) {
                byte[] buffer = new byte[256 * 1024];
                int n;
                while ((n = in.read(buffer)) != -1) {
                    if (firstUsed < first.length) {
                        int take = Math.min(n, first.length - firstUsed);
                        System.arraycopy(buffer, 0, first, firstUsed, take);
                        firstUsed += take;
                    }
                    digest.update(buffer, 0, n);
                    out.write(buffer, 0, n);
                    total += n;
                }
                out.getFD().sync();
            }
        } catch (IOException e) {
            staging.delete();
            throw e;
        }

        int expectedRevision = total < MAGIC_LENGTH ? 0 : releaseRevision(first);
        if (expectedRevision == 0) {
            staging.delete();
            throw new IOException("Not a canonical CMPCT release archive");
        }

        String id = hex(digest.digest());
        File destination = new File(directory, id + ".cmpct");
        boolean created = false;
        if (!destination.exists()) {
            if (!staging.renameTo(destination)) {
                staging.delete();
                throw new IOException("Unable to commit imported CMPCT archive into app storage");
            }
            created = true;
        } else {
            staging.delete();
        }

        try (CmpctNative.Archive archive = new CmpctNative.Archive(destination.getAbsolutePath())) {
            int revision = archive.revision();
            if (revision != expectedRevision) {
                throw new IOException(
                        "CMPCT release identity mismatch: magic expects revision "
                                + expectedRevision + ", native reader reported " + revision);
            }
            archive.verify();
        } catch (IOException e) {
            // Footnote: never publish a DocumentsProvider root after magic/index-only validation. The shared
            // native verifier must authenticate every complete regular member first; otherwise corrupted RAW
            // payload bytes could survive import and fail later only when a user opens a document.
            if (created) destination.delete();
            throw e;
        }

        String name = displayName(context, uri);
        if (name == null || name.trim().isEmpty()) name = id.substring(0, 12) + ".cmpct";
        prefs(context).edit().putString(id, name).apply();
        context.getContentResolver().notifyChange(
                DocumentsContract.buildRootsUri(context.getPackageName() + ".documents"), null);
        return new Record(id, name, destination);
    }

    static List<Record> all(Context context) {
        Map<String, ?> values = prefs(context).getAll();
        List<Record> out = new ArrayList<>();
        for (Map.Entry<String, ?> e : values.entrySet()) {
            if (!(e.getValue() instanceof String)) continue;
            File file = new File(archiveDirectory(context), e.getKey() + ".cmpct");
            if (file.isFile()) out.add(new Record(e.getKey(), (String) e.getValue(), file));
        }
        Collections.sort(out, (a, b) -> a.displayName.compareToIgnoreCase(b.displayName));
        return out;
    }

    static Record get(Context context, String id) {
        String name = prefs(context).getString(id, null);
        if (name == null) return null;
        File file = new File(archiveDirectory(context), id + ".cmpct");
        return file.isFile() ? new Record(id, name, file) : null;
    }

    private static File archiveDirectory(Context context) {
        File directory = new File(context.getFilesDir(), "cmpct-archives");
        if (!directory.exists() && !directory.mkdirs() && !directory.isDirectory()) {
            throw new IllegalStateException("Unable to create CMPCT archive directory");
        }
        return directory;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static int releaseRevision(byte[] actual) {
        if (matchesMagic(actual, MAGIC_R24)) return 24;
        if (matchesMagic(actual, MAGIC_R25_G04) || matchesMagic(actual, MAGIC_R25_PREFIX)) return 25;
        return 0;
    }

    private static boolean matchesMagic(byte[] actual, byte[] expected) {
        if (actual.length != expected.length) return false;
        int diff = 0;
        for (int i = 0; i < expected.length; i++) diff |= actual[i] ^ expected[i];
        return diff == 0;
    }

    private static String displayName(Context context, Uri uri) {
        try (Cursor c = context.getContentResolver().query(
                uri, new String[] {OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int column = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (column >= 0) return c.getString(column);
            }
        } catch (RuntimeException ignored) {
            // Footnote: display-name metadata is cosmetic; refusing a valid archive because a provider
            // cannot answer OpenableColumns would make Android interoperability worse for no safety gain.
        }
        String last = uri.getLastPathSegment();
        return last == null ? null : new File(last).getName();
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }
}
