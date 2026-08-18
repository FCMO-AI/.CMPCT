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

/** Device acceptance for the exact builder-independent canonical revision-25 archives. */
@RunWith(AndroidJUnit4.class)
public final class CmpctAndroidR25Test {

    @Test
    public void canonicalR25GoldensUseSharedPortableReaderAndHideInternalManifest() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject fixture = new JSONObject(readAsset(tests, "v030-r25-canonical.json"));
        JSONObject expected = fixture.getJSONObject("filesystem").getJSONObject("entries");
        String internal = fixture.getJSONObject("filesystem").getString("internal_path");

        for (String profile : new String[] {"g04", "prefixgraph"}) {
            JSONObject vector = fixture.getJSONObject(profile);
            byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
            assertEquals(vector.getString("archive_sha256"), sha256(archiveBytes));
            File source = new File(target.getCacheDir(), "android-r25-" + profile + ".cmpct");
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
                assertFalse("internal filesystem manifest must not leak into Android user view", paths.contains(internal));
                assertTrue(paths.contains("dir/hello.bin"));
                assertTrue(paths.contains("dir/hello-hard.bin"));
                assertTrue(paths.contains("link.bin"));

                int regular = archive.findEntry("dir/hello.bin");
                int hardlink = archive.findEntry("dir/hello-hard.bin");
                int symlink = archive.findEntry("link.bin");
                CmpctNative.Entry regularInfo = archive.entry(regular);
                assertEquals(CmpctNative.KIND_FILE, regularInfo.kind);
                assertEquals(318L, regularInfo.size);
                byte[] head = archive.readRange(regular, 0, 32);
                byte[] hardHead = archive.readRange(hardlink, 0, 32);
                assertEquals(hex(head), hex(hardHead));
                assertEquals("canonical-r25-portability\ncanon", new String(head, StandardCharsets.UTF_8));
                byte[] targetBytes = archive.readRange(symlink, 0, 13);
                assertEquals("dir/hello.bin", new String(targetBytes, StandardCharsets.UTF_8));
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

// Footnote: these exact bytes are independently generated from the canonical r25 grammar and are shared with
// native desktop acceptance. The emulator therefore proves Android packaging/JNI sees the same revision, hidden
// internal namespace, link semantics and selected-member bytes rather than a second Android-only parser fixture.
