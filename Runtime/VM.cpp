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

VM::VM() : memory(nullptr), mt(rd())
{
#ifdef _WIN32
    hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD dwOriginalOutMode = 0;
    GetConsoleMode(hConsole, &dwOriginalOutMode);
    DWORD newMode = dwOriginalOutMode | ENABLE_VIRTUAL_TERMINAL_PROCESSING | DISABLE_NEWLINE_AUTO_RETURN;
    SetConsoleMode(hConsole, newMode);
#endif
}

VM::~VM()
{
    Free();
}

#define read16(list, pos) (*reinterpret_cast<addr*>(list + pos))

#define HANDLE_EXCEPTION(code) if (handlers.count(code))\
{\
    CALL(handlers[code], -ADDRESS_SIZE);\
    skip = 0;\
}\
else\
{\
    if (nvram.is_open())\
    {\
        nvram.close();\
    }\
    std::cerr << "Program interrupted: " << code;\
    return;\
}

#define BIN_OP(op) { memory[SP-2] = memory[SP-1] op memory[SP-2]; SP--; }
#define BIN_OP_INV(op) { memory[SP-2] = memory[SP-2] op memory[SP-1]; SP--; }
#define LOGICAL_OP(op) { memory[SP - 2] = memory[SP - 1] op memory[SP - 2] ? 1 : 0; SP--; }
#define OP_WITH_CONST(op, con) { memory[SP-1] = memory[SP-1] op con; }

#define BIN_OP_16(op) { write16(memory, SP-4, read16(memory,SP-2) op read16(memory,SP-4)); SP-=2; }
#define BIN_OP_16_INV(op) { write16(memory, SP-4, read16(memory,SP-4) op read16(memory,SP-2)); SP-=2; }
#define LOGICAL_OP_16(op) { memory[SP-4] = read16(memory,SP-2) op read16(memory,SP-4) ? 1 : 0 ; SP-=3; }
#define OP_WITH_CONST_16(op, con) { write16(memory, SP-2, read16(memory,SP-2) op con); }

void VM::LoadProgram(word* program, int program_length, int memory_size, const char* nvr_file)
{
    if (memory_size < program_length + 3) // plus registers
    {
        memory_size = program_length + 3;
    }
    Free();
    memory = new word[memory_size];

    IP = PROGRAM_BEGIN;

    for (int i = 0; i < program_length; i++)
    {
        memory[i + PROGRAM_BEGIN] = program[i];
    }
    stackStartPos = (addr)(program_length + PROGRAM_BEGIN);
    SP = stackStartPos;
    FP = stackStartPos;
    POINTER = 0;
    //max_sp = SP;
    handlers.clear();
    nvram_file = nvr_file;
}


inline offs VM::readoffs(word* list, int pos) { return list[pos + 1] * 256 + list[pos]; }


#define PUSH(arg) { memory[SP] = arg; SP++;}

#define PUSH_ADDR(arg) { write16(memory, SP, arg); SP += ADDRESS_SIZE; }

#define PUSHI(arg) { PUSH((word)arg); }

#define PUSHI_ADDR(arg) { PUSH_ADDR((addr)arg); };

inline word VM::POP() { auto v = memory[SP - 1]; SP--; return v; }

inline addr VM::POP_ADDR() { auto v = read16(memory, SP - ADDRESS_SIZE); SP -= ADDRESS_SIZE; return v; }

inline word VM::read_next_program_byte(word& skip)
{
    auto instr = IP;
    auto targ = memory[instr + 1];
    skip += WORD_SIZE;
    return targ;
}

inline addr VM::read_addr_from_program(word& skip, int offset)
{
    auto instr = IP;
    auto targ = read16(memory, instr + offset);
    skip += ADDRESS_SIZE;
    return targ;
}

inline offs VM::read_offs_from_program(word& skip, int offset)
{
    auto instr = IP;
    auto targ = readoffs(memory, instr + offset);
    skip += ADDRESS_SIZE;
    return targ;
}

inline void VM::CALL(addr address, int offset)
{
    PUSHI_ADDR((IP + offset));
    PUSH_ADDR(FP);
    IP = address;
    FP = SP;
}

