package ai.fcmo.cmpct;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.content.Context;
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
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Cross-representation device gate for the shared native reader packaged inside Android. */
@RunWith(AndroidJUnit4.class)
public final class RepresentationMatrixInstrumentedTest {
    private static final String[] MATRIX_ASSETS = {
            "v24-chunk-maps.json",
            "v24-sparse.json",
            "v24-zstd-dictionary.json",
            "v24-wavflac.json",
            "v24-virtual-zip.json",
            "v24-virtual-zip-deflate-mode0.json",
            "v24-virtual-zip-deflate-mode1.json",
            "v24-virtual-zip-deflate-mode2.json"
    };

    @Test
    public void fixedRepresentationMatrixReadsThroughPackagedRustCore() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        int exercised = 0;

        for (String asset : MATRIX_ASSETS) {
            JSONObject root = new JSONObject(readAsset(tests, asset));
            if (root.has("vectors")) {
                JSONArray vectors = root.getJSONArray("vectors");
                for (int i = 0; i < vectors.length(); i++) {
                    exerciseVector(target, asset + "-" + i, vectors.getJSONObject(i));
                    exercised++;
                }
            } else {
                exerciseVector(target, asset, root.getJSONObject("vector"));
                exercised++;
            }
        }
        assertTrue("representation matrix should exercise more than the direct-codec smoke set",
                exercised >= 9);
    }

    @Test
    public void independentPackOracleSupportsWholeAndSeekedMemberReads() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject vector = new JSONObject(readAsset(tests, "v24-pack.json")).getJSONObject("vector");
        File archiveFile = writeArchive(target, "android-pack.cmpct",
                Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT));

        try (CmpctNative.Archive archive = new CmpctNative.Archive(archiveFile.getAbsolutePath())) {
            JSONArray files = vector.getJSONArray("files");
            assertEquals(files.length(), archive.entryCount());
            for (int i = 0; i < files.length(); i++) {
                JSONObject member = files.getJSONObject(i);
                int index = archive.findEntry(member.getString("name"));
                assertTrue(index >= 0);
                byte[] whole = archive.readRange(index, 0, member.getInt("length"));
                assertEquals(member.getString("hex"), hex(whole));

                JSONObject range = member.getJSONArray("ranges").getJSONObject(0);
                assertEquals(range.getString("hex"), hex(archive.readRange(
                        index,
                        range.getLong("offset"),
                        range.getInt("length"))));
            }
        }
    }

    @Test
    public void corruptPrimaryAndTornTailRecoverSameCommittedTreeOnAndroid() throws Exception {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests = InstrumentationRegistry.getInstrumentation().getContext();
        JSONObject vector = new JSONObject(readAsset(tests, "v24-recovery.json")).getJSONObject("vector");
        String[] fields = {
                "valid_archive_base64",
                "primary_corrupt_base64",
                "torn_tail_base64",
                "invalid_newest_footer_base64"
        };
        List<String> expected = new ArrayList<>();
        JSONArray expectedJson = vector.getJSONArray("expected_files");
        for (int i = 0; i < expectedJson.length(); i++) expected.add(expectedJson.getString(i));
        Collections.sort(expected);

        for (String field : fields) {
            File archiveFile = writeArchive(target, "android-recovery-" + field + ".cmpct",
                    Base64.decode(vector.getString(field), Base64.DEFAULT));
            try (CmpctNative.Archive archive = new CmpctNative.Archive(archiveFile.getAbsolutePath())) {
                List<String> actual = new ArrayList<>();
                for (int i = 0; i < archive.entryCount(); i++) actual.add(archive.entry(i).path);
                Collections.sort(actual);
                assertEquals(field, expected, actual);
            }
        }
    }

    private static void exerciseVector(Context target, String label, JSONObject vector) throws Exception {
        byte[] archiveBytes = Base64.decode(vector.getString("archive_base64"), Base64.DEFAULT);
        File archiveFile = writeArchive(target, "matrix-" + sanitize(label) + ".cmpct", archiveBytes);
        try (CmpctNative.Archive archive = new CmpctNative.Archive(archiveFile.getAbsolutePath())) {
            assertEquals(24, archive.revision());
            assertEquals(1, archive.entryCount());
            CmpctNative.Entry entry = archive.entry(0);
            assertEquals(vector.getString("name"), entry.path);
            assertEquals(vector.getLong("logical_size"), entry.size);

            JSONObject range = null;
            if (vector.has("range")) range = vector.getJSONObject("range");
            else if (vector.has("ranges") && vector.getJSONArray("ranges").length() > 0)
                range = vector.getJSONArray("ranges").getJSONObject(0);

            if (range != null) {
                byte[] got = archive.readRange(
                        0,
                        range.getLong("offset"),
                        range.getInt("length"));
                assertEquals(label, range.getString("hex"), hex(got));
            } else {
                // Footnote: a future fixed vector may intentionally omit a range oracle. It still has
                // to cross Android -> JNI -> Rust and return the exact declared logical byte count for
                // a bounded prefix rather than merely compile into the APK.
                int length = (int) Math.min(entry.size, 64);
                assertEquals(length, archive.readRange(0, 0, length).length);
            }
        }
    }

    private static File writeArchive(Context context, String name, byte[] bytes) throws Exception {
        File file = new File(context.getCacheDir(), name);
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(bytes);
            out.getFD().sync();
        }
        return file;
    }

    private static String sanitize(String value) {
        return value.replaceAll("[^A-Za-z0-9_.-]", "_");
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
