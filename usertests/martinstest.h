#ifndef PXAR_MARTINSTEST_H
#define PXAR_MARTINSTEST_H

#include <iostream>
#include <PixTest.hh>
#include <dictionaries.h>

class CmdProc;

// WER KENNT IHN NICHT - DEN MARTINSTEST :D

class DLLEXPORT MartinsTest: public PixTest {
public:
MartinsTest(PixSetup *, std::string);
MartinsTest();
virtual ~MartinsTest();
void init();

void doTest();
void createWidgets();
void flush(std::string s);
void runCommand(std::string s);
void stopTest();

private:


CmdProc * cmd;

};

#endif //PXAR_MARTINSTEST_H
