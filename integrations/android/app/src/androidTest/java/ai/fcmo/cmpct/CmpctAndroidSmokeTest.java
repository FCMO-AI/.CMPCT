package ai.fcmo.cmpct;

import android.content.Context;
import android.net.Uri;
import android.test.InstrumentationTestCase;
import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Device/emulator conformance smoke test for the JNI + shared native reader boundary. */
@SuppressWarnings("deprecation")
public final class CmpctAndroidSmokeTest extends InstrumentationTestCase {

    public void testDirectCodecGoldenArchivesThroughAndroidBridge() throws Exception {
        Context context = getInstrumentation().getTargetContext();
        JSONObject root = new JSONObject(readAsset(context, "v24-direct-codecs.json"));
        assertEquals(24, root.getInt("format_revision"));
        JSONArray vectors = root.getJSONArray("vectors");

        for (int i = 0; i < vectors.length(); i++) {
            JSONObject vector = vectors.getJSONObject(i);
            byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
            File source = new File(context.getCacheDir(), "android-golden-" + i + ".cmpct");
            try (FileOutputStream out = new FileOutputStream(source)) {
                out.write(archiveBytes);
                out.getFD().sync();
            }

            ArchiveRegistry.Record record = ArchiveRegistry.importArchive(context, Uri.fromFile(source));
            try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
                assertEquals(24, archive.revision());
                assertEquals(1, archive.entryCount());
                CmpctNative.Entry entry = archive.entry(0);
                assertEquals(vector.getString("name"), entry.path);
                assertEquals(vector.getLong("logical_size"), entry.size);

                JSONObject range = vector.getJSONObject("range");
                byte[] got = archive.readRange(
                        0,
                        range.getLong("offset"),
                        range.getInt("length"));
                assertEquals(range.getString("hex"), hex(got));
            }
        }
    }

    public void testBadMagicNeverBecomesImportedRoot() throws Exception {
        Context context = getInstrumentation().getTargetContext();
        File bad = new File(context.getCacheDir(), "not-cmpct.cmpct");
        try (FileOutputStream out = new FileOutputStream(bad)) {
            out.write("PK-not-a-cmpct-archive".getBytes(StandardCharsets.UTF_8));
        }
        try {
            ArchiveRegistry.importArchive(context, Uri.fromFile(bad));
            fail("bad magic must be rejected before native parsing");
        } catch (java.io.IOException expected) {
            assertTrue(expected.getMessage().contains("CMPCT24"));
        }
    }

    private static String readAsset(Context context, String name) throws Exception {
        try (InputStream in = context.getAssets().open(name);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[16 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }
}
