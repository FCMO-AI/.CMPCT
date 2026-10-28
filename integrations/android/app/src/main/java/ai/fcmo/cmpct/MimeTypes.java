package ai.fcmo.cmpct;

import java.util.Locale;

/** Small no-dependency MIME mapper for handing individual archive members to Android apps. */
final class MimeTypes {
    private MimeTypes() {}

    static String forPath(String path) {
        String p = path.toLowerCase(Locale.ROOT);
        if (p.endsWith(".txt") || p.endsWith(".md") || p.endsWith(".log") || p.endsWith(".csv")) return "text/plain";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".html") || p.endsWith(".htm")) return "text/html";
        if (p.endsWith(".pdf")) return "application/pdf";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".gif")) return "image/gif";
        if (p.endsWith(".webp")) return "image/webp";
        if (p.endsWith(".mp3")) return "audio/mpeg";
        if (p.endsWith(".wav")) return "audio/wav";
        if (p.endsWith(".mp4")) return "video/mp4";
        if (p.endsWith(".zip")) return "application/zip";
        // Footnote: unknown members remain generic bytes. Guessing an executable/media MIME from an
        // extension CMPCT does not understand would create worse Android behavior than an explicit
        // app chooser for application/octet-stream.
        return "application/octet-stream";
    }
}
