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


#define PUSH(arg) { memory[SP++] = arg;}

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
    addr sp_value;
    int offset;
    addr val;
    word tmp;
    int signedResult;
#ifdef _MSC_VER
	int direction; // for MSVC
#endif

#ifdef WITH_PROFILER

    std::map<I, long> counters;
    addr max_sp = 0;
#endif

    while (true)
    {
        instr = (I)memory[IP];
#ifdef WITH_PROFILER
        if (profile)
        {
            if (SP > max_sp)
                max_sp = SP;
            if (counters.count(instr))
                counters[instr]++;
            else
                counters[instr] = 1;
        }
#endif

        skip = WORD_SIZE;

        switch (instr)
        {
        case I::PUSH:
            arg = read_next_program_byte(skip);
            PUSH(arg);
            break;
        case I::PUSH16:
            address = read_addr_from_program(skip);
            PUSH_ADDR(address);
            break;
        case I::PUSH16_REL:
            offset = read_offs_from_program(skip);
            address = (addr)(IP + offset);
            PUSH_ADDR(address);
            break;
        case I::PUSHN:
            arg = read_next_program_byte(skip);
            SP += arg;
            break;
        case I::PUSHN2:
            SP += POP();
            break;
        case I::PUSH_NEXT_SP:
            sp_value = SP;
            PUSHI_ADDR(sp_value + ADDRESS_SIZE);
            break;
        case I::PUSH_STACK_START:
            PUSH_ADDR(stackStartPos);
            break;
            break;
        case I::POP:
            POP();
            break;
        case I::POPN:
            arg = read_next_program_byte(skip);
            SP -= arg;
            break;
        case I::POPN2:
            SP -= POP();
            break;
        case I::PUSH_REG:
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
            break;
        case I::POP_REG:
            arg = read_next_program_byte(skip);
            if (arg == 0)
                IP = POP_ADDR();
            else if (arg == 1)
                SP = POP_ADDR();
            else if (arg == 2)
                FP = POP_ADDR();
            break;
        case I::ADD:
            BIN_OP(+);
            break;
        case I::ADD16:
            BIN_OP_16(+);
            break;
        case I::ADD16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(+, address);
            break;
        case I::SUB16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(-, address);
            break;
        case I::ADDC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(+, address);
            break;
        case I::SUBC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(-, address);
            break;
        case I::MULC:
            address = read_next_program_byte(skip);
            OP_WITH_CONST(*, address);
            break;
        case I::SUB:
            BIN_OP(-);
            break;
        case I::SUB2:
            BIN_OP_INV(-);
            break;
        case I::SUB16:
            BIN_OP_16(-);
            break;
        case I::SUB216:
        {
            BIN_OP_16_INV(-);
        }
        break;
        case I::DIV:
            if (memory[SP-2] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP(/)
            break;
        case I::DIV2:
            if (memory[SP-1] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP_INV(/)
            break;
        case I::DIV216:
        {
            auto tmp1 = POP_ADDR();
            auto tmp2 = POP_ADDR();
            if (tmp1 == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            PUSHI(tmp2 / tmp1);
            break;
        }
        case I::MOD:
            if (memory[SP - 2] == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            BIN_OP(%)
            break;
        case I::MOD16:
            address = POP_ADDR();
            val = POP_ADDR();
            if (val == 0)
            {
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            }
            PUSHI_ADDR(address % val);
            break;
        case I::MUL:
            BIN_OP(*);
            break;
        case I::MUL16:
            BIN_OP_16(*);
            break;
        case I::MUL16C:
            address = read_addr_from_program(skip);
            OP_WITH_CONST_16(*, address);
            break;

        case I::EQ:
            LOGICAL_OP(==);
            break;
        case I::NE:
            LOGICAL_OP(!=);
            break;
        case I::LESS:
            LOGICAL_OP(<);
            break;
        case I::LESS_OR_EQ:
            LOGICAL_OP(<=);
            break;
        case I::GREATER:
            LOGICAL_OP(>);
            break;
        case I::GREATER_OR_EQ:
            LOGICAL_OP(>=);
            break;
        case I::ZERO:
            sp_value = SP;
            memory[sp_value - 1] = (word)(memory[sp_value - 1] == 0 ? 1 : 0);
            break;
        case I::NZERO:
            sp_value = SP;
            memory[sp_value - 1] = (word)(memory[sp_value - 1] != 0 ? 1 : 0);
            break;

        case I::EQ16:
            LOGICAL_OP_16(==);
            break;
        case I::NE16:
            LOGICAL_OP_16(!=);
            break;
        case I::LESS16:
            LOGICAL_OP_16(<);
            break;
        case I::LESS_OR_EQ16:
            LOGICAL_OP_16(<=);
            break;
        case I::GREATER16:
            LOGICAL_OP_16(>);
            break;
        case I::GREATER_OR_EQ16:
            LOGICAL_OP_16(>=);
            break;
        case I::ZERO16:
            PUSHI(POP_ADDR() == 0 ? 1 : 0);
            break;
        case I::NZERO16:
            PUSHI(POP_ADDR() != 0 ? 1 : 0);
            break;

        case I::AND:
            BIN_OP(&);
            break;
        case I::OR:
            BIN_OP(|);
            break;
        case I::LAND:
            PUSHI((POP() != 0) && (POP() != 0) ? 1 : 0);
            break;
        case I::LOR:
            PUSHI((POP() != 0) || (POP() != 0) ? 1 : 0);
            break;
        case I::XOR:
            BIN_OP(^);
            break;
        case I::LSH:
        {
            BIN_OP_INV(<<);
            break;
        }
        case I::RSH:
        {
            BIN_OP_INV(>>);
            break;
        }
        case I::FLIP:
            PUSHI(~POP());
            break;


        case I::AND16:
            BIN_OP_16(&);
            break;
        case I::OR16:
            BIN_OP_16(|);
            break;
        case I::XOR16:
            BIN_OP_16(^);
            break;
        case I::LSH16:
        {
            BIN_OP_16_INV(<< );
            break;
        }
        case I::RSH16:
        {
            BIN_OP_16_INV(>>);
            break;
        }
        case I::FLIP16:
            PUSHI_ADDR(~POP_ADDR());
            break;

        case I::NOT:
            sp_value = SP;
            memory[sp_value - 1] = (word)(memory[sp_value - 1] ? 0 : 1);
            break;
        case I::INC:
            sp_value = SP;
            memory[sp_value - 1]++;
            break;
        case I::DEC:
            sp_value = SP;
            memory[sp_value - 1]--;
            break;
        case I::INC16:
            offset = SP - ADDRESS_SIZE;
            write16(memory, offset, (addr)(read16(memory, offset) + 1));
            break;
        case I::DEC16:
            offset = SP - ADDRESS_SIZE;
            write16(memory, offset, (addr)(read16(memory, offset) - 1));
            break;
        case I::EXTEND:
            PUSH_ADDR(POP());
            break;
        case I::DOWNCAST:
        {
            address = POP_ADDR();
            PUSH(address <= 255 ? (word)address : 255);
            break;
        }
        case I::JMP:
            address = read_addr_from_program(skip);
            IP = address;
            skip = 0;
            break;
        case I::JMP_REL:
            offset = read_offs_from_program(skip);
            IP += offset;
            skip = 0;
            break;
        case I::JF:
            if (!POP())
            {
                IP = read16(memory, IP+1);
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            break;
        case I::JF16:
            if (!POP_ADDR())
            {
                IP = read16(memory, IP+1);
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            break;
        case I::JT:
            if (POP())
            {
                IP = read16(memory, IP+1);;
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            break;
        case I::JT16:
            if (POP_ADDR())
            {
                IP = read16(memory, IP+1);;
                skip = 0;
            }
            else
                skip += ADDRESS_SIZE;
            break;
        case I::JF_REL:
            offset = read_offs_from_program(skip);
            if (POP() == 0)
            {
                IP += offset;
                skip = 0;
            }
            break;
        case I::JT_REL:
            offset = read_offs_from_program(skip);
            if (POP() != 0)
            {
                IP += offset;
                skip = 0;
            }
            break;
        case I::JMP2:
            address = POP_ADDR();
            IP = address;
            skip = 0;
            break;
        case I::JT2:
            address = POP_ADDR();
            if (POP())
            {
                IP = address;
                skip = 0;
            }
            break;
        case I::JF2:
            address = POP_ADDR();
            if (!POP())
            {
                IP = address;
                skip = 0;
            }
            break;
        case I::CASE:
            arg = read_next_program_byte(skip);
            address = read_addr_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            sp_value = SP;
            if (memory[sp_value - 1] == arg)
            {
                POP();
                IP = address;
                skip = 0;
            }
            break;
        case I::ELSE:
            POP();
            address = read_addr_from_program(skip);
            IP = address;
            skip = 0;
            break;
        case I::CASE_REL:
            arg = read_next_program_byte(skip);
            offset = read_offs_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            sp_value = SP;
            if (memory[sp_value - 1] == arg)
            {
                POP();
                IP += offset + 1;
                skip = 0;
            }
            break;
        case I::ELSE_REL:
            POP();
            offset = read_offs_from_program(skip);
            IP += offset;
            skip = 0;
            break;
        case I::LOAD_GLOBAL:
            address = POP_ADDR();
            POINTER = address;
            PUSH(memory[address]);
            break;
        case I::STORE_GLOBAL:
            address = POP_ADDR();
            POINTER = address;;
            arg = POP();
            memory[address] = arg;
            break;
        case I::STORE_GLOBAL2:
            arg = POP();
            address = POP_ADDR();
            POINTER = address;;
            memory[address] = arg;
            break;
        case I::LOAD_GLOBAL16:
            address = POP_ADDR();
            POINTER = address;;
            PUSH_ADDR(read16(memory, address));
            break;
        case I::STORE_GLOBAL16:
            address = POP_ADDR();
            POINTER = address;;
            val = POP_ADDR();
            write16(memory, address, val);
            break;
        case I::STORE_GLOBAL216:
            val = POP_ADDR();
            address = POP_ADDR();
            POINTER = address;;
            write16(memory, address, val);
            break;
#ifdef _MSC_VER
		// merged cases optimize better for MSVC
        case I::LOAD_LOCAL:
        case I::LOAD_ARG:
        case I::LOAD_LOCAL16:
        case I::LOAD_ARG16:
            arg = read_next_program_byte(skip);
            direction = (instr == I::LOAD_ARG || instr == I::LOAD_ARG16) ? -1 : 1;
            offset = (instr == I::LOAD_ARG || instr == I::LOAD_ARG16) ? 2 * ADDRESS_SIZE : 0;
            if (instr == I::LOAD_LOCAL16 || instr == I::LOAD_ARG16)
            {
                PUSH_ADDR(read16(memory, FP + (arg + offset) * direction));
            }
            else
                PUSH(memory[FP + (arg + offset) * direction]);
            break;
        case I::STORE_LOCAL:
        case I::STORE_ARG:
        case I::STORE_LOCAL16:
        case I::STORE_ARG16:
            arg = read_next_program_byte(skip);
            direction = (instr == I::STORE_ARG || instr == I::STORE_ARG16) ? -1 : 1;
            offset = (instr == I::STORE_ARG || instr == I::STORE_ARG16) ? 2 * ADDRESS_SIZE : 0;
            if (instr == I::STORE_LOCAL16 || instr == I::STORE_ARG16)
                write16(memory, FP + (arg + offset) * direction, POP_ADDR());
            else
                memory[FP + (arg + offset) * direction] = POP();
            break;
#else
			// Separate cases for better performance on GCC/Clang
        case I::LOAD_LOCAL:
            arg = read_next_program_byte(skip);
            PUSH(memory[FP + arg]);
            break;
        case I::LOAD_ARG:
            arg = read_next_program_byte(skip);
            PUSH(memory[FP - arg - 2 * ADDRESS_SIZE]);
            break;
        case I::LOAD_LOCAL16:
            arg = read_next_program_byte(skip);
            PUSH_ADDR(read16(memory, FP + arg));
            break;
        case I::LOAD_ARG16:
            arg = read_next_program_byte(skip);
            PUSH_ADDR(read16(memory, FP - arg - 2 * ADDRESS_SIZE));
            break;
        case I::STORE_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] = POP();
            break;
        case I::STORE_ARG:
            arg = read_next_program_byte(skip);
            memory[FP - arg - 2 * ADDRESS_SIZE] = POP();
            break;
        case I::STORE_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, POP_ADDR());
            break;
        case I::STORE_ARG16:
            arg = read_next_program_byte(skip);
            write16(memory, FP - arg - 2 * ADDRESS_SIZE, POP_ADDR());
            break;
#endif
        case I::LOAD_NVRAM:
            address = POP_ADDR();
            if (!nvram.is_open())
                OpenNvramFile();
            nvram.seekg(address);
            nvram.read(reinterpret_cast<char*>(&arg), 1);
            PUSH(arg);
            break;
        case I::STORE_NVRAM:
            address = POP_ADDR();
            arg = POP();
            if (!nvram.is_open())
                OpenNvramFile();
            nvram.seekg(address);
            nvram.put(arg);
            break;
        case I::CALL:
        case I::CALL2:
        case I::CALL_REL:
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
            break;
        case I::RET:
            SP = FP;
            FP = POP_ADDR();
            address = POP_ADDR();
            IP = (addr)(address + ADDRESS_SIZE + 1); // skip address of call and go to next instruction
            skip = 0;
            break;
        case I::SWAP:
            sp_value = SP;
            tmp = memory[sp_value - 1];
            memory[sp_value - 1] = memory[sp_value - 2];
            memory[sp_value - 2] = tmp;
            break;
        case I::SWAP16:
            sp_value = SP;
            val = read16(memory, sp_value - ADDRESS_SIZE * 2);
            write16(memory, sp_value - ADDRESS_SIZE * 2, read16(memory, sp_value - ADDRESS_SIZE));
            write16(memory, sp_value - ADDRESS_SIZE, val);
            break;
        case I::DUP:
            sp_value = SP;
            PUSH(memory[sp_value - 1]);
            break;
        case I::DUP16:
            sp_value = SP;
            PUSH_ADDR(read16(memory, sp_value - ADDRESS_SIZE));
            break;
        case I::ROLL3:
        {
            auto a = POP();
            auto b = POP();
            auto c = POP();
            PUSH(a);
            PUSH(c);
            PUSH(b);
        }
        break;
        case I::NEG:
            PUSHI(-POP());
            break;
        case I::NOP:
            break;
        case I::DEBUGGER:
#ifdef _WIN32
            DebugBreak();
#endif
            break;
        case I::INTERRUPT_HANDLER:
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
            break;
        case I::SYSCALL:
        case I::SYSCALL2:
            arg = instr == I::SYSCALL ? read_next_program_byte(skip) : POP();
            {
                auto result = STDLIB(arg);
                if (result != InterruptCodes::NoError)
                {
                    HANDLE_EXCEPTION(result);
                }
            }
            break;
        case I::HALT:

            if (nvram.is_open())
            {
                nvram.close();
            }
#ifdef WITH_PROFILER
            goto end;
#else
            return; // end of program
#endif
        case I::MACRO_POP_EXT_X2_ADD16:
        {
            address = POP() * 2; // extends to addr
            addr a2 = POP_ADDR();
            PUSH_ADDR(address + a2);
        }
        break;
        case I::MACRO_POP_EXT_X2_ADD16_LG16:
        {
            address = POP() * 2; // extends to addr
            addr a2 = POP_ADDR();
            address += a2;
            POINTER = address;;
            PUSH_ADDR(read16(memory, address));
        }
        break;
        case I::MACRO_ADD8_TO_16:
        {
            address = POP(); // extends to addr
            addr a2 = POP_ADDR();
            PUSH_ADDR(address + a2);
        }
        break;
        case I::MACRO_ANDX:
            PUSH_ADDR(POP() & POP());
            break;
        case I::MACRO_ORX:
            PUSH_ADDR(POP() | POP());
            break;
        case I::MACRO_LSH16_BY8:
        {
            auto tmp1 = POP();
            auto tmp2 = POP_ADDR();
            signedResult = tmp2 << tmp1;
            PUSHI_ADDR(signedResult);
            break;
        }
        case I::MACRO_INC_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] += 1;
            break;
        case I::MACRO_DEC_LOCAL:
            arg = read_next_program_byte(skip);
            memory[FP + arg] -= 1;
            break;
        case I::MACRO_INC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, read16(memory, FP + arg) + 1);
            break;
        case I::MACRO_DEC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, FP + arg, read16(memory, FP + arg) - 1);
            break;
        case I::MACRO_X2:
        {
			OP_WITH_CONST(<< , 1);
            break;
        }
        case I::MACRO_X216:
        {
			OP_WITH_CONST_16(<< , 1);
            break;
        }
        case I::MACRO_DIV2:
        {
            OP_WITH_CONST(>> , 1);
            break;
        }
        case I::MACRO_X3:
        {
            OP_WITH_CONST(* , 3);
            break;
        }
        case I::MACRO_DIV3:
        {
            OP_WITH_CONST(/ , 3);
            break;
        }
        case I::GET_PTR:
            PUSH_ADDR(POINTER);
            break;
        case I::LOAD_GLOBAL_PTR:
            address = POINTER;
            PUSH(memory[address]);
            break;
        case I::STORE_GLOBAL_PTR:
            address = POINTER;
            arg = POP();
            memory[address] = arg;
            break;
        case I::LOAD_GLOBAL_PTR16:
            address = POINTER;
            PUSH_ADDR(read16(memory, address));
            break;
        case I::STORE_GLOBAL_PTR16:
            address = POINTER;
            val = POP_ADDR();
            write16(memory, address, val);
            break;
        default:
            std::cerr << "Instruction not implemented: " << std::to_string(instr) << std::endl;
            throw std::runtime_error("Instruction not implemented: " + std::to_string(instr));
        }
        IP += skip;
    }



#ifdef WITH_PROFILER
    end :
    if (profile)
    {
        // Sort counters by value (descending)
        std::vector<std::pair<I, long>> sortedCounters(counters.begin(), counters.end());
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
    addr sp_value;
    int result;
    std::string input;

    switch ((Stdlib)callNumber)
    {
    case Stdlib::PrintInt:
        sp_value = SP;
        std::cout << (int)memory[sp_value - 1];
        break;
    case Stdlib::PrintInt16:
        sp_value = SP;
        std::cout << (int)read16(memory, sp_value - ADDRESS_SIZE);
        break;
    case Stdlib::PrintNewLine:
        std::cout << std::endl;
        break;

    case Stdlib::PrintChar:
        sp_value = SP;
        std::cout << (char)memory[sp_value - 1];
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
        sp_value = POP_ADDR(); // not sp value, simply reuse variable
        address = POP_ADDR();
        for (int i = 0; i < sp_value; i++)
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