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

        try (InputStream raw = context.getContentResolver().openInputStream(uri)) {
            if (raw == null) throw new IOException("Android provider did not expose readable archive bytes");
            try (BufferedInputStream in = new BufferedInputStream(raw);
                 FileOutputStream out = new FileOutputStream(staging)) {
                byte[] buffer = new byte[256 * 1024];
                int n;
                while ((n = in.read(buffer)) != -1) {
                    digest.update(buffer, 0, n);
                    out.write(buffer, 0, n);
                }
                out.getFD().sync();
            }
        } catch (IOException e) {
            staging.delete();
            throw e;
        }

        // The shared portable reader is the single authority for canonical release identities. Keeping a Java
        // magic whitelist here previously rejected a newly promoted canonical r25 profile (C25LG12) before JNI
        // could dispatch it, and would require Android to duplicate every future canonical grammar addition.
        // Authenticate the staged bytes *before* publication instead: only revision-24/25 archives that the
        // production portable reader can completely verify are eligible to enter app-private storage.
        try (CmpctNative.Archive archive = new CmpctNative.Archive(staging.getAbsolutePath())) {
            int revision = archive.revision();
            if (revision != 24 && revision != 25) {
                throw new IOException(
                        "Not a canonical CMPCT release archive (native reader reported revision " + revision + ")");
            }
            archive.verify();
        } catch (IOException e) {
            staging.delete();
            throw e;
        }

        String id = hex(digest.digest());
        File destination = new File(directory, id + ".cmpct");
        if (!destination.exists()) {
            if (!staging.renameTo(destination)) {
                staging.delete();
                throw new IOException("Unable to commit imported CMPCT archive into app storage");
            }
        } else {
            staging.delete();
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

// Footnote: archive identity parsing intentionally lives only in cmpct-portable. Android copies provider bytes to
// a private staging file, asks the production native reader to identify + strongly verify them, and atomically
// publishes only after that succeeds. This keeps future canonical profiles from requiring a second Java parser.
