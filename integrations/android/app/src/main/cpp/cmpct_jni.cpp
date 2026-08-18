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
    const char *utf = env->GetStringUTFChars(path, nullptr);
    if (utf == nullptr) return 0;  // JVM already raised OOM.
    PortableArchive *archive = nullptr;
    const int32_t status = cmpct_portable_open(utf, &archive);
    env->ReleaseStringUTFChars(path, utf);
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
    int32_t status = cmpct_portable_entry_path(
        archive, static_cast<size_t>(index), nullptr, 0, &len);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    std::vector<uint8_t> path(len + 1, 0);
    status = cmpct_portable_entry_path(
        archive, static_cast<size_t>(index), path.data(), path.size(), &len);
    if (status != CMPCT_PORTABLE_OK) {
        throw_io(env, status);
        return nullptr;
    }
    return env->NewStringUTF(reinterpret_cast<const char *>(path.data()));
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
    const int32_t status =
        cmpct_portable_entry_info(archive, static_cast<size_t>(index), &info);
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