void VM::RunProgram(bool profile)
{
    word skip;
    I instr;
    word arg;
    addr address;
    int offset;
    addr val;
    word tmp;
    int signedResult;
#ifdef _MSC_VER
    int direction; // for MSVC
#endif

#ifdef WITH_PROFILER
    long long counters[256];
    for (int i = 0; i < 256; i++)
        counters[i] = 0;
    addr max_sp = 0;
#else
    if (profile)
        std::cerr << "Program was built without profiler support. Use -DWITH_PROFILER to enable profiling." << std::endl;
#endif

#ifndef _MSC_VER
    // Computed goto jump table for GCC/Clang
    static void* jump_table[] = {
        &&LABEL_PUSH, &&LABEL_PUSH16, &&LABEL_PUSH16_REL, &&LABEL_PUSHN, &&LABEL_PUSHN2, &&LABEL_PUSH_NEXT_SP, &&LABEL_PUSH_STACK_START,
        &&LABEL_POP, &&LABEL_POPN, &&LABEL_POPN2, &&LABEL_PUSH_REG, &&LABEL_POP_REG, &&LABEL_ADD, &&LABEL_ADD16, &&LABEL_ADD16C, &&LABEL_SUB16C,
        &&LABEL_ADDC, &&LABEL_SUBC, &&LABEL_MULC, &&LABEL_SUB, &&LABEL_SUB2, &&LABEL_SUB16, &&LABEL_SUB216, &&LABEL_DIV, &&LABEL_DIV2, &&LABEL_DIV216,
        &&LABEL_MOD, &&LABEL_MOD16, &&LABEL_MUL, &&LABEL_MUL16, &&LABEL_MUL16C, &&LABEL_EQ, &&LABEL_NE, &&LABEL_LESS, &&LABEL_LESS_OR_EQ,
        &&LABEL_GREATER, &&LABEL_GREATER_OR_EQ, &&LABEL_ZERO, &&LABEL_NZERO, &&LABEL_EQ16, &&LABEL_NE16, &&LABEL_LESS16, &&LABEL_LESS_OR_EQ16,
        &&LABEL_GREATER16, &&LABEL_GREATER_OR_EQ16, &&LABEL_ZERO16, &&LABEL_NZERO16, &&LABEL_AND, &&LABEL_OR, &&LABEL_LAND, &&LABEL_LOR,
        &&LABEL_XOR, &&LABEL_LSH, &&LABEL_RSH, &&LABEL_FLIP, &&LABEL_AND16, &&LABEL_OR16, &&LABEL_XOR16, &&LABEL_LSH16, &&LABEL_RSH16, &&LABEL_FLIP16,
        &&LABEL_NOT, &&LABEL_INC, &&LABEL_DEC, &&LABEL_INC16, &&LABEL_DEC16, &&LABEL_EXTEND, &&LABEL_DOWNCAST, &&LABEL_JMP, &&LABEL_JMP_REL,
        &&LABEL_JF, &&LABEL_JF16, &&LABEL_JT, &&LABEL_JT16, &&LABEL_JF_REL, &&LABEL_JT_REL, &&LABEL_JMP2, &&LABEL_JT2, &&LABEL_JF2, &&LABEL_CASE,
        &&LABEL_ELSE, &&LABEL_CASE_REL, &&LABEL_ELSE_REL, &&LABEL_LOAD_GLOBAL, &&LABEL_STORE_GLOBAL, &&LABEL_STORE_GLOBAL2, &&LABEL_LOAD_GLOBAL16,
        &&LABEL_STORE_GLOBAL16, &&LABEL_STORE_GLOBAL216, &&LABEL_LOAD_LOCAL, &&LABEL_LOAD_ARG, &&LABEL_LOAD_LOCAL16, &&LABEL_LOAD_ARG16,
        &&LABEL_STORE_LOCAL, &&LABEL_STORE_ARG, &&LABEL_STORE_LOCAL16, &&LABEL_STORE_ARG16, &&LABEL_STORE_LOCAL_KEEP, &&LABEL_STORE_LOCAL_KEEP16,
        &&LABEL_LOAD_NVRAM, &&LABEL_STORE_NVRAM, &&LABEL_CALL, &&LABEL_CALL2, &&LABEL_CALL_REL, &&LABEL_RET, &&LABEL_SWAP, &&LABEL_SWAP16,
        &&LABEL_DUP, &&LABEL_DUP16, &&LABEL_ROLL3, &&LABEL_NEG, &&LABEL_NOP, &&LABEL_DEBUGGER, &&LABEL_INTERRUPT_HANDLER, &&LABEL_SYSCALL,
        &&LABEL_SYSCALL2, &&LABEL_HALT, &&LABEL_MACRO_POP_EXT_X2_ADD16, &&LABEL_MACRO_POP_EXT_X2_ADD16_LG16, &&LABEL_MACRO_ADD8_TO_16,
        &&LABEL_MACRO_ADD16_TO_8, &&LABEL_MACRO_ANDX, &&LABEL_MACRO_ORX, &&LABEL_MACRO_LSH16_BY8, &&LABEL_MACRO_INC_LOCAL, &&LABEL_MACRO_DEC_LOCAL,
        &&LABEL_MACRO_INC_LOCAL16, &&LABEL_MACRO_DEC_LOCAL16, &&LABEL_MACRO_X2, &&LABEL_MACRO_X216, &&LABEL_MACRO_DIV2, &&LABEL_MACRO_X3,
        &&LABEL_MACRO_DIV3, &&LABEL_GET_PTR, &&LABEL_LOAD_GLOBAL_PTR, &&LABEL_STORE_GLOBAL_PTR, &&LABEL_LOAD_GLOBAL_PTR16, &&LABEL_STORE_GLOBAL_PTR16,
        &&LABEL_MACRO_CONDITIONAL_JF, &&LABEL_MACRO_SET_LOCAL, &&LABEL_MACRO_SET_LOCAL16
        // Add more labels if your enum has more entries
    };
#endif

    while (true)
    {
        instr = (I)memory[IP];
#ifdef WITH_PROFILER
        if (profile)
        {
            if (SP > max_sp)
                max_sp = SP;
            counters[instr]++;
        }
#endif

        skip = WORD_SIZE;

#ifndef _MSC_VER
        if ((size_t)instr >= sizeof(jump_table) / sizeof(jump_table[0])) {
            std::cerr << "Instruction not implemented: " << std::to_string(instr) << std::endl;
            throw std::runtime_error("Instruction not implemented: " + std::to_string(instr));
        }
        goto *jump_table[(size_t)instr];

#define NEXT_INSTR() do { IP += skip; instr = (I)memory[IP]; skip = WORD_SIZE; goto *jump_table[(size_t)instr]; } while(0)
#else
#define NEXT_INSTR() break
#endif

        // --- All labels below must match the enum order! ---
LABEL_PUSH:
            arg = read_next_program_byte(skip);
            PUSH(arg);
            NEXT_INSTR();
LABEL_PUSH16:
            address = read_addr_from_program(skip);
            PUSH_ADDR(address);
            NEXT_INSTR();
LABEL_PUSH16_REL:
            offset = read_offs_from_program(skip);
            address = (addr)(IP + offset);
            PUSH_ADDR(address);
            NEXT_INSTR();
LABEL_PUSHN:
            arg = read_next_program_byte(skip);
            SP += arg;
            NEXT_INSTR();
LABEL_PUSHN2:
            SP += POP();
            NEXT_INSTR();
LABEL_PUSH_NEXT_SP:
            PUSHI_ADDR(SP + ADDRESS_SIZE);
            NEXT_INSTR();
LABEL_PUSH_STACK_START:
            PUSH_ADDR(stackStartPos);
            NEXT_INSTR();
LABEL_POP:
            POP();
            NEXT_INSTR();
LABEL_POPN:
            arg = read_next_program_byte(skip);
            SP -= arg;
            NEXT_INSTR();
LABEL_POPN2:
            SP -= POP();
            NEXT_INSTR();
LABEL_PUSH_REG:
            arg = read_next_program_byte(skip);
            if (arg == 0)
            {
                PUSH_ADDR(IP);
            }
            else if (arg == 1)
            {
                PUSH_ADDR(SP);
            }
            else if (arg == 2)
            {
                PUSH_ADDR(FP);
            }
            NEXT_INSTR();
LABEL_POP_REG:
            arg = read_next_program_byte(skip);
            if (arg == 0)
                IP = POP_ADDR();
            else if (arg == 1)
                SP = POP_ADDR();
            else if (arg == 2)
                FP = POP_ADDR();
            NEXT_INSTR();
LABEL_ADD:
            BIN_OP(+);
            NEXT_INSTR();
LABEL_ADD16:
            BIN_OP_16(+);
            NEXT_INSTR();
LABEL_ADD16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(+, address);
            NEXT_INSTR();
LABEL_SUB16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(-, address);
            NEXT_INSTR();
LABEL_ADDC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(+, address);
            NEXT_INSTR();
LABEL_SUBC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(-, address);
            NEXT_INSTR();
LABEL_MULC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(*, address);
            NEXT_INSTR();
LABEL_SUB:
            BIN_OP(-);
            NEXT_INSTR();
LABEL_SUB2:
            BIN_OP_INV(-);
            NEXT_INSTR();
LABEL_SUB16:
            BIN_OP_16(-);
            NEXT_INSTR();
LABEL_SUB216:
            BIN_OP_16_INV(-);
            NEXT_INSTR();
LABEL_DIV:
            if (memory[SP-2] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP(/)
            NEXT_INSTR();
LABEL_DIV2:
            if (memory[SP-1] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP_INV(/)
            NEXT_INSTR();
LABEL_DIV216:
            {
                auto tmp1 = POP_ADDR();
                auto tmp2 = POP_ADDR();
                if (tmp1 == 0)
                {
                    HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
                }
                PUSHI(tmp2 / tmp1);
            }
            NEXT_INSTR();
LABEL_MOD:
            if (memory[SP - 2] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP(%)
            NEXT_INSTR();
LABEL_MOD16:
            address = POP_ADDR();
            val = POP_ADDR();
            if (val == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            PUSHI_ADDR(address % val);
            NEXT_INSTR();
LABEL_MUL:
            BIN_OP(*);
            NEXT_INSTR();
LABEL_MUL16:
            BIN_OP_16(*);
            NEXT_INSTR();
LABEL_MUL16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(*, address);
            NEXT_INSTR();
LABEL_EQ:
            LOGICAL_OP(==);
            NEXT_INSTR();
LABEL_NE:
            LOGICAL_OP(!=);
            NEXT_INSTR();
LABEL_LESS:
            LOGICAL_OP(<);
            NEXT_INSTR();
LABEL_LESS_OR_EQ:
            LOGICAL_OP(<=);
            NEXT_INSTR();
LABEL_GREATER:
            LOGICAL_OP(>);
            NEXT_INSTR();
LABEL_GREATER_OR_EQ:
            LOGICAL_OP(>=);
            NEXT_INSTR();
LABEL_ZERO:
            memory[SP - 1] = (word)(memory[SP - 1] == 0 ? 1 : 0);
            NEXT_INSTR();
LABEL_NZERO:
            memory[SP - 1] = (word)(memory[SP - 1] != 0 ? 1 : 0);
            NEXT_INSTR();
LABEL_EQ16:
            LOGICAL_OP_16(==);
            NEXT_INSTR();
LABEL_NE16:
            LOGICAL_OP_16(!=);
            NEXT_INSTR();
LABEL_LESS16:
            LOGICAL_OP_16(<);
            NEXT_INSTR();
LABEL_LESS_OR_EQ16:
            LOGICAL_OP_16(<=);
            NEXT_INSTR();
LABEL_GREATER16:
            LOGICAL_OP_16(>);
            NEXT_INSTR();
LABEL_GREATER_OR_EQ16:
            LOGICAL_OP_16(>=);
            NEXT_INSTR();
LABEL_ZERO16:
            PUSHI(POP_ADDR() == 0 ? 1 : 0);
            NEXT_INSTR();
LABEL_NZERO16:
            PUSHI(POP_ADDR() != 0 ? 1 : 0);
            NEXT_INSTR();
LABEL_AND:
            BIN_OP(&);
            NEXT_INSTR();
LABEL_OR:
            BIN_OP(|);
            NEXT_INSTR();
LABEL_LAND:
            PUSHI((POP() != 0) && (POP() != 0) ? 1 : 0);
            NEXT_INSTR();
LABEL_LOR:
            PUSHI((POP() != 0) || (POP() != 0) ? 1 : 0);
            NEXT_INSTR();
LABEL_XOR:
            BIN_OP(^);
            NEXT_INSTR();
LABEL_LSH:
            BIN_OP_INV(<<);
            NEXT_INSTR();
LABEL_RSH:
            BIN_OP_INV(>>);
            NEXT_INSTR();
LABEL_FLIP:
            PUSHI(~POP());
            NEXT_INSTR();
LABEL_AND16:
            BIN_OP_16(&);
            NEXT_INSTR();
LABEL_OR16:
            BIN_OP_16(|);
            NEXT_INSTR();
LABEL_XOR16:
            BIN_OP_16(^);
            NEXT_INSTR();
LABEL_LSH16:
            BIN_OP_16_INV(<< );
            NEXT_INSTR();
LABEL_RSH16:
            BIN_OP_16_INV(>>);
            NEXT_INSTR();
LABEL_FLIP16:
            PUSHI_ADDR(~POP_ADDR());
            NEXT_INSTR();
LABEL_NOT:
            memory[SP - 1] = (word)(memory[SP - 1] ? 0 : 1);
            NEXT_INSTR();
LABEL_INC:
            memory[SP - 1]++;
            NEXT_INSTR();
LABEL_DEC:
            memory[SP - 1]--;
            NEXT_INSTR();
LABEL_INC16:
            offset = SP - ADDRESS_SIZE;
            write16(memory, offset, (addr)(read16(memory, offset) + 1));
            NEXT_INSTR();
LABEL_DEC16:
            offset = SP - ADDRESS_SIZE;
            write16(memory, offset, (addr)(read16(memory, offset) - 1));
            NEXT_INSTR();
LABEL_EXTEND:
            PUSH_ADDR(POP());
            NEXT_INSTR();
LABEL_DOWNCAST:
            address = POP_ADDR();
            PUSH(address <= 255 ? (word)address : 255);
            NEXT_INSTR();
LABEL_JMP:
            address = read_addr_from_program(skip);
            IP = address;
            skip = 0;
            NEXT_INSTR();
LABEL_JMP_REL:
            offset = read_offs_from_program(skip);
            IP += offset;
            skip = 0;
            NEXT_INSTR();
LABEL_JF:
            if (!POP())
            {
                IP = read16(memory, IP+1);
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            NEXT_INSTR();
LABEL_JF16:
            if (!POP_ADDR())
            {
                IP = read16(memory, IP+1);
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            NEXT_INSTR();
LABEL_JT:
            if (POP())
            {
                IP = read16(memory, IP+1);;
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            NEXT_INSTR();
LABEL_JT16:
            if (POP_ADDR())
            {
                IP = read16(memory, IP+1);;
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            NEXT_INSTR();
LABEL_JF_REL:
            offset = read_offs_from_program(skip);
            if (POP() == 0)
            {
                IP += offset;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_JT_REL:
            offset = read_offs_from_program(skip);
            if (POP() != 0)
            {
                IP += offset;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_JMP2:
            address = POP_ADDR();
            IP = address;
            skip = 0;
            NEXT_INSTR();
LABEL_JT2:
            address = POP_ADDR();
            if (POP())
            {
                IP = address;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_JF2:
            address = POP_ADDR();
            if (!POP())
            {
                IP = address;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_CASE:
            arg = read_next_program_byte(skip);
            address = read_addr_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            if (memory[SP - 1] == arg)
            {
                POP();
                IP = address;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_ELSE:
            POP();
            address = read_addr_from_program(skip);
            IP = address;
            skip = 0;
            NEXT_INSTR();
LABEL_CASE_REL:
            arg = read_next_program_byte(skip);
            offset = read_offs_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            if (memory[SP - 1] == arg)
            {
                POP();
                IP += offset + 1;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_ELSE_REL:
            POP();
            offset = read_offs_from_program(skip);
            IP += offset;
            skip = 0;
            NEXT_INSTR();
LABEL_LOAD_GLOBAL:
            address = POP_ADDR();
            POINTER = address;
            PUSH(memory[address]);
            NEXT_INSTR();
LABEL_STORE_GLOBAL:
            address = POP_ADDR();
            POINTER = address;;
            arg = POP();
            memory[address] = arg;
            NEXT_INSTR();
LABEL_STORE_GLOBAL2:
            arg = POP();
            address = POP_ADDR();
            POINTER = address;;
            memory[address] = arg;
            NEXT_INSTR();
LABEL_LOAD_GLOBAL16:
            address = POP_ADDR();
            POINTER = address;;
            PUSH_ADDR(read16(memory, address));
            NEXT_INSTR();
LABEL_STORE_GLOBAL16:
            address = POP_ADDR();
            POINTER = address;;
            val = POP_ADDR();
            write16(memory, address, val);
            NEXT_INSTR();
LABEL_STORE_GLOBAL216:
            val = POP_ADDR();
            address = POP_ADDR();
            POINTER = address;;
            write16(memory, address, val);
            NEXT_INSTR();
LABEL_LOAD_LOCAL:
            arg = read_next_program_byte(skip);
            PUSH(memory[FP + arg]);
            NEXT_INSTR();
LABEL_LOAD_ARG:
            arg = read_next_program_byte(skip);
            PUSH(memory[FP - arg - 2 * ADDRESS_SIZE]);
            NEXT_INSTR();
LABEL_LOAD_LOCAL16:
            arg = read_next_program_byte(skip);
            PUSH_ADDR(read16(memory, FP + arg));
            NEXT_INSTR();
LABEL_LOAD_ARG16:
            arg = read_next_program_byte(skip);
            PUSH_ADDR(read16(memory, FP - arg - 2 * ADDRESS_SIZE));
            NEXT_INSTR();
LABEL_STORE_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] = POP();
            NEXT_INSTR();
LABEL_STORE_ARG:
            arg = read_next_program_byte(skip);
            memory[FP - arg - 2 * ADDRESS_SIZE] = POP();
            NEXT_INSTR();
LABEL_STORE_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, POP_ADDR());
            NEXT_INSTR();
LABEL_STORE_ARG16:
            arg = read_next_program_byte(skip);
            write16(memory, FP - arg - 2 * ADDRESS_SIZE, POP_ADDR());
            NEXT_INSTR();
LABEL_STORE_LOCAL_KEEP:
            arg = read_next_program_byte(skip);
            memory[FP + arg] = memory[SP - 1];
            NEXT_INSTR();
LABEL_STORE_LOCAL_KEEP16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, read16(memory, SP - ADDRESS_SIZE));
            NEXT_INSTR();
LABEL_LOAD_NVRAM:
            address = POP_ADDR();
            if (!nvram.is_open())
                OpenNvramFile();
            nvram.seekg(address);
            nvram.read(reinterpret_cast<char*>(&arg), 1);
            PUSH(arg);
            NEXT_INSTR();
LABEL_STORE_NVRAM:
            address = POP_ADDR();
            arg = POP();
            if (!nvram.is_open())
                OpenNvramFile();
            nvram.seekg(address);
            nvram.put(arg);
            NEXT_INSTR();
LABEL_CALL:
LABEL_CALL2:
LABEL_CALL_REL:
            if (instr == I::CALL_REL)
            {
                offset = read_offs_from_program(skip);
                address = (addr)(IP + offset);
            }
            else
            {
                address = instr == I::CALL ? read_addr_from_program(skip) : POP_ADDR();
            }
            CALL(address);
            skip = 0;
            NEXT_INSTR();
LABEL_RET:
            SP = FP;
            FP = POP_ADDR();
            address = POP_ADDR();
            IP = (addr)(address + ADDRESS_SIZE + 1); // skip address of call and go to next instruction
            skip = 0;
            NEXT_INSTR();
LABEL_SWAP:
            tmp = memory[SP - 1];
            memory[SP - 1] = memory[SP - 2];
            memory[SP - 2] = tmp;
            NEXT_INSTR();
LABEL_SWAP16:
            val = read16(memory, SP - ADDRESS_SIZE * 2);
            write16(memory, SP - ADDRESS_SIZE * 2, read16(memory, SP - ADDRESS_SIZE));
            write16(memory, SP - ADDRESS_SIZE, val);
            NEXT_INSTR();
LABEL_DUP:
            PUSH(memory[SP - 1]);
            NEXT_INSTR();
LABEL_DUP16:
            PUSH_ADDR(read16(memory, SP - ADDRESS_SIZE));
            NEXT_INSTR();
LABEL_ROLL3:
            {
                auto a = POP();
                auto b = POP();
                auto c = POP();
                PUSH(a);
                PUSH(c);
                PUSH(b);
            }
            NEXT_INSTR();
LABEL_NEG:
            PUSHI(-POP());
            NEXT_INSTR();
LABEL_NOP:
            NEXT_INSTR();
LABEL_DEBUGGER:
#ifdef _WIN32
            DebugBreak();
#endif
            NEXT_INSTR();
LABEL_INTERRUPT_HANDLER:
            arg = read_next_program_byte(skip);
            address = read_addr_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            if (address > 0)
                handlers[(InterruptCodes)arg] = address;
            else
                if (handlers.count((InterruptCodes)arg))
                {
                    handlers.erase((InterruptCodes)arg);
                }
            NEXT_INSTR();
LABEL_SYSCALL:
LABEL_SYSCALL2:
            arg = instr == I::SYSCALL ? read_next_program_byte(skip) : POP();
            {
                auto result = STDLIB(arg);
                if (result != InterruptCodes::NoError)
                {
                    HANDLE_EXCEPTION(result);
                }
            }
            NEXT_INSTR();
LABEL_HALT:
            if (nvram.is_open())
            {
                nvram.close();
            }
#ifdef WITH_PROFILER
            goto end;
#else
            return; // end of program
#endif
LABEL_MACRO_POP_EXT_X2_ADD16:
            PUSH_ADDR(POP() * 2 + POP_ADDR());
            NEXT_INSTR();
LABEL_MACRO_POP_EXT_X2_ADD16_LG16:
            address = POP() * 2 + POP_ADDR();
            POINTER = address;;
            PUSH_ADDR(read16(memory, address));
            NEXT_INSTR();
LABEL_MACRO_ADD8_TO_16:
LABEL_MACRO_ADD16_TO_8:
            address = instr == I::MACRO_ADD8_TO_16 ?  POP() + POP_ADDR() : POP_ADDR() + POP();
            if (memory[IP + 1] == I::LOAD_GLOBAL)
            {
                POINTER = address;
                PUSH(memory[address]);
                skip++;
            }
            else if (memory[IP + 1] == I::STORE_GLOBAL)
            {
                POINTER = address;
                memory[address] = POP();
                skip++;
            }
            else
                PUSH_ADDR(address);
                NEXT_INSTR();
LABEL_MACRO_ANDX:
            PUSH_ADDR(POP() & POP());
            NEXT_INSTR();
LABEL_MACRO_ORX:
            PUSH_ADDR(POP() | POP());
            NEXT_INSTR();
LABEL_MACRO_LSH16_BY8:
            {
                auto tmp1 = POP();
                auto tmp2 = POP_ADDR();
                signedResult = tmp2 << tmp1;
                PUSHI_ADDR(signedResult);
            }
            NEXT_INSTR();
LABEL_MACRO_INC_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] += 1;
            NEXT_INSTR();
LABEL_MACRO_DEC_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] -= 1;
            NEXT_INSTR();
LABEL_MACRO_INC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, read16(memory, FP + arg) + 1);
            NEXT_INSTR();
LABEL_MACRO_DEC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, read16(memory, FP + arg) - 1);
            NEXT_INSTR();
LABEL_MACRO_X2:
            OP_WITH_CONST(<< , 1);
            NEXT_INSTR();
LABEL_MACRO_X216:
            OP_WITH_CONST_16(<< , 1);
            NEXT_INSTR();
LABEL_MACRO_DIV2:
            OP_WITH_CONST(>> , 1);
            NEXT_INSTR();
LABEL_MACRO_X3:
            OP_WITH_CONST(* , 3);
            NEXT_INSTR();
LABEL_MACRO_DIV3:
            OP_WITH_CONST(/ , 3);
            NEXT_INSTR();
LABEL_GET_PTR:
            PUSH_ADDR(POINTER);
            NEXT_INSTR();
LABEL_LOAD_GLOBAL_PTR:
            address = POINTER;
            PUSH(memory[address]);
            NEXT_INSTR();
LABEL_STORE_GLOBAL_PTR:
            address = POINTER;
            arg = POP();
            memory[address] = arg;
            NEXT_INSTR();
LABEL_LOAD_GLOBAL_PTR16:
            address = POINTER;
            PUSH_ADDR(read16(memory, address));
            NEXT_INSTR();
LABEL_STORE_GLOBAL_PTR16:
            address = POINTER;
            val = POP_ADDR();
            write16(memory, address, val);
            NEXT_INSTR();
LABEL_MACRO_CONDITIONAL_JF:
            arg = read_next_program_byte(skip);
            address = read_addr_from_program(skip, 2);
            switch (arg)
            {
            case 0: // EQ
                signedResult = POP() == POP();
                break;
            case 1: // NE
                signedResult = POP() != POP();
                break;
            case 2: // LESS
                signedResult = POP() < POP();
                break;
            case 3: // LESS_OR_EQ
                signedResult = POP() <= POP();
                break;
            case 4: // GREATER
                signedResult = POP() > POP();
                break;
            case 5: // GREATER_OR_EQ
                signedResult = POP() >= POP();
                break;
            case 6: // ZERO
                signedResult = POP() == 0;
                break;
            case 7: // NZERO
                signedResult = POP() != 0;
                break;
            default:
                std::cerr << "Unknown conditional argument: " << std::to_string(arg) << std::endl;
                throw std::runtime_error("Unknown conditional argument: " + std::to_string(arg));
            }
            if (!signedResult)
            {
                IP = address;
                skip = 0;
            }
            NEXT_INSTR();
LABEL_MACRO_SET_LOCAL:
            arg = read_next_program_byte(skip);
            tmp = memory[IP + 2];
            skip = 3;
            memory[FP + arg] = tmp;
            NEXT_INSTR();
LABEL_MACRO_SET_LOCAL16:
            arg = read_next_program_byte(skip);
            address = read16(memory, IP + 2);
            skip = 4;
            write16(memory, FP + arg, address);
            NEXT_INSTR();

        // Add more labels as needed for your enum
        // End of computed goto block
#endif // _MSC_VER

#ifdef WITH_PROFILER
    end :
    if (profile)
    {
        // Sort counters by value (descending)
        std::map<I, long long> counterMaps;
        for (int i = 0; i < 256; i++)
        {
            if (counters[i] == 0) continue;
            counterMaps[(I)i] = counters[i];
        }
        std::vector<std::pair<I, long long>> sortedCounters(counterMaps.begin(), counterMaps.end());
        std::sort(sortedCounters.begin(), sortedCounters.end(),
            [](const auto& a, const auto& b) { return a.second > b.second; });

        // Print sorted counters
        for (const auto& [instr, count] : sortedCounters)
        {
            std::cout << magic_enum::enum_name(instr) << ": " << count << std::endl;
        }
        std::cout << "Max stack pointer: " << max_sp << std::endl;
    }
#endif
}

void VM::WriteStringToMemory(const std::string& str, int addr, int maxLen)
{
    auto len = std::min(maxLen - 1, (int)str.length());
    for (int i = 0; i < len; i++)
        memory[addr + i] = (word)str[i];
    memory[addr + len] = 0;
}

std::string VM::ReadStringFromMemory(int addr)
{
    return std::string(reinterpret_cast<const char*>(memory + addr));
}

InterruptCodes VM::STDLIB(int callNumber)
{
    word arg, maxLen, len, arg2;
    addr address, srcAddress, targetAddress;
    int result;
    std::string input;

    switch ((Stdlib)callNumber)
    {
    case Stdlib::PrintInt:
        
        std::cout << (int)memory[SP - 1];
        break;
    case Stdlib::PrintInt16:
        
        std::cout << (int)read16(memory, SP - ADDRESS_SIZE);
        break;
    case Stdlib::PrintNewLine:
        std::cout << std::endl;
        break;

    case Stdlib::PrintChar:
        
        std::cout << (char)memory[SP - 1];
        break;
    case Stdlib::PrintCharPop:
        std::cout << (char)POP();
        break;
    case Stdlib::PrintString:
        address = POP_ADDR();
        do
        {
            arg = memory[address++];
            if (!arg) break;
            std::cout << (char)arg;
        } while (arg != 0);
        break;

    case Stdlib::ReadString:
        maxLen = POP();
        address = POP_ADDR();
        std::cin >> input;
        WriteStringToMemory(input.c_str(), address, maxLen);
        break;
    case Stdlib::ReadKey:
#ifdef _WIN32
        if (_kbhit())
        {
            result = _getch();
            if (result != EOF)
            {
                PUSHI(result);
            }
        }
        else PUSH(0);
#else
        if (kbhit())
        {
            result = getchar2();
            if (result != EOF)
            {
                PUSHI(result);
            }
        }
        else PUSH(0);
#endif
        break;

    case Stdlib::SetConsoleCursorPosition:
        arg = POP() + 1; // top
        arg2 = POP() + 1; // left
        std::cout << std::string("\x1b[") + std::to_string(arg) + ";" + std::to_string(arg2) + "H";
        break;
    case Stdlib::ShowConsoleCursor:
        arg = POP();
        if (arg)
            std::cout << "\x1b[?25h";
        else
            std::cout << "\x1b[?25l";
        break;
    case Stdlib::SetConsoleColors:
        arg = POP(); // fg
        arg2 = POP(); // bg
        std::cout << std::string("\x1b[") + std::to_string(BgColorToVT100((Colors)arg2)) + ";" + std::to_string(FgColorToVT100((Colors)arg)) + "m";
        break;

    case Stdlib::ConsoleClear:
        std::cout << "\x1b[2J";
        break;
    case Stdlib::StringToInt:
        address = POP_ADDR();
        input = ReadStringFromMemory(address);
        try
        {
            result = std::stoi(input);
            PUSH(result);
        }
        catch (...)
        {
            return InterruptCodes::ParseError;
        }
        break;
    case Stdlib::IntToString:
        arg = POP();
        maxLen = POP();
        address = POP_ADDR();
        WriteStringToMemory(std::to_string(arg), address, maxLen);
        break;
    case Stdlib::MemCpy:
        maxLen = POP();
        targetAddress = POP_ADDR();
        srcAddress = POP_ADDR();
        for (int i = 0; i < maxLen; i++)
            memory[targetAddress + i] = memory[srcAddress + i];
        break;
    case Stdlib::MemSet:
        arg = POP();
        SP = POP_ADDR(); // not sp value, simply reuse variable
        address = POP_ADDR();
        for (int i = 0; i < SP; i++)
        {
            memory[address + i] = arg;
        }
        break;
    case Stdlib::MemSwap:
        len = POP();
        targetAddress = POP_ADDR();
        srcAddress = POP_ADDR();
        word tmp;
        for (int i = 0; i < len; i++)
        {
            tmp = memory[targetAddress + i];
            memory[targetAddress + i] = memory[srcAddress + i];
            memory[srcAddress + i] = tmp;
        }
        break;
    case Stdlib::MemCmp:
        len = POP();
        targetAddress = POP_ADDR();
        srcAddress = POP_ADDR();
        result = 0;
        for (int i = 0; i < len; i++)
        {
            auto a = memory[targetAddress + i];
            auto b = memory[srcAddress + i];
            if (a != b)
            {
                result = srcAddress + i; break;
            }
        }
        PUSHI(result);
        break;

    case Stdlib::Strlen:
        address = POP_ADDR();
        result = 0;
        do
        {
            arg = memory[address + result++];
        } while (arg != 0);
        result--;
        PUSHI_ADDR(result);
        break;
    case Stdlib::Sleep:
        address = POP_ADDR(); // not really an address :)
        std::cout << std::flush; // especially needed for Linux
        std::this_thread::sleep_for(std::chrono::milliseconds(address));
        break;
    case Stdlib::GetRandomNumber:
    {
        arg = POP(); // max
        arg2 = POP(); // min
        std::uniform_int_distribution<int> dist(arg2, arg);
        PUSHI(dist(mt));
        break;
    }
    default:
        throw std::runtime_error("Syscall not implemented: " + std::to_string(callNumber));
    }

    return InterruptCodes::NoError;
}

void VM::Free()
{
    if (memory != nullptr)
    {
        delete memory;
        memory = nullptr;
    }
}

bool file_exists(const std::string& fileName)
{
    std::ifstream infile(fileName);
    return infile.good();
}

void VM::OpenNvramFile()
{
    if (!file_exists(nvram_file))
    {
        char c = 0;
        nvram.open(nvram_file, std::ios::out);
        for (int i = 0; i < 65535; i++)
            nvram.write(&c, 1);
        nvram.flush();
        nvram.close();
    }
    nvram.open(nvram_file, std::fstream::in | std::fstream::out | std::fstream::binary);
}

#ifndef _WIN32
// https://stackoverflow.com/questions/29335758/using-kbhit-and-getch-on-linux
bool VM::kbhit()
{
    disableEcho(); // todo: dirty solution
    termios term;
    tcgetattr(0, &term);
    termios term2 = term;
    term2.c_lflag &= ~ICANON;
    tcsetattr(0, TCSANOW, &term2);
    int byteswaiting;
    ioctl(0, FIONREAD, &byteswaiting);
    tcsetattr(0, TCSANOW, &term);
    return byteswaiting > 0;
}
char VM::getchar2()
{
    char c;
    termios term;
    tcgetattr(0, &term);
    termios term2 = term;
    term2.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(0, TCSANOW, &term2);
    c = getchar();
    tcsetattr(0, TCSANOW, &term);
    return c;
}
void VM::disableEcho()
{
    termios term;
    tcgetattr(0, &term);
    termios term2 = term;
    term2.c_lflag &= ~ECHO;
    tcsetattr(0, TCSANOW, &term2);
}
#endif

/*
*     Black,
    Red,
    Green,
    Yellow,
    Blue,
    Magenta,
    Cyan,
    White,
    BrightBlack,
    BrightRed,
    BrightGreen,
    BrightYellow,
    BrightBlue,
    BrightMagenta,
    BrightCyan,
    BrightWhite,
    Gray,
    BrightGray
*/

int VM::FgColorToVT100(Colors color)
{
    switch (color)
    {
    case Colors::Black:
        return 30;
    case Colors::Red:
        return 31;
    case Colors::Green:
        return 32;
    case Colors::Yellow:
        return 33;
    case Colors::Blue:
        return 34;
    case Colors::Magenta:
        return 35;
    case Colors::Cyan:
        return 36;
    case Colors::White:
        return 37;
    case Colors::BrightBlack:
        return 90;
    case Colors::BrightRed:
        return 91;
    case Colors::BrightGreen:
        return 92;
    case Colors::BrightYellow:
        return 93;
    case Colors::BrightBlue:
        return 94;
    case Colors::BrightMagenta:
        return 95;
    case Colors::BrightCyan:
        return 96;
    case Colors::BrightWhite:
        return 97;
    case Colors::Gray:
    case Colors::BrightGray:
        return 37; // unsupported - use dark white
    default:
        return 37;
    }
}
int VM::BgColorToVT100(Colors color)
{
    switch (color)
    {
    case Colors::Black:
        return 40;
    case Colors::Red:
        return 41;
    case Colors::Green:
        return 42;
    case Colors::Yellow:
        return 43;
    case Colors::Blue:
        return 44;
    case Colors::Magenta:
        return 45;
    case Colors::Cyan:
        return 46;
    case Colors::White:
        return 47;
    case Colors::BrightBlack:
        return 90;
    case Colors::BrightRed:
        return 101;
    case Colors::BrightGreen:
        return 102;
    case Colors::BrightYellow:
        return 103;
    case Colors::BrightBlue:
        return 104;
    case Colors::BrightMagenta:
        return 105;
    case Colors::BrightCyan:
        return 106;
    case Colors::BrightWhite:
        return 107;
    case Colors::Gray:
    case Colors::BrightGray:
        return 47; // unsupported - use dark white
    default:
        return 37;
    }
}