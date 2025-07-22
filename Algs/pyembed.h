#ifndef PYEMBED_H
#define PYEMBED_H

int InitPython();
void FinalizePython();
char* CallProcess(const char*);

#endif