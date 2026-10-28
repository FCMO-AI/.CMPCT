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
/* J24C10: read-time constant-stride proof, not an admission predicate.
 * Positive only when every interior chunk has the same positive length,
 * the last is positive and no larger, all refs are bounded exact ints,
 * and their sum matches the authenticated logical size. No offsets retained.
 */
static PyObject *uniform_stride(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *refs, *blobs, *size_obj;
    if (!PyArg_ParseTuple(args, "OOO", &refs, &blobs, &size_obj)) return NULL;
    if (!PyList_CheckExact(refs) || !PyList_CheckExact(blobs) ||
        !PyLong_CheckExact(size_obj)) return PyLong_FromLong(0);
    Py_ssize_t expected = PyLong_AsSsize_t(size_obj);
    if (expected <= 0 || PyErr_Occurred()) {
        PyErr_Clear();
        return PyLong_FromLong(0);
    }
    const Py_ssize_t n = PyList_Size(refs);
    const Py_ssize_t blob_count = PyList_Size(blobs);
    if (n <= 0) return PyLong_FromLong(0);
    Py_ssize_t total = 0, stride = 0;
    int uniform = 1;
    for (Py_ssize_t i = 0; i < n; ++i) {
        PyObject *index_obj = PyList_GetItem(refs, i);
        if (!PyLong_CheckExact(index_obj)) return PyLong_FromLong(0);
        Py_ssize_t idx = PyLong_AsSsize_t(index_obj);
        if (idx < 0 || idx >= blob_count || PyErr_Occurred()) {
            PyErr_Clear();
            return PyLong_FromLong(0);
        }
        PyObject *row = PyList_GetItem(blobs, idx);
        if (!PyList_CheckExact(row) || PyList_Size(row) != 5) return PyLong_FromLong(0);
        PyObject *length_obj = PyList_GetItem(row, 1);
        if (!PyLong_CheckExact(length_obj)) return PyLong_FromLong(0);
        Py_ssize_t length = PyLong_AsSsize_t(length_obj);
        if (length <= 0 || PyErr_Occurred()) {
            PyErr_Clear();
            return PyLong_FromLong(0);
        }
        if (length > PY_SSIZE_T_MAX - total) return PyLong_FromLong(0);
        total += length;
        if (i == 0) stride = length;
        else if ((i < n - 1 && length != stride) ||
                 (i == n - 1 && length > stride)) uniform = 0;
    }
    if (total != expected || !uniform) return PyLong_FromLong(0);
    return PyLong_FromSsize_t(stride);
}
static PyMethodDef Methods[] = {
    {"scan_refs", scan_refs, METH_VARARGS, "Optional exact built-in list admission; False requires original validator."},
    {"uniform_stride", uniform_stride, METH_VARARGS, "Optional positive exact fixed-stride proof for range access; zero requires original range path."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef Module = {
    PyModuleDef_HEAD_INIT, "_fastscan_abi3", "CMPCT optional stable ABI fixed-chunk admission",
    -1, Methods, NULL, NULL, NULL, NULL
};
PyMODINIT_FUNC PyInit__fastscan_abi3(void) { return PyModule_Create(&Module); }
