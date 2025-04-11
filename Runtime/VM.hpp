#pragma once
typedef unsigned char word;
typedef unsigned short int addr;
typedef short int offs;

#include<vector>
#include <map>
#include <string>
#include <random>
#include <fstream>
#include "types.hpp"
class VM
{
public:
    VM();
	void LoadProgram(word* program, int program_length, int memory_size, const char* nvram_file = "nvr.bin");
	void RunProgram();
    I StepProgram();
    virtual ~VM();

private:
    word* memory;
    const int IP_REGISTER = 0;
    const int SP_REGISTER = 1;
    const int FP_REGISTER = 2;
    const int PROGRAM_BEGIN = 0;
    addr stackStartPos = 0;
    addr registers[3];


    void* hConsole;
    std::random_device rd;
    std::mt19937 mt;

    std::string nvram_file;
    std::fstream nvram;

    const word WORD_SIZE = 1;  // size in array, not in bytes
    const word ADDRESS_SIZE = 2;
    int max_sp = 0;
    unsigned long long xic = 0;
    std::map<InterruptCodes, addr> handlers;


    static inline addr read16(word* list, int pos);
    static inline offs readoffs(word* list, int pos);
    static inline void write16(word* list, int pos, addr value);
    inline addr READ_REGISTER(int r);
    inline void WRITE_REGISTER(int r, addr value);
    inline void ADD_TO_REGISTER(int r, int value);

    inline void PUSH(word arg);
    inline void PUSH_ADDR(addr arg);
    inline void PUSHI(int arg);
    inline void PUSHI_ADDR(int arg);
    inline word POP();
    inline addr POP_ADDR();
    
    inline word read_next_program_byte(word& skip, int offset = 1);
    
    inline addr read_addr_from_program(word&, int offset = 1);
    inline offs read_offs_from_program(word&, int offset = 1);
    
    
    inline void CALL(addr address, int offset = 0);
    
    void STDLIB(int callNumber);
    void Free();
    void WriteStringToMemory(const std::string& str, int addr, int maxLen);
    std::string ReadStringFromMemory(int addr);
    void OpenNvramFile();

    int FgColorToVT100(Colors color);
    int BgColorToVT100(Colors color);

#ifndef _WIN32
    bool kbhit();
    char getchar2();
    void disableEcho();
#endif
};

class InterruptException : public std::exception
{
public:
    InterruptException(InterruptCodes code);
    InterruptCodes Code;
};
