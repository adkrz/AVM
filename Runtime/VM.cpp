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
    uint32_t IP = 0;
    uint32_t aboutToCall = 0;

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
            case I::MOV_RI:
                arg8 = program[IP++];
                argi32 = readU32(program, IP);
                IP += 4;
                current_frame->registers[arg8].i = argi32;
                break;
            case I::MOV_RR:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8] = current_frame->registers[arg8a];
                break;
            case I::ADD_RI:
                arg8 = program[IP++];
                argi32 = readU32(program, IP);
                IP += 4;
                current_frame->registers[arg8].i += argi32;
                break;
            case I::ADD_RI8:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8].i += arg8a;
                break;
            case I::ADD_RR:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8].i += current_frame->registers[arg8a].i;
                break;
            case I::JMP:
                IP = readU32(program, IP);
                break;
            case I::JMP_R:
                IP = current_frame->registers[program[IP]].addr;
                break;
            case I::JT:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                if (current_frame->registers[arg8].i)
                    IP = arg32;
                else IP+=ADDRESS_SIZE;
                break;
            case I::JF:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                if (!current_frame->registers[arg8].i)
                    IP = arg32;
                else IP+=ADDRESS_SIZE;
                break;
            case I::JT_R:
                arg8 = program[IP++];
                arg8a = program[IP++];
                if (current_frame->registers[arg8].i)
                    IP = current_frame->registers[arg8a].addr;
                else IP+=ADDRESS_SIZE;
                break;
            case I::JF_R:
                arg8 = program[IP++];
                arg8a = program[IP++];
                if (!current_frame->registers[arg8].i)
                    IP = current_frame->registers[arg8a].addr;
                else IP+=ADDRESS_SIZE;
                break;
            case I::PREPARE_CALL:
            case I::PREPARE_CALL_R:
                if (instr == I::PREPARE_CALL)
                {
                    aboutToCall = readU32(program, IP);
                    IP += ADDRESS_SIZE;
                }
                else
                {
                    aboutToCall = current_frame->registers[program[IP++]].addr;
                }
                arg8 = 0; // frame size
                if (program[aboutToCall] == I::NEW_FRAME)
                {
                    arg8 = program[aboutToCall+1];
                    aboutToCall += 2;
                }
                current_frame->create_frame(arg8);
                break;
            case I::CALL:
                current_frame->ip_backup = IP;
                IP = aboutToCall;
                current_frame = current_frame->next;
                break;
            case I::RET:
                current_frame = current_frame->previous;
                IP = current_frame->ip_backup;
                break;
            case I::COPY_TO_FUNC:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->next->registers[arg8a] = current_frame->registers[arg8];
                break;
            case I::COPY_CONST_TO_FUNC:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                IP += 4;
                current_frame->next->registers[arg8].u = arg32;
                break;
            case I::COPY_FROM_FUNC:
                arg8 = program[IP++];
                arg8a = program[IP++];
                current_frame->registers[arg8a] = current_frame->next->registers[arg8];
                break;
            case I::COMPARE:
            case I::COMPARE_I:
            case I::COMPARE_JF:
            case I::COMPARE_I_JF:
                arg8 = program[IP++]; // compare type
                {
                    int32_t tmp1 = current_frame->registers[program[IP++]].i;
                    int32_t tmp2;
                    if (instr == I::COMPARE || instr == I::COMPARE_JF)
                    {
                        tmp2 = current_frame->registers[program[IP++]].i;
                    }
                    else
                    {
                        tmp2 = readU32(program, IP);
                        IP += 4;
                    }
                    reg result = 0;
                    switch (arg8)
                    {
                    case 0:
                        result = tmp1 == tmp2;
                        break;
                    case 1:
                        result = tmp1 != tmp2;
                        break;
                    case 2:
                        result = tmp1 > tmp2;
                        break;
                    case 3:
                        result = tmp1 >= tmp2;
                        break;
                    case 4:
                        result = tmp1 < tmp2;
                        break;
                    case 5:
                        result = tmp1 <= tmp2;
                        break;
                    default:
                        break;
                    }
                    if (instr == I::COMPARE || instr == I::COMPARE_I)
                    {
                        current_frame->registers[program[IP++]].u = result;
                    }
                    else
                    {
                        // JF:
                        if (!result)
                            IP = readU32(program, IP);
                        else IP+=ADDRESS_SIZE;
                    }
                }
                break;
            case I::LOCAL_ALLOC:
                arg8 = program[IP++];
                arg32 = readU32(program, IP);
                IP += ADDRESS_SIZE;
                current_frame->allocate(arg8, arg32);
                break;
            case I::LOAD:
            {
                arg8 = program[IP++]; // reg no with base address
                arg32 = readU32(program, IP); // scale
                IP += ADDRESS_SIZE;
                arg8a = program[IP++]; // reg no with no of elements
                auto arg32a = readU32(program, IP); //offset
                IP += ADDRESS_SIZE;
                auto arg8b = program[IP++]; // target reg to write to
                uint32_t* ptr = (uint32_t*)(current_frame->registers[arg8].ptr + arg32 * current_frame->registers[arg8a].u + arg32a);
                current_frame->registers[arg8b].u = *ptr;
            }
                break;
            case I::STORE:
            {
                arg8 = program[IP++]; // reg no with base address
                arg32 = readU32(program, IP); // scale
                IP += ADDRESS_SIZE;
                arg8a = program[IP++]; // reg no with no of elements
                auto arg32a = readU32(program, IP); //offset
                IP += ADDRESS_SIZE;
                auto arg8b = program[IP++]; // src reg to read from
                uint32_t* ptr = (uint32_t*)(current_frame->registers[arg8].ptr + arg32 * current_frame->registers[arg8a].u + arg32a);
                *ptr = current_frame->registers[arg8b].u;
            }
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

HeapEntry::HeapEntry(size_t size, HeapEntry* next): ptr(malloc(size)), next(next)
{
}

HeapEntry::~HeapEntry()
{
    if (next)
        delete next;
}

Frame::Frame(int size, Frame* previous):
    registers(size),
    previous(previous),
    localHeap(nullptr)
{
}

Frame::~Frame()
{
    if (next)
        delete next;
    if (localHeap)
        delete localHeap;
}

void Frame::print()
{
    for (size_t i =0; i<registers.size(); i++)
        std::cout << "R" << i << ": " << registers[i].u << " (" << registers[i].i << ")" << std::endl;
    if (previous)
    {
        std::cout << "Previous frame: " << std::endl;
        previous->print();
    }
}

Frame* Frame::create_frame(int size)
{
    if (next) delete next;
    next = new Frame(size, this);
    return next;
}

void Frame::allocate(uint8_t targetRegister, size_t size)
{
    localHeap = new HeapEntry(size, localHeap);
    registers[targetRegister].ptr = localHeap->ptr;
}