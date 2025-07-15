#pragma once
#include <cstdint>
typedef uint32_t reg;
typedef uint8_t word;
typedef reg addr;

union Register
{
    uint32_t u;
    int32_t i;
    void* ptr; // pointer to memory buffer (native)
    uint32_t addr; // jump target of this machine (virtual)
};

#include<vector>
#include <map>
#include <string>
#include <random>
#include <fstream>
#include "types.hpp"
class VM
{
#define writeU32(list, pos, value) *reinterpret_cast<reg*>(list+pos) = value
#define readU32(list, pos) (*reinterpret_cast<reg*>(list + pos))
#define readI32(list, pos) (*reinterpret_cast<int32_t*>(list + pos))

public:
	void LoadProgram(word* program);
	void RunProgram(bool profile=false);

    static const int ADDRESS_SIZE = 4;
private:
    word* program;
};

struct HeapEntry
{
public:
    HeapEntry(size_t size, HeapEntry* next);
    ~HeapEntry();
    void* ptr;
    HeapEntry* next = nullptr;
};

class Frame
{
public:
    Frame(int size, Frame* previous);
    ~Frame();
    std::vector<Register> registers;
    Frame* previous = nullptr;
    Frame* next = nullptr;
    uint32_t ip_backup;

    void print();

    void allocate(uint8_t targetRegister, size_t size);

    Frame* create_frame(int size);
private:
    HeapEntry* localHeap;
};


