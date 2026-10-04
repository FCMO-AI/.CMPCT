package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.net.Uri;
import android.util.Base64;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Set;

/** Device/JNI acceptance for the production C25CC01 compact-control dispatch. */
@RunWith(AndroidJUnit4.class)
public final class CmpctAndroidCompactControlTest {

    @Test
    public void compactControlUsesSharedPortableReaderAndExactMemberBytes() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject vector = new JSONObject(readSmallAsset(tests, "v030-compact-control-android.json"));
        assertEquals("cmpct-v030-android-compact-control-vector-v2", vector.getString("schema"));
        assertEquals("r24-compact-control-v1", vector.getString("profile"));
        assertEquals(25, vector.getInt("revision"));

        JSONObject facts = vector.getJSONObject("facts");
        assertTrue(facts.getBoolean("strong_verify"));
        assertTrue(facts.getBoolean("physical_payload_records_unchanged"));
        assertTrue(facts.getBoolean("two_authenticated_control_copies"));
        assertTrue(facts.getBoolean("strictly_smaller_than_source_r24"));

        // The archive is deliberately a separate binary asset. Copy + hash it incrementally so the
        // low-memory API-29 instrumentation process never holds base64 text plus decoded bytes plus
        // the native reader state at the same time.
        File source = new File(target.getCacheDir(), "android-r25-compact-control.cmpct");
        String archiveSha;
        long archiveBytes;
        try (InputStream in = tests.getAssets().open(vector.getString("archive_asset"));
             FileOutputStream out = new FileOutputStream(source)) {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[16 * 1024];
            long total = 0;
            int n;
            while ((n = in.read(buffer)) != -1) {
                out.write(buffer, 0, n);
                digest.update(buffer, 0, n);
                total += n;
            }
            out.getFD().sync();
            archiveSha = hex(digest.digest());
            archiveBytes = total;
        }
        assertEquals(vector.getLong("archive_bytes"), archiveBytes);
        assertEquals(vector.getString("archive_sha256"), archiveSha);

        ArchiveRegistry.Record record = ArchiveRegistry.importArchive(target, Uri.fromFile(source));
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            assertEquals(25, archive.revision());
            archive.verify();
            assertEquals(vector.getInt("expected_entry_count"), archive.entryCount());

            Set<String> filePaths = new HashSet<>();
            Set<String> directoryPaths = new HashSet<>();
            for (int i = 0; i < archive.entryCount(); i++) {
                CmpctNative.Entry entry = archive.entry(i);
                if (entry.kind == CmpctNative.KIND_FILE) {
                    filePaths.add(entry.path);
                } else if (entry.kind == CmpctNative.KIND_DIR) {
                    directoryPaths.add(entry.path);
                }
            }
            assertEquals(vector.getInt("expected_regular_entry_count"), filePaths.size());

            JSONArray expectedPaths = vector.getJSONArray("expected_paths");
            for (int i = 0; i < expectedPaths.length(); i++) {
                assertTrue("missing compact-control public file: " + expectedPaths.getString(i),
                        filePaths.contains(expectedPaths.getString(i)));
            }
            JSONArray expectedDirectories = vector.getJSONArray("expected_directory_paths");
            assertEquals(expectedDirectories.length(), directoryPaths.size());
            for (int i = 0; i < expectedDirectories.length(); i++) {
                assertTrue("missing compact-control public directory: " + expectedDirectories.getString(i),
                        directoryPaths.contains(expectedDirectories.getString(i)));
            }

            String representative = vector.getString("representative_path");
            int index = archive.findEntry(representative);
            assertEquals(CmpctNative.KIND_FILE, archive.entry(index).kind);
            assertEquals(vector.getLong("representative_size"), archive.entry(index).size);
            byte[] expectedHead = Base64.decode(vector.getString("representative_head_base64"), Base64.DEFAULT);
            byte[] actualHead = archive.readRange(index, 0, expectedHead.length);
            assertEquals(hex(expectedHead), hex(actualHead));
            assertEquals(vector.getString("representative_sha256"), sha256(readWhole(archive, index)));
        }
    }

    private static byte[] readWhole(CmpctNative.Archive archive, int index) throws Exception {
        long size = archive.entry(index).size;
        if (size > Integer.MAX_VALUE) throw new IllegalArgumentException("test member too large");
        return archive.readRange(index, 0, (int) size);
    }

    private static String readSmallAsset(Context context, String name) throws Exception {
        try (InputStream in = context.getAssets().open(name);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[16 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            return out.toString("UTF-8");
        }
    }

    private static String sha256(byte[] bytes) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        return hex(digest.digest(bytes));
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }
}
