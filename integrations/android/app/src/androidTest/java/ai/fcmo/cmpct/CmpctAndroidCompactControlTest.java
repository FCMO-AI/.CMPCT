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
        JSONObject vector = new JSONObject(readAsset(tests, "v030-compact-control-android.json"));
        assertEquals("cmpct-v030-android-compact-control-vector-v1", vector.getString("schema"));
        assertEquals("r24-compact-control-v1", vector.getString("profile"));
        assertEquals(25, vector.getInt("revision"));

        JSONObject facts = vector.getJSONObject("facts");
        assertTrue(facts.getBoolean("strong_verify"));
        assertTrue(facts.getBoolean("physical_payload_records_unchanged"));
        assertTrue(facts.getBoolean("two_authenticated_control_copies"));
        assertTrue(facts.getBoolean("strictly_smaller_than_source_r24"));

        byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
        assertEquals(vector.getString("archive_sha256"), sha256(archiveBytes));
        File source = new File(target.getCacheDir(), "android-r25-compact-control.cmpct");
        try (FileOutputStream out = new FileOutputStream(source)) {
            out.write(archiveBytes);
            out.getFD().sync();
        }

        ArchiveRegistry.Record record = ArchiveRegistry.importArchive(target, Uri.fromFile(source));
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            assertEquals(25, archive.revision());
            archive.verify();
            assertEquals(vector.getInt("expected_entry_count"), archive.entryCount());

            Set<String> paths = new HashSet<>();
            for (int i = 0; i < archive.entryCount(); i++) paths.add(archive.entry(i).path);
            JSONArray expectedPaths = vector.getJSONArray("expected_paths");
            for (int i = 0; i < expectedPaths.length(); i++) {
                assertTrue("missing compact-control public entry: " + expectedPaths.getString(i),
                        paths.contains(expectedPaths.getString(i)));
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

    private static String readAsset(Context context, String name) throws Exception {
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
