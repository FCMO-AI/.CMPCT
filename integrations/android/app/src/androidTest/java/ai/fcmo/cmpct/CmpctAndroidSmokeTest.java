package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ProviderInfo;
import android.content.pm.ResolveInfo;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
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
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Device/emulator conformance smoke test for Android routing, DocumentsProvider and the JNI core. */
@RunWith(AndroidJUnit4.class)
public final class CmpctAndroidSmokeTest {

    @Test
    public void directCodecGoldenArchivesThroughAndroidBridge() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        // Footnote: the canonical conformance JSON is packaged into the test APK, not the target APK.
        // Read it from instrumentation context while all imported archives live in the real app context.
        JSONObject root = new JSONObject(readAsset(tests, "v24-direct-codecs.json"));
        assertEquals(24, root.getInt("format_revision"));
        JSONArray vectors = root.getJSONArray("vectors");

        for (int i = 0; i < vectors.length(); i++) {
            JSONObject vector = vectors.getJSONObject(i);
            byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
            File source = new File(target.getCacheDir(), "android-golden-" + i + ".cmpct");
            try (FileOutputStream out = new FileOutputStream(source)) {
                out.write(archiveBytes);
                out.getFD().sync();
            }

            ArchiveRegistry.Record record = ArchiveRegistry.importArchive(target, Uri.fromFile(source));
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

    @Test
    public void androidRoutesCmpctViewIntentsWithoutHijackingOtherBinaryFiles() {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        PackageManager pm = target.getPackageManager();

        Intent canonical = new Intent(Intent.ACTION_VIEW)
                .setDataAndType(Uri.parse("content://example/archive.cmpct"), "application/vnd.fcmo.cmpct")
                .addCategory(Intent.CATEGORY_BROWSABLE);
        assertTrue("canonical CMPCT MIME must resolve to the installed handler", resolvesToCmpct(pm, canonical));

        // Footnote: real Android download/file providers commonly label unknown extensions as generic
        // binary. The bounded .cmpct path fallback is therefore part of the user-visible acceptance
        // contract, not merely manifest decoration.
        Intent genericCmpct = new Intent(Intent.ACTION_VIEW)
                .setDataAndType(Uri.parse("content://example/Download/archive.cmpct"), "application/octet-stream")
                .addCategory(Intent.CATEGORY_BROWSABLE);
        assertTrue("octet-stream .cmpct content URI must resolve to the installed handler",
                resolvesToCmpct(pm, genericCmpct));

        Intent unrelatedBinary = new Intent(Intent.ACTION_VIEW)
                .setDataAndType(Uri.parse("content://example/Download/archive.bin"), "application/octet-stream")
                .addCategory(Intent.CATEGORY_BROWSABLE);
        assertFalse("CMPCT must not advertise itself for unrelated generic binary content",
                resolvesToCmpct(pm, unrelatedBinary));
    }

    @Test
    public void importedArchiveBecomesBrowsableDocumentsProviderTreeAndStreamsMember() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject vector = new JSONObject(readAsset(tests, "v24-direct-codecs.json"))
                .getJSONArray("vectors").getJSONObject(0); // RAW 0..63 oracle.
        byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
        File source = new File(target.getCacheDir(), "android-provider-tree.cmpct");
        try (FileOutputStream out = new FileOutputStream(source)) {
            out.write(archiveBytes);
            out.getFD().sync();
        }
        ArchiveRegistry.Record record = ArchiveRegistry.importArchive(target, Uri.fromFile(source));

        CmpctDocumentsProvider provider = new CmpctDocumentsProvider();
        ProviderInfo info = target.getPackageManager().getProviderInfo(
                new ComponentName(target, CmpctDocumentsProvider.class), 0);
        provider.attachInfo(target, info);

        String rootDocumentId = null;
        try (Cursor roots = provider.queryRoots(null)) {
            int rootIdCol = roots.getColumnIndexOrThrow(DocumentsContract.Root.COLUMN_ROOT_ID);
            int docIdCol = roots.getColumnIndexOrThrow(DocumentsContract.Root.COLUMN_DOCUMENT_ID);
            while (roots.moveToNext()) {
                if (record.id.equals(roots.getString(rootIdCol))) {
                    rootDocumentId = roots.getString(docIdCol);
                    break;
                }
            }
        }
        assertNotNull("imported archive must appear as a DocumentsProvider root", rootDocumentId);

        String childDocumentId;
        // Footnote: API 26 added a Bundle overload with the same first two parameters. Cast null to
        // String so this test deliberately exercises CMPCT's legacy-compatible sortOrder override.
        try (Cursor children = provider.queryChildDocuments(rootDocumentId, null, (String) null)) {
            assertEquals(1, children.getCount());
            assertTrue(children.moveToFirst());
            assertEquals("raw.bin", children.getString(children.getColumnIndexOrThrow(
                    DocumentsContract.Document.COLUMN_DISPLAY_NAME)));
            assertEquals(64L, children.getLong(children.getColumnIndexOrThrow(
                    DocumentsContract.Document.COLUMN_SIZE)));
            childDocumentId = children.getString(children.getColumnIndexOrThrow(
                    DocumentsContract.Document.COLUMN_DOCUMENT_ID));
        }

        byte[] member;
        ParcelFileDescriptor pfd = provider.openDocument(childDocumentId, "r", null);
        // Footnote: AutoCloseInputStream owns pfd. Giving the same descriptor a second try-with-resource
        // owner would make the test exercise a double-close artifact rather than provider correctness.
        try (InputStream in = new ParcelFileDescriptor.AutoCloseInputStream(pfd)) {
            member = readAll(in);
        }
        assertEquals(64, member.length);
        for (int i = 0; i < member.length; i++) assertEquals((byte) i, member[i]);
    }

    @Test
    public void badMagicNeverBecomesImportedRoot() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        File bad = new File(target.getCacheDir(), "not-cmpct.cmpct");
        try (FileOutputStream out = new FileOutputStream(bad)) {
            out.write("PK-not-a-cmpct-archive".getBytes(StandardCharsets.UTF_8));
        }
        try {
            ArchiveRegistry.importArchive(target, Uri.fromFile(bad));
            fail("bad magic must be rejected before native parsing");
        } catch (java.io.IOException expected) {
            assertTrue(expected.getMessage().contains("CMPCT24"));
        }
    }

    private static boolean resolvesToCmpct(PackageManager pm, Intent intent) {
        List<ResolveInfo> matches = pm.queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY);
        for (ResolveInfo match : matches) {
            if (match.activityInfo != null
                    && "ai.fcmo.cmpct".equals(match.activityInfo.packageName)
                    && match.activityInfo.name.endsWith(".MainActivity")) return true;
        }
        return false;
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

    private static byte[] readAll(InputStream in) throws Exception {
        try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[16 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            return out.toByteArray();
        }
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format("%02x", b & 0xff));
        return out.toString();
    }
}
