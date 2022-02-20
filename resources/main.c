#include <Python.h>

int main() {
    Py_Initialize();
    PyRun_SimpleFile(_Py_fopen("main.py", "r+"), "main.py");
    Py_Finalize();
}