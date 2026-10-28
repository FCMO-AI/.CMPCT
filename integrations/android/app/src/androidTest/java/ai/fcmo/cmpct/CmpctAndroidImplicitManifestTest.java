package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.net.Uri;
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
import java.util.HashSet;
import java.util.Set;

/** Device acceptance for builder-independent canonical r25 implicit-v4 filesystem control. */
@RunWith(AndroidJUnit4.class)
public final class CmpctAndroidImplicitManifestTest {

    @Test
    public void implicitV4GoldensUseTheSharedPortableReaderOnDevice() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject fixture = new JSONObject(readAsset(tests, "v030-r25-implicit-v4.json"));
        assertEquals("cmpct-v030-native-implicit-v4-golden-v1", fixture.getString("schema"));
        JSONObject expected = fixture.getJSONObject("filesystem").getJSONObject("entries");
        String internal = fixture.getJSONObject("filesystem").getString("internal_path");

        for (String profile : new String[] {"g04", "prefixgraph"}) {
            JSONObject vector = fixture.getJSONObject(profile);
            byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
            assertEquals(vector.getString("archive_sha256"), sha256(archiveBytes));
            File source = new File(target.getCacheDir(), "android-r25-implicit-" + profile + ".cmpct");
            try (FileOutputStream out = new FileOutputStream(source)) {
                out.write(archiveBytes);
                out.getFD().sync();
            }

            ArchiveRegistry.Record record = ArchiveRegistry.importArchive(target, Uri.fromFile(source));
            try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
                assertEquals(25, archive.revision());
                archive.verify();
                assertEquals(expected.length(), archive.entryCount());

                Set<String> paths = new HashSet<>();
                for (int i = 0; i < archive.entryCount(); i++) paths.add(archive.entry(i).path);
                assertFalse("implicit filesystem control must remain internal", paths.contains(internal));
                assertTrue(paths.contains("dir"));
                assertTrue(paths.contains("dir/hello.bin"));
                assertTrue(paths.contains("dir/hello-hard.bin"));
                assertTrue(paths.contains("link.bin"));

                int regular = archive.findEntry("dir/hello.bin");
                int hardlink = archive.findEntry("dir/hello-hard.bin");
                int symlink = archive.findEntry("link.bin");
                assertEquals(CmpctNative.KIND_FILE, archive.entry(regular).kind);
                assertEquals(CmpctNative.KIND_HARDLINK, archive.entry(hardlink).kind);
                assertEquals(CmpctNative.KIND_SYMLINK, archive.entry(symlink).kind);
                assertEquals(318L, archive.entry(regular).size);
                assertEquals(318L, archive.entry(hardlink).size);

                byte[] head = archive.readRange(regular, 0, 32);
                byte[] hardHead = archive.readRange(hardlink, 0, 32);
                assertEquals(hex(head), hex(hardHead));
                assertEquals("canonical-r25-portability\ncanoni", new String(head, StandardCharsets.UTF_8));
                assertEquals(
                        "dir/hello.bin",
                        new String(archive.readRange(symlink, 0, 13), StandardCharsets.UTF_8));
            }
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

// Footnote: this test intentionally consumes the same builder-independent implicit-v4 bytes as desktop native
// authority through ArchiveRegistry -> JNI -> libcmpct_portable. It adds no Android-specific parser or admission
// policy; a platform green therefore means the shared canonical reader understands the compact filesystem control.
