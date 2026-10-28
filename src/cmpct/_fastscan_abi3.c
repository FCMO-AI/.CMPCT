#define PY_SSIZE_T_CLEAN
#define Py_LIMITED_API 0x030B0000
#include <Python.h>

/* Optional shipping stable-ABI exact built-in list path. False requires original validator
 * fallback: it does not authorize acceptance or provide a diagnostic.
 */
static PyObject *scan_refs(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *refs, *blobs, *size_obj;
    if (!PyArg_ParseTuple(args, "OOO", &refs, &blobs, &size_obj)) return NULL;
    if (!PyList_CheckExact(refs) || !PyList_CheckExact(blobs) ||
        !PyLong_CheckExact(size_obj)) Py_RETURN_FALSE;
    Py_ssize_t expected = PyLong_AsSsize_t(size_obj);
    if (expected < 0 || PyErr_Occurred()) {
        PyErr_Clear();
        Py_RETURN_FALSE;
    }
    const Py_ssize_t blob_count = PyList_Size(blobs);
    Py_ssize_t sum = 0;
    const Py_ssize_t n = PyList_Size(refs);
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *index_obj = PyList_GetItem(refs, i);
        if (!PyLong_CheckExact(index_obj)) Py_RETURN_FALSE;
        Py_ssize_t idx = PyLong_AsSsize_t(index_obj);
        if (idx < 0 || idx >= blob_count || PyErr_Occurred()) {
            PyErr_Clear();
            Py_RETURN_FALSE;
        }
        PyObject *row = PyList_GetItem(blobs, idx);
        if (!PyList_CheckExact(row) || PyList_Size(row) != 5) Py_RETURN_FALSE;
        PyObject *length_obj = PyList_GetItem(row, 1);
        if (!PyLong_CheckExact(length_obj)) Py_RETURN_FALSE;
        Py_ssize_t length = PyLong_AsSsize_t(length_obj);
        if (length < 0 || PyErr_Occurred()) {
            PyErr_Clear();
            Py_RETURN_FALSE;
        }
        if (length > PY_SSIZE_T_MAX - sum) Py_RETURN_FALSE;
        sum += length;
    }
    if (sum == expected) Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

/* Fused proof + bounded, in-memory logical offset checkpoints.
 *
 * As with scan_refs, any false result routes to the exact inherited Python
 * structural validator. A tuple is issued only after checking every descriptor
 * and the complete signed length; read_range uses it as a *search hint*, not as
 * authority for physical payload bytes or mutable on-disk state.
 *
 * Collect one logical prefix per 256 references while performing the existing
 * required native admission pass. No second full-index walk is required.
 * A 4M-reference cap keeps the optional metadata below ~0.6 MiB; larger valid
 * members remain safely admitted without index acceleration.
 */
static PyObject *scan_refs_index(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *refs, *blobs, *size_obj;
    if (!PyArg_ParseTuple(args, "OOO", &refs, &blobs, &size_obj)) return NULL;
    if (!PyList_CheckExact(refs) || !PyList_CheckExact(blobs) ||
        !PyLong_CheckExact(size_obj)) Py_RETURN_FALSE;
    Py_ssize_t expected = PyLong_AsSsize_t(size_obj);
    if (expected < 0 || PyErr_Occurred()) {
        PyErr_Clear();
        Py_RETURN_FALSE;
    }
    const Py_ssize_t n = PyList_Size(refs);
    const Py_ssize_t blob_count = PyList_Size(blobs);
    const int indexed = n >= 512 && n <= 4 * 1024 * 1024;
    PyObject *marks = indexed ? PyTuple_New((n + 255) / 256) : NULL;
    if (indexed && !marks) return NULL;
    Py_ssize_t sum = 0;
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *index_obj = PyList_GetItem(refs, i);
        if (!PyLong_CheckExact(index_obj)) goto invalid;
        Py_ssize_t idx = PyLong_AsSsize_t(index_obj);
        if (idx < 0 || idx >= blob_count || PyErr_Occurred()) {
            PyErr_Clear();
            goto invalid;
        }
        PyObject *row = PyList_GetItem(blobs, idx);
        if (!PyList_CheckExact(row) || PyList_Size(row) != 5) goto invalid;
        PyObject *length_obj = PyList_GetItem(row, 1);
        if (!PyLong_CheckExact(length_obj)) goto invalid;
        Py_ssize_t length = PyLong_AsSsize_t(length_obj);
        if (length < 0 || PyErr_Occurred()) {
            PyErr_Clear();
            goto invalid;
        }
        if (length > PY_SSIZE_T_MAX - sum) goto invalid;
        if (indexed && (i & 255) == 0) {
            PyObject *prefix = PyLong_FromSsize_t(sum);
            if (!prefix) goto error;
            /* PyTuple_SetItem steals the new-reference ownership even when
             * it reports failure. Never DECREF prefix a second time.
             */
            if (PyTuple_SetItem(marks, i / 256, prefix) < 0) {
                goto error;
            }
        }
        sum += length;
    }
    if (sum != expected) goto invalid;
    if (marks) return marks;
    Py_RETURN_TRUE;
invalid:
    Py_XDECREF(marks);
    Py_RETURN_FALSE;
error:
    Py_XDECREF(marks);
    return NULL;
}

static PyMethodDef Methods[] = {
    {"scan_refs", scan_refs, METH_VARARGS, "Optional exact built-in list admission; False requires original validator."},
    {"scan_refs_index", scan_refs_index, METH_VARARGS, "Fully admitted S_CHUNKS with bounded native prefix checkpoints."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef Module = {
    PyModuleDef_HEAD_INIT, "_fastscan_abi3", "CMPCT optional stable ABI fixed-chunk admission",
    -1, Methods, NULL, NULL, NULL, NULL
};
PyMODINIT_FUNC PyInit__fastscan_abi3(void) { return PyModule_Create(&Module); }
