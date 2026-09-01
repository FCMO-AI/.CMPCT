package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.util.Base64;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.json.JSONObject;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/** Proves Android preserves canonical standard UTF-8 paths across the JNI boundary. */
@RunWith(AndroidJUnit4.class)
public final class CmpctAndroidUnicodePathTest {

    @Test
    public void supplementaryUnicodePathRoundTripsThroughPortableJni() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject fixture = new JSONObject(readAsset(tests, "v030-logs-android.json"));
        assertEquals("cmpct-v030-android-logs-vector-v1", fixture.getString("schema"));
        String unicodePath = fixture.getString("unicode_hardlink_path");
        String ownerPath = fixture.getString("regular_path");
        // U+1F680 is encoded as four bytes in standard UTF-8 and as a surrogate pair in JNI Modified UTF-8.
        // The old NewStringUTF(path_bytes) bridge therefore could not preserve this authenticated path exactly.
        assertTrue(unicodePath.contains("\uD83D\uDE80"));

        byte[] archiveBytes = Base64.decode(fixture.getString("archive_base64"), Base64.DEFAULT);
        assertEquals(fixture.getString("archive_sha256"), sha256(archiveBytes));
        File source = new File(target.getCacheDir(), "android-r25-unicode-logs.cmpct");
        try (FileOutputStream out = new FileOutputStream(source)) {
            out.write(archiveBytes);
            out.getFD().sync();
        }

        try (CmpctNative.Archive archive = new CmpctNative.Archive(source.getAbsolutePath())) {
            assertEquals(25, archive.revision());
            archive.verify();
            int unicode = archive.findEntry(unicodePath);
            int owner = archive.findEntry(ownerPath);
            assertTrue("supplementary Unicode path must survive JNI exactly", unicode >= 0);
            assertTrue(owner >= 0);
            assertEquals(unicodePath, archive.entry(unicode).path);
            assertEquals(CmpctNative.KIND_HARDLINK, archive.entry(unicode).kind);
            byte[] unicodeHead = archive.readRange(unicode, 0, 64);
            byte[] ownerHead = archive.readRange(owner, 0, 64);
            assertEquals(hex(ownerHead), hex(unicodeHead));
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

// Footnote: the normal logs-inverse Android vector now carries a supplementary-plane hardlink path, so this
// regression gate exercises the real r25 product generator, shared portable dispatcher, JNI shim, and member read.
// JNI NewStringUTF is reserved for JNI Modified UTF-8 strings; archive-owned standard UTF-8 requires explicit
// byte-to-Java decoding to preserve supplementary code points exactly.
