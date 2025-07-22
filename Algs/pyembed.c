#include <Python.h>
#include <stdlib.h>
#include <string.h>
#include "pyembed.h"

static PyObject *pModule = NULL;
static PyObject *pFunc = NULL;

int InitPython() {
    Py_Initialize();

    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.path.append('.')");

    PyObject *pName = PyUnicode_DecodeFSDefault("pymodule");
    pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (!pModule) {
        PyErr_Print();
        return 0;
    }

    pFunc = PyObject_GetAttrString(pModule, "process");

    if (!(pFunc && PyCallable_Check(pFunc))) {
        PyErr_Print();
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
        return 0;
    }

    return 1;  // Success
}

char* CallProcess(const char* text) {
    if (!pFunc) return NULL;

    PyObject *pArgs = PyTuple_New(1);
    PyObject *pValue = PyUnicode_FromString(text);
    PyTuple_SetItem(pArgs, 0, pValue);

    PyObject *pResult = PyObject_CallObject(pFunc, pArgs);
    Py_DECREF(pArgs);

    if (pResult != NULL) {
        PyObject *bytes = PyUnicode_AsEncodedString(pResult, "utf-8", "strict");
        char* result = strdup(PyBytes_AsString(bytes));
        Py_DECREF(bytes);
        Py_DECREF(pResult);
        return result;
    } else {
        PyErr_Print();
    }

    return NULL;
}

void FinalizePython() {
    Py_XDECREF(pFunc);
    Py_XDECREF(pModule);
    Py_Finalize();
}
