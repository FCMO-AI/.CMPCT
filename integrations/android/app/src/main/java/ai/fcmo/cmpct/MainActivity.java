package ai.fcmo.cmpct;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Tap/open archive browser backed exclusively by the shared CMPCT native core. */
public final class MainActivity extends Activity {
    private static final int REQUEST_PICK = 24;

    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private TextView title;
    private ListView list;
    private ArchiveRegistry.Record currentArchive;
    private String currentDirectory = "";
    private List<Node> visibleNodes = new ArrayList<>();

    private static final class Node {
        final CmpctNative.Entry entry;
        Node(CmpctNative.Entry entry) { this.entry = entry; }
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        Uri incoming = Intent.ACTION_VIEW.equals(getIntent().getAction()) ? getIntent().getData() : null;
        if (incoming != null) {
            importAndBrowse(incoming);
        } else {
            showLibrary();
        }
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(16), dp(12), dp(12), dp(12));

        title = new TextView(this);
        title.setTextSize(18f);
        title.setSingleLine(true);
        LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        bar.addView(title, titleParams);

        Button open = new Button(this);
        open.setText("Open .cmpct");
        open.setOnClickListener(v -> pickArchive());
        bar.addView(open);
        root.addView(bar);

        list = new ListView(this);
        list.setOnItemClickListener((parent, view, position, id) -> activate(position));
        root.addView(list, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);
    }

    private void pickArchive() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        // Footnote: Storage Access Framework providers are inconsistent about unknown custom MIME
        // types. Pick broadly, then enforce CMPCT24\0 ourselves before any native parsing occurs.
        intent.setType("application/octet-stream");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                "application/vnd.fcmo.cmpct", "application/x-cmpct", "application/octet-stream"
        });
        startActivityForResult(intent, REQUEST_PICK);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_PICK && resultCode == RESULT_OK && data != null && data.getData() != null) {
            importAndBrowse(data.getData());
        }
    }

    private void importAndBrowse(Uri uri) {
        title.setText("Importing CMPCT…");
        list.setAdapter(null);
        io.execute(() -> {
            try {
                ArchiveRegistry.Record record = ArchiveRegistry.importArchive(this, uri);
                // Opening through Rust after magic validation catches corrupt index/schema bytes before
                // the archive is presented as a directory to the user.
                try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
                    if (archive.revision() != 24) throw new IOException("Unsupported CMPCT revision");
                }
                runOnUiThread(() -> browse(record, ""));
            } catch (Exception e) {
                runOnUiThread(() -> {
                    toast(e.getMessage() == null ? e.toString() : e.getMessage());
                    showLibrary();
                });
            }
        });
    }

    private void showLibrary() {
        currentArchive = null;
        currentDirectory = "";
        title.setText("CMPCT archives");
        List<ArchiveRegistry.Record> records = ArchiveRegistry.all(this);
        List<String> labels = new ArrayList<>();
        for (ArchiveRegistry.Record record : records) labels.add(record.displayName);
        if (labels.isEmpty()) labels.add("No imported archives — tap Open .cmpct");
        list.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, labels));
        list.setOnItemClickListener((parent, view, position, id) -> {
            if (records.isEmpty()) pickArchive();
            else browse(records.get(position), "");
        });
    }

    private void browse(ArchiveRegistry.Record record, String directory) {
        currentArchive = record;
        currentDirectory = directory;
        title.setText(record.displayName + (directory.isEmpty() ? "" : " / " + directory));
        list.setAdapter(null);
        list.setOnItemClickListener((parent, view, position, id) -> activate(position));
        io.execute(() -> {
            try {
                List<Node> nodes = children(record, directory);
                runOnUiThread(() -> renderNodes(nodes));
            } catch (Exception e) {
                runOnUiThread(() -> toast(e.getMessage() == null ? e.toString() : e.getMessage()));
            }
        });
    }

    private List<Node> children(ArchiveRegistry.Record record, String directory) throws IOException {
        List<Node> out = new ArrayList<>();
        try (CmpctNative.Archive archive = new CmpctNative.Archive(record.file.getAbsolutePath())) {
            int count = archive.entryCount();
            for (int i = 0; i < count; i++) {
                CmpctNative.Entry entry = archive.entry(i);
                if (parentOf(entry.path).equals(directory)) out.add(new Node(entry));
            }
        }
        out.sort((a, b) -> {
            boolean ad = a.entry.kind == CmpctNative.KIND_DIR;
            boolean bd = b.entry.kind == CmpctNative.KIND_DIR;
            if (ad != bd) return ad ? -1 : 1;
            return baseName(a.entry.path).compareToIgnoreCase(baseName(b.entry.path));
        });
        return out;
    }

    private void renderNodes(List<Node> nodes) {
        visibleNodes = nodes;
        List<String> labels = new ArrayList<>();
        for (Node node : nodes) {
            CmpctNative.Entry e = node.entry;
            if (e.kind == CmpctNative.KIND_DIR) {
                labels.add("DIR   " + baseName(e.path));
            } else if (e.kind == CmpctNative.KIND_FILE) {
                labels.add("FILE  " + baseName(e.path) + "   (" + humanBytes(e.size) + ")");
            } else if (e.kind == CmpctNative.KIND_SYMLINK) {
                labels.add("LINK  " + baseName(e.path));
            } else {
                labels.add("HARD  " + baseName(e.path));
            }
        }
        if (labels.isEmpty()) labels.add("(empty directory)");
        list.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, labels));
    }

    private void activate(int position) {
        if (position < 0 || position >= visibleNodes.size()) return;
        CmpctNative.Entry entry = visibleNodes.get(position).entry;
        if (entry.kind == CmpctNative.KIND_DIR) {
            browse(currentArchive, entry.path);
            return;
        }
        if (entry.kind != CmpctNative.KIND_FILE) {
            toast("This preview browser opens regular files; link materialization is a later native-core gate.");
            return;
        }
        String docId = CmpctDocumentsProvider.documentId(currentArchive.id, entry.path);
        Uri uri = DocumentsContract.buildDocumentUri(
                getPackageName() + ".documents", docId);
        Intent view = new Intent(Intent.ACTION_VIEW)
                .setDataAndType(uri, MimeTypes.forPath(entry.path))
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivity(view);
        } catch (Exception e) {
            Intent share = new Intent(Intent.ACTION_SEND)
                    .setType(MimeTypes.forPath(entry.path))
                    .putExtra(Intent.EXTRA_STREAM, uri)
                    .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(share, "Open CMPCT member with"));
        }
    }

    @Override
    public void onBackPressed() {
        if (currentArchive != null) {
            if (!currentDirectory.isEmpty()) browse(currentArchive, parentOf(currentDirectory));
            else showLibrary();
            return;
        }
        super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }

    private static String parentOf(String path) {
        int slash = path.lastIndexOf('/');
        return slash < 0 ? "" : path.substring(0, slash);
    }

    private static String baseName(String path) {
        int slash = path.lastIndexOf('/');
        return slash < 0 ? path : path.substring(slash + 1);
    }

    private static String humanBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        double kib = bytes / 1024.0;
        if (kib < 1024) return String.format("%.1f KiB", kib);
        return String.format("%.1f MiB", kib / 1024.0);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
