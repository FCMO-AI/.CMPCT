#include <jni.h>
#include <stdint.h>

#include <string>
#include <vector>

#include "cmpct.h"

namespace {

CmpctArchive *from_handle(jlong handle) {
    return reinterpret_cast<CmpctArchive *>(static_cast<intptr_t>(handle));
}

jlong to_handle(CmpctArchive *archive) {
    return static_cast<jlong>(reinterpret_cast<intptr_t>(archive));
}

const char *status_name(int32_t status) {
    switch (status) {
        case CMPCT_OK: return "ok";
        case CMPCT_ERR_NULL: return "null argument";
        case CMPCT_ERR_IO: return "I/O or truncated archive";
        case CMPCT_ERR_FORMAT: return "invalid/corrupt CMPCT archive";
        case CMPCT_ERR_LIMIT: return "CMPCT resource limit exceeded";
        case CMPCT_ERR_UTF8: return "invalid UTF-8 path";
        case CMPCT_ERR_RANGE: return "range outside CMPCT member";
        case CMPCT_ERR_UNSUPPORTED: return "CMPCT representation not yet supported by native core";
        case CMPCT_ERR_PANIC: return "native CMPCT panic boundary triggered";
        default: return "unknown CMPCT native error";
    }
}

void throw_io(JNIEnv *env, int32_t status) {
    jclass cls = env->FindClass("java/io/IOException");
    if (cls != nullptr) {
        env->ThrowNew(cls, status_name(status));
    }
}

bool require_archive(JNIEnv *env, jlong handle, CmpctArchive **out) {
    *out = from_handle(handle);
    if (*out != nullptr) return true;
    throw_io(env, CMPCT_ERR_NULL);
    return false;
}

}  // namespace

extern "C" JNIEXPORT jlong JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeOpen(JNIEnv *env, jclass, jstring path) {
    if (path == nullptr) {
        throw_io(env, CMPCT_ERR_NULL);
        return 0;
    }
    const char *utf = env->GetStringUTFChars(path, nullptr);
    if (utf == nullptr) return 0;  // JVM already raised OOM.
    CmpctArchive *archive = nullptr;
    const int32_t status = cmpct_open(utf, &archive);
    env->ReleaseStringUTFChars(path, utf);
    if (status != CMPCT_OK) {
        throw_io(env, status);
        return 0;
    }
    return to_handle(archive);
}

extern "C" JNIEXPORT void JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeClose(JNIEnv *, jclass, jlong handle) {
    CmpctArchive *archive = from_handle(handle);
    if (archive != nullptr) cmpct_close(archive);
}

extern "C" JNIEXPORT jint JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeRevision(JNIEnv *env, jclass, jlong handle) {
    CmpctArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return 0;
    return static_cast<jint>(cmpct_revision(archive));
}

extern "C" JNIEXPORT jint JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryCount(JNIEnv *env, jclass, jlong handle) {
    CmpctArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return 0;
    return static_cast<jint>(cmpct_entry_count(archive));
}

extern "C" JNIEXPORT jstring JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryPath(JNIEnv *env, jclass, jlong handle, jint index) {
    CmpctArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0) {
        throw_io(env, CMPCT_ERR_RANGE);
        return nullptr;
    }

    size_t len = 0;
    int32_t status = cmpct_entry_path(archive, static_cast<size_t>(index), nullptr, 0, &len);
    if (status != CMPCT_OK) {
        throw_io(env, status);
        return nullptr;
    }
    std::vector<char> path(len + 1, 0);
    status = cmpct_entry_path(archive, static_cast<size_t>(index), path.data(), path.size(), &len);
    if (status != CMPCT_OK) {
        throw_io(env, status);
        return nullptr;
    }
    return env->NewStringUTF(path.data());
}

extern "C" JNIEXPORT jlongArray JNICALL
Java_ai_fcmo_cmpct_CmpctNative_nativeEntryInfo(JNIEnv *env, jclass, jlong handle, jint index) {
    CmpctArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0) {
        throw_io(env, CMPCT_ERR_RANGE);
        return nullptr;
    }

    CmpctEntryInfo info{};
    const int32_t status = cmpct_entry_info(archive, static_cast<size_t>(index), &info);
    if (status != CMPCT_OK) {
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
    CmpctArchive *archive = nullptr;
    if (!require_archive(env, handle, &archive)) return nullptr;
    if (index < 0 || offset < 0 || length < 0) {
        throw_io(env, CMPCT_ERR_RANGE);
        return nullptr;
    }

    std::vector<uint8_t> buffer(static_cast<size_t>(length));
    size_t read = 0;
    const int32_t status = cmpct_entry_read_range(
        archive,
        static_cast<size_t>(index),
        static_cast<uint64_t>(offset),
        buffer.empty() ? nullptr : buffer.data(),
        buffer.size(),
        &read);
    if (status != CMPCT_OK) {
        throw_io(env, status);
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
