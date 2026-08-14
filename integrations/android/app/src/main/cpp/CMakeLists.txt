cmake_minimum_required(VERSION 3.22.1)
project(cmpct_android LANGUAGES CXX)

add_library(cmpct_core SHARED IMPORTED)
set_target_properties(cmpct_core PROPERTIES
    IMPORTED_LOCATION "${CMAKE_CURRENT_LIST_DIR}/../jniLibs/${ANDROID_ABI}/libcmpct_core.so"
    # Footnote: Rust cdylibs do not guarantee an ELF SONAME. Without this property CMake may preserve
    # the absolute IMPORTED_LOCATION in DT_NEEDED, which works on the CI linker host but makes Android
    # try to dlopen a /home/runner/... path at runtime. Marking the missing SONAME explicitly makes the
    # linker record the packaged basename (`libcmpct_core.so`) instead.
    IMPORTED_NO_SONAME TRUE
)

add_library(cmpct_android SHARED cmpct_jni.cpp)
target_include_directories(cmpct_android PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../../../../../../native/cmpct-core/include"
)

# Footnote: the JNI layer contains no parser logic. It forwards ownership/enumeration/range calls to
# libcmpct_core so Android cannot drift into a second interpretation of revision-24 bytes.
target_link_libraries(cmpct_android PRIVATE cmpct_core)
