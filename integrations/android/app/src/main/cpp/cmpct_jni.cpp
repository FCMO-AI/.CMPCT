#include <jni.h>
#include <stdint.h>

#include <string>
#include <vector>

#include "cmpct_portable.h"

namespace {

PortableArchive *from_handle(jlong handle) {
    return reinterpret_cast<PortableArchive *>(static_cast<intptr_t>(handle));
}

jlong to_handle(PortableArchive *archive) {
    return static_cast<jlong>(reinterpret_cast<intptr_t>(archive));
}

const char *status_name(int32_t status) {
    switch (status) {
        case CMPCT_PORTABLE_OK: return "ok";
        case CMPCT_PORTABLE_NULL: return "null argument";
        case CMPCT_PORTABLE_IO: return "I/O or truncated archive";
        case CMPCT_PORTABLE_FORMAT: return "invalid/corrupt CMPCT archive";
        case CMPCT_PORTABLE_LIMIT: return "CMPCT resource limit exceeded";
        case CMPCT_PORTABLE_UTF8: return "invalid UTF-8 path";
        case CMPCT_PORTABLE_RANGE: return "range outside CMPCT member";
        case CMPCT_PORTABLE_UNSUPPORTED: return "CMPCT operation is not portable on this representation/platform";
        case CMPCT_PORTABLE_INTEGRITY: return "CMPCT authenticated integrity check failed";
        case CMPCT_PORTABLE_PANIC: return "native CMPCT panic boundary triggered";
        default: return "unknown CMPCT portable native error";
    }
}

void throw_io(JNIEnv *env, int32_t status) {
    jclass cls = env->FindClass("java/io/IOException");
    if (cls != nullptr) {
        env->ThrowNew(cls, status_name(status));
    }
}

bool java_string_to_standard_utf8(JNIEnv *env, jstring value, std::string *out) {
    if (value == nullptr || out == nullptr) {
        throw_io(env, CMPCT_PORTABLE_NULL);
        return false;
    }
    const jsize len = env->GetStringLength(value);
    const jchar *chars = env->GetStringChars(value, nullptr);
    if (chars == nullptr) return false;

    out->clear();
    out->reserve(static_cast<size_t>(len) * 3);
    bool ok = true;
    for (jsize i = 0; i < len && ok; ++i) {
        uint32_t cp = chars[i];
        if (cp == 0) {
            ok = false;  // Native path APIs are NUL-terminated; never permit Java embedded-NUL truncation.
            break;
        }
        if (cp >= 0xD800 && cp <= 0xDBFF) {
            if (i + 1 >= len) {
                ok = false;
                break;
            }
            const uint32_t low = chars[++i];
            if (low < 0xDC00 || low > 0xDFFF) {
                ok = false;
                break;
            }
            cp = 0x10000 + ((cp - 0xD800) << 10) + (low - 0xDC00);
        } else if (cp >= 0xDC00 && cp <= 0xDFFF) {
            ok = false;
            break;
        }

        if (cp <= 0x7F) {
            out->push_back(static_cast<char>(cp));
        } else if (cp <= 0x7FF) {
            out->push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out->push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else if (cp <= 0xFFFF) {
            out->push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out->push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out->push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else {
            out->push_back(static_cast<char>(0xF0 | (cp >> 18)));
            out->push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
            out->push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out->push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        }
    }
    env->ReleaseStringChars(value, chars);
    if (!ok) {
        out->clear();
        throw_io(env, CMPCT_PORTABLE_UTF8);
    }
    return ok;
}

jstring new_standard_utf8_string(JNIEnv *env, const uint8_t *bytes, size_t len) {
    // JNI NewStringUTF consumes Modified UTF-8, not ordinary UTF-8. CMPCT paths are authenticated
    // standard UTF-8 and may contain supplementary code points encoded as four bytes, so routing
    // archive bytes through NewStringUTF can corrupt an otherwise valid cross-platform pathname.
    if (len > static_cast<size_t>(INT32_MAX)) {
        throw_io(env, CMPCT_PORTABLE_LIMIT);
        return nullptr;
    }

    jbyteArray raw = env->NewByteArray(static_cast<jsize>(len));
    if (raw == nullptr) return nullptr;
    if (len > 0) {
        env->SetByteArrayRegion(
            raw,
            0,
            static_cast<jsize>(len),
            reinterpret_cast<const jbyte *>(bytes));
        if (env->ExceptionCheck()) {
            env->DeleteLocalRef(raw);
            return nullptr;
        }
    }

    jclass string_class = env->FindClass("java/lang/String");
    if (string_class == nullptr) {
        env->DeleteLocalRef(raw);
        return nullptr;
    }
    jmethodID constructor = env->GetMethodID(string_class, "<init>", "([BLjava/lang/String;)V");
    if (constructor == nullptr) {
        env->DeleteLocalRef(string_class);
        env->DeleteLocalRef(raw);
        return nullptr;
    }
    // This literal is ASCII, so NewStringUTF is correct here; it is never populated with archive bytes.
    jstring charset_name = env->NewStringUTF("UTF-8");
    if (charset_name == nullptr) {
        env->DeleteLocalRef(string_class);
        env->DeleteLocalRef(raw);
        return nullptr;
    }
    jobject value = env->NewObject(string_class, constructor, raw, charset_name);
    env->DeleteLocalRef(charset_name);
    env->DeleteLocalRef(string_class);
    env->DeleteLocalRef(raw);
    return static_cast<jstring>(value);
}

bool require_archive(JNIEnv *env, jlong handle, PortableArchive **out) {
    *out = from_handle(handle);
    if (*out != nullptr) return true;
    throw_io(env, CMPCT_PORTABLE_NULL);
    return false;
}

}  // namespace

extern "C" JNIEXPORT jlong JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeOpen(JNIEnv *env, jclass, jstring path) {
    if (path == nullptr) {
        throw_io(env, CMPCT_PORTABLE_NULL);
        return 0;
    }
    std::string utf8_path;
    if (!java_string_to_standard_utf8(env, path, &utf8_path)) return 0;
    PortableArchive *archive = nullptr;
    const int32_t status = cmpct_portable_open(utf8_path.c_str(), &archive);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return 0;
    }
    return to_handle(archive);
}

extern "C" JNIEXPORT void JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeClose(JNIEnv *, jclass, jlong handle) {
    PortableArchive *archive = from_handle(handle);
    if (archive != nullptr) cmpct_portable_close(archive);
}

extern "C" JNIEXPORT jint JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeRevision(JNIEnv *env, jclass, jlong handle) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return 0;
    uint32_t revision = 0;
    const int32_t status = cmpct_portable_revision(archive, &revision);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return 0;
    }
    return static_cast<jint>(revision);
}

