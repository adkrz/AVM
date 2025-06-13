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
#define write16(list, pos, value) *reinterpret_cast<addr*>(list+pos) = value

public:
    VM();
	void LoadProgram(word* program, int program_length, int memory_size, const char* nvram_file = "nvr.bin");
	void RunProgram(bool profile=false);
    virtual ~VM();

    static const int PROGRAM_BEGIN = 0; // place where the program starts in memory
    static const word ADDRESS_SIZE = 2; // size in bytes of address (register, memory slot)
private:
    word* memory;
    
    
    static const word WORD_SIZE = 1;  // size in array, not in bytes
    
    addr stackStartPos = 0;
    addr IP, SP, FP, POINTER;
    bool carry = false;


    void* hConsole;
    std::random_device rd;
    std::mt19937 mt;

    std::string nvram_file;
    std::fstream nvram;

    
    //int max_sp = 0;
    std::map<InterruptCodes, addr> handlers;

    static inline offs readoffs(word* list, int pos);
   
    inline void PUSH(word arg);
    inline void PUSH_ADDR(addr arg);
    inline void PUSHI(int arg);
    inline void PUSHI_ADDR(int arg);
    inline word POP();
    inline addr POP_ADDR();
    
    inline word read_next_program_byte(word& skip);
    
    inline addr read_addr_from_program(word&, int offset = 1);
    inline offs read_offs_from_program(word&, int offset = 1);
    
    
    inline void CALL(addr address, int offset = 0);
    
    InterruptCodes STDLIB(int callNumber); // returns error in case of problem, or 0
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

