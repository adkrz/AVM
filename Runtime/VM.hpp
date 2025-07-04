#pragma once
#include <cstdint>
typedef uint32_t reg;
typedef uint8_t word;
typedef reg addr;

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
	void LoadProgram(word* program, int program_length);
	void RunProgram(bool profile=false);

    static const int ADDRESS_SIZE = 4;
private:
    word* program;
};

class Frame
{
public:
    Frame(int size, Frame* previous);
    std::vector<reg> registers;
    Frame* previous = nullptr;
    uint32_t ip_backup;
    reg return_value;

    void print();
};