extern "C" JNIEXPORT void JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeVerify(JNIEnv *env, jclass, jlong handle) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return;
    const int32_t status = cmpct_portable_verify(archive);
    if (status != CMPCT_PORTABLE_OK) throw_io(env, status);
}

extern "C" JNIEXPORT jint JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryCount(JNIEnv *env, jclass, jlong handle) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return 0;
    size_t count = 0;
    const int32_t status = cmpct_portable_entry_count(archive, &count);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return 0;
    }
    if (count > static_cast<size_t>(INT32_MAX)) {
        throw_io(env, CMPCT_PORTABLE_LIMIT);
        return 0;
    }
    return static_cast<jint>(count);
}

extern "C" JNIEXPORT jstring JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryPath(JNIEnv *env, jclass, jlong handle, jint index) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0) {
        throw_io(env, CMPCT_PORTABLE_RANGE);
        return nullptr;
    }
    size_t len = 0;
    int32_t status = cmpct_portable_entry_path(archive, static_cast<size_t>(index), nullptr, 0, &len);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    std::vector<uint8_t> path(len);
    status = cmpct_portable_entry_path(
        archive,
        static_cast<size_t>(index),
        path.empty() ? nullptr : path.data(),
        path.size(),
        &len);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    return new_standard_utf8_string(env, path.data(), len);
}

extern "C" JNIEXPORT jlongArray JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryInfo(JNIEnv *env, jclass, jlong handle, jint index) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0) {
        throw_io(env, CMPCT_PORTABLE_RANGE);
        return nullptr;
    }
    CmpctPortableEntryInfo info{};
    const int32_t status = cmpct_portable_entry_info(archive, static_cast<size_t>(index), &info);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    const jlong values[4] = {
        static_cast<jlong>(info.kind),
        static_cast<jlong>(info.mode),
        static_cast<jlong>(info.size),
        static_cast<jlong>(info.mtime_ns),
    };
    jlongArray out = env->NewLongArray(4);
    if (out != nullptr) env->SetLongArrayRegion(out, 0, 4, values);
    return out;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeReadRange(
    JNIEnv *env, jclass, jlong handle, jint index, jlong offset, jint length) {
    PortableArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0 || offset < 0 || length < 0) {
        throw_io(env, CMPCT_PORTABLE_RANGE);
        return nullptr;
    }
    std::vector<uint8_t> buffer(static_cast<size_t>(length));
    size_t read = 0;
    const int32_t status = cmpct_portable_entry_read_range(
        archive,
        static_cast<size_t>(index),
        static_cast<uint64_t>(offset),
        buffer.empty() ? nullptr : buffer.data(),
        buffer.size(),
        &read);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    if (read > static_cast<size_t>(INT32_MAX)) {
        throw_io(env, CMPCT_PORTABLE_LIMIT);
        return nullptr;
    }
    jbyteArray out = env->NewByteArray(static_cast<jsize>(read));
    if (out != nullptr && read > 0) {
        env->SetByteArrayRegion(
            out,
            0,
            static_cast<jsize>(read),
            reinterpret_cast<const jbyte *>(buffer.data()));
    }
    return out;
}

// Footnote: JNI owns no archive grammar. Every operation, including complete verification, crosses the same
// libcmpct_portable ABI used by desktop/native tests so Android cannot accidentally become a weaker parser.
// Public entry paths are decoded as standard UTF-8 rather than JNI Modified UTF-8, preserving supplementary
// Unicode code points exactly across the native/Java boundary.
