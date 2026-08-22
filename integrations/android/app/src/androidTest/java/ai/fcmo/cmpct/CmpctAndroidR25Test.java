package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

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
import java.io.IOException;
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
                // The builder-independent golden payload is 26-byte "canonical-r25-portability\n" repetitions;
                // a 32-byte range therefore ends in "canoni". Keep the assertion at the requested byte count so
                // Android proves exact selected-read boundaries rather than masking an off-by-one with a shorter read.
                assertEquals("canonical-r25-portability\ncanoni", new String(head, StandardCharsets.UTF_8));
                byte[] targetBytes = archive.readRange(symlink, 0, 13);
                assertEquals("dir/hello.bin", new String(targetBytes, StandardCharsets.UTF_8));
            }
        }
    }

    @Test
    public void logsInverseProfileUsesProductionPortableDispatchOnAndroid() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject vector = new JSONObject(readAsset(tests, "v030-logs-android.json"));
        assertEquals("cmpct-v030-android-logs-vector-v1", vector.getString("schema"));
        assertEquals(25, vector.getInt("revision"));

        byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
        assertEquals(vector.getString("archive_sha256"), sha256(archiveBytes));
        File source = new File(target.getCacheDir(), "android-r25-logs-inverse.cmpct");
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
                assertTrue("missing logs public entry: " + expectedPaths.getString(i), paths.contains(expectedPaths.getString(i)));
            }
            for (String path : paths) {
                assertFalse("logs internal filesystem manifest must not leak into Android user view", path.startsWith(".__cmpct_r25_internal__/"));
            }

            int regular = archive.findEntry(vector.getString("regular_path"));
            int hardlink = archive.findEntry(vector.getString("hardlink_path"));
            int symlink = archive.findEntry(vector.getString("symlink_path"));
            assertEquals(CmpctNative.KIND_FILE, archive.entry(regular).kind);
            assertEquals(CmpctNative.KIND_HARDLINK, archive.entry(hardlink).kind);
            assertEquals(CmpctNative.KIND_SYMLINK, archive.entry(symlink).kind);

            byte[] expectedHead = Base64.decode(vector.getString("regular_head_base64"), Base64.DEFAULT);
            byte[] regularHead = archive.readRange(regular, 0, expectedHead.length);
            byte[] hardlinkHead = archive.readRange(hardlink, 0, expectedHead.length);
            assertEquals(hex(expectedHead), hex(regularHead));
            assertEquals(hex(regularHead), hex(hardlinkHead));

            byte[] symlinkTarget = archive.readRange(symlink, 0, vector.getString("symlink_target").getBytes(StandardCharsets.UTF_8).length);
            assertEquals(vector.getString("symlink_target"), new String(symlinkTarget, StandardCharsets.UTF_8));
        }
    }

    @Test
    public void importRejectsNonCanonicalBytesBeforeRegistryPublication() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        File source = new File(target.getCacheDir(), "android-not-cmpct.bin");
        byte[] garbage = "definitely-not-a-canonical-cmpct-archive".getBytes(StandardCharsets.UTF_8);
        try (FileOutputStream out = new FileOutputStream(source)) {
            out.write(garbage);
            out.getFD().sync();
        }

        String id = sha256(garbage);
        File published = new File(new File(target.getFilesDir(), "cmpct-archives"), id + ".cmpct");
        if (published.exists()) assertTrue(published.delete());

        try {
            ArchiveRegistry.importArchive(target, Uri.fromFile(source));
            fail("non-canonical bytes must be rejected by the production portable reader");
        } catch (IOException expected) {
            assertFalse("failed import must never publish into the archive registry", published.exists());
            assertFalse("failed import must not create a durable registry record", ArchiveRegistry.get(target, id) != null);
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

// Footnote: canonical r25 goldens and the dynamically generated logs-inverse vector are both consumed through
// libcmpct_portable. Android therefore proves the packaged JNI/C-ABI path sees the same public filesystem namespace,
// link semantics, exact member bytes and strong-verification behavior as desktop native code rather than carrying
// an Android-only archive parser. Invalid inputs are likewise rejected by that same native authority before the
// registry commits a content-addressed archive into app-private storage.
