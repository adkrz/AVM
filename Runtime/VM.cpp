#include "VM.hpp"
#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <fstream>
#include "magic_enum.hpp"

#define NOMINMAX
#ifdef _WIN32
#include <Windows.h>
#include <conio.h>
#else
#include <termios.h>
#include <unistd.h>
#include <sys/ioctl.h>
#undef NZERO // avoid conflict with <sys/ioctl.h>
#endif


void VM::LoadProgram(word* program)
{
    this->program = program;
}


void VM::RunProgram(bool profile)
{
    Frame* current_frame = nullptr;
    uint8_t arg8;
    uint8_t arg8a;
    reg arg32;
    int32_t argi32;
    int64_t IP = 0;

    if (profile)
        std::cerr << "Profiler not implemented" << std::endl;

    while (true)
    {
        auto instr = (I)program[IP++];
        switch (instr)
        {
            case I::NOP: [[unlikely]]
                break;
            case I::NEW_FRAME:
                arg8 = program[IP++];
                current_frame = new Frame(arg8, current_frame);
                break;
            case I::MOV_RU:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                IP += 4;
                current_frame->registers[arg8] = arg32;
                break;
            case I::MOV_RI:
                arg8 = program[IP++];
                argi32 = readI32(program, IP);
                IP += 4;
                current_frame->registers[arg8] = argi32;
                break;
            case I::MOV_RR:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8] = current_frame->registers[arg8a];
                break;
            case I::ADD_RU:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                IP += 4;
                current_frame->registers[arg8] += arg32;
                break;
            case I::ADD_RI:
                arg8 = program[IP++];
                argi32 = readI32(program, IP);
                IP += 4;
                current_frame->registers[arg8] += argi32;
                break;
            case I::ADD_RI8:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8] += arg8a;
                break;
            case I::ADD_RR:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8] += current_frame->registers[arg8a];
                break;
            case I::JMP:
                IP = readU32(program, IP);;
                break;
            case I::JMP_R:
                IP = current_frame->registers[program[IP]];
                break;
            case I::JT:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                if (current_frame->registers[arg8])
                    IP = arg32;
                else IP++;
                break;
            case I::JF:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                if (!current_frame->registers[arg8])
                    IP = arg32;
                else IP++;
                break;
            case I::JT_R:
                arg8 = program[IP++];
                arg8a = program[IP++];
                if (current_frame->registers[arg8])
                    IP = current_frame->registers[arg8a];
                else IP++;
                break;
            case I::JF_R:
                arg8 = program[IP++];
                arg8a = program[IP++];
                if (!current_frame->registers[arg8])
                    IP = current_frame->registers[arg8a];
                else IP++;
                break;
            case I::PRINT_FRAMES:
                current_frame->print();
                break;
            case I::HALT:
                return;
            default:
                std::cerr << "Instruction not implemented: " << instr << std::endl;
                break;;
        }
    }
}

Frame::Frame(int size, Frame* previous):
    previous(previous)
{
    registers.resize(size);
}

void Frame::print()
{
    for (size_t i =0; i<registers.size(); i++)
        std::cout << "R" << i << ": " << registers[i] << " (" << readI32(registers.data(), i) << ")" << std::endl;
    std::cout << "RET: " << return_value  << " (" << *reinterpret_cast<int32_t*>(&return_value) << ")" << std::endl;
    if (previous)
    {
        std::cout << "Previous frame: " << std::endl;
        previous->print();
    }
}