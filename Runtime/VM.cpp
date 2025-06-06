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

VM::VM() : memory(nullptr), registers{ 0, 0, 0 }, mt(rd())
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
#define READ_REGISTER(r) registers[r]
#define WRITE_REGISTER(r, value) registers[r] = value
#define ADD_TO_REGISTER(r, value) registers[r] += value

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

void VM::LoadProgram(word* program, int program_length, int memory_size, const char* nvr_file)
{
    if (memory_size < program_length + 3) // plus registers
    {
        memory_size = program_length + 3;
    }
    Free();
    memory = new word[memory_size];

    WRITE_REGISTER(IP_REGISTER, PROGRAM_BEGIN);
    for (int i = 0; i < program_length; i++)
    {
        memory[i + PROGRAM_BEGIN] = program[i];
    }
    stackStartPos = (addr)(program_length + PROGRAM_BEGIN);
    WRITE_REGISTER(SP_REGISTER, stackStartPos);
    WRITE_REGISTER(FP_REGISTER, stackStartPos);
    //max_sp = READ_REGISTER(SP_REGISTER);
    handlers.clear();
    nvram_file = nvr_file;
}


inline offs VM::readoffs(word* list, int pos) { return list[pos + 1] * 256 + list[pos]; }


inline void VM::PUSH(word arg) { memory[registers[SP_REGISTER]] = arg; ADD_TO_REGISTER(SP_REGISTER, 1);}

inline void VM::PUSH_ADDR(addr arg) {write16(memory, registers[SP_REGISTER], arg); ADD_TO_REGISTER(SP_REGISTER, ADDRESS_SIZE);}

inline void VM::PUSHI(int arg) { PUSH((word)arg); }

inline void VM::PUSHI_ADDR(int arg) { PUSH_ADDR((addr)arg); };

inline word VM::POP() { auto v = memory[registers[SP_REGISTER] - 1]; ADD_TO_REGISTER(SP_REGISTER, -1); return v; }

inline addr VM::POP_ADDR() { auto v = read16(memory, registers[SP_REGISTER] - ADDRESS_SIZE); ADD_TO_REGISTER(SP_REGISTER, -ADDRESS_SIZE); return v; }

inline word VM::read_next_program_byte(word& skip, int offset)
{
    auto instr = READ_REGISTER(IP_REGISTER);
    auto targ = memory[instr + offset];
    skip += WORD_SIZE;
    return targ;
}

inline addr VM::read_addr_from_program(word& skip, int offset)
{
    auto instr = READ_REGISTER(IP_REGISTER);
    auto targ = read16(memory, instr + offset);
    skip += ADDRESS_SIZE;
    return targ;
}

inline offs VM::read_offs_from_program(word& skip, int offset)
{
    auto instr = READ_REGISTER(IP_REGISTER);
    auto targ = readoffs(memory, instr + offset);
    skip += ADDRESS_SIZE;
    return targ;
}

inline void VM::CALL(addr address, int offset)
{
    PUSHI_ADDR((READ_REGISTER(IP_REGISTER) + offset));
    PUSH_ADDR(READ_REGISTER(FP_REGISTER));
    WRITE_REGISTER(IP_REGISTER, address);
    WRITE_REGISTER(FP_REGISTER, READ_REGISTER(SP_REGISTER));
}

void VM::RunProgram(bool profile)
{
    word skip;
    I instr;
    word arg;
    addr address;
    addr sp_value;
    int direction;
    int offset;
    addr val;
    word tmp;
    int signedResult;

#ifdef WITH_PROFILER

    std::map<I, long> counters;
    addr max_sp = 0;
#endif

    while (true)
    {
        instr = (I)memory[READ_REGISTER(IP_REGISTER)];
#ifdef WITH_PROFILER
        if (profile)
        {
            if (READ_REGISTER(SP_REGISTER) > max_sp)
                max_sp = READ_REGISTER(SP_REGISTER);
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
            address = (addr)(READ_REGISTER(IP_REGISTER) + offset);
            PUSH_ADDR(address);
            break;
        case I::PUSHN:
            arg = read_next_program_byte(skip);
            ADD_TO_REGISTER(SP_REGISTER, arg);
            sp_value = READ_REGISTER(SP_REGISTER);
            //if (sp_value > max_sp) max_sp = sp_value;
            break;
        case I::PUSHN2:
            ADD_TO_REGISTER(SP_REGISTER, POP());
            sp_value = READ_REGISTER(SP_REGISTER);
            //if (sp_value > max_sp) max_sp = sp_value;
            break;
        case I::PUSH_NEXT_SP:
            sp_value = READ_REGISTER(SP_REGISTER);
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
            ADD_TO_REGISTER(SP_REGISTER, -arg);
            break;
        case I::POPN2:
            ADD_TO_REGISTER(SP_REGISTER, -POP());
            break;
        case I::PUSH_REG:
            arg = read_next_program_byte(skip);
            PUSHI_ADDR(READ_REGISTER(arg));
            break;
        case I::POP_REG:
            arg = read_next_program_byte(skip);
            WRITE_REGISTER(arg, POP_ADDR());
            break;
        case I::ADD:
            signedResult = POP() + POP();
            carry = signedResult > 255;
            PUSHI(signedResult);
            break;
        case I::ADD16:
            signedResult = POP_ADDR() + POP_ADDR();
            carry = signedResult > 65535;
            PUSHI_ADDR(signedResult);
            break;
        case I::ADD16C:
            address = read_addr_from_program(skip);
            signedResult = POP_ADDR() + address;
            carry = signedResult > 35535;
            PUSHI_ADDR(signedResult);
            break;
        case I::ADDC:
            address = read_next_program_byte(skip);
            signedResult = POP() + address;
            carry = signedResult > 255;
            PUSHI(signedResult);
            break;
        case I::MULC:
            address = read_next_program_byte(skip);
            signedResult = POP() * address;
            carry = signedResult > 255;
            PUSHI(signedResult);
            break;
        case I::SUB:
            signedResult = POP() - POP();
            carry = signedResult < 0;
            PUSHI(signedResult);
            break;
        case I::SUB2:
        {
            auto tmp1 = POP();
            auto tmp2 = POP();
            signedResult = tmp2 - tmp1;
            carry = signedResult < 0;
            PUSHI(signedResult);
        }
        break;
        case I::SUB16:
            signedResult = POP_ADDR() - POP_ADDR();
            carry = signedResult < 0;
            PUSHI_ADDR(signedResult);
            break;
        case I::SUB216:
        {
            auto tmp1 = POP_ADDR();
            auto tmp2 = POP_ADDR();
            signedResult = tmp2 - tmp1;
            carry = signedResult < 0;
            PUSHI_ADDR(signedResult);
        }
        break;
        case I::CARRY:
            PUSH(carry ? 1 : 0);
            break;
        case I::DIV:
            arg = POP();
            tmp = POP();
            if (tmp == 0)
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            PUSHI(arg / tmp);
            break;
        case I::DIV2:
            arg = POP();
            tmp = POP();
            if (arg == 0)
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            PUSHI(tmp / arg);
            break;
        case I::DIV216:
        {
            auto tmp1 = POP_ADDR();
            auto tmp2 = POP_ADDR();
            if (tmp1 == 0)
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            PUSHI(tmp2 / tmp1);
            break;
        }
        case I::MOD:
            arg = POP();
            tmp = POP();
            if (tmp == 0)
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            PUSHI((arg % tmp));
            break;
        case I::MOD16:
            address = POP_ADDR();
            val = POP_ADDR();
            if (val == 0)
                HANDLE_EXCEPTION(InterruptCodes::DivisionByZeroError);
            PUSHI_ADDR(address % val);
            break;
        case I::MUL:
            PUSHI((POP() * POP()));
            break;
        case I::MUL16:
            PUSHI_ADDR((POP_ADDR() * POP_ADDR()));
            break;
        case I::MUL16C:
            address = read_addr_from_program(skip);
            PUSHI_ADDR((POP_ADDR() * address));
            break;

        case I::EQ:
            PUSHI(POP() == POP() ? 1 : 0);
            break;
        case I::NE:
            PUSHI(POP() == POP() ? 0 : 1);
            break;
        case I::LESS:
            PUSHI(POP() < POP() ? 1 : 0);
            break;
        case I::LESS_OR_EQ:
            PUSHI(POP() <= POP() ? 1 : 0);
            break;
        case I::GREATER:
            PUSHI(POP() > POP() ? 1 : 0);
            break;
        case I::GREATER_OR_EQ:
            PUSHI(POP() >= POP() ? 1 : 0);
            break;
        case I::ZERO:
            sp_value = READ_REGISTER(SP_REGISTER);
            memory[sp_value - 1] = (word)(memory[sp_value - 1] == 0 ? 1 : 0);
            break;
        case I::NZERO:
            sp_value = READ_REGISTER(SP_REGISTER);
            memory[sp_value - 1] = (word)(memory[sp_value - 1] != 0 ? 1 : 0);
            break;

        case I::EQ16:
            PUSHI(POP_ADDR() == POP_ADDR() ? 1 : 0);
            break;
        case I::NE16:
            PUSHI(POP_ADDR() != POP_ADDR() ? 1 : 0);
            break;
        case I::LESS16:
            PUSHI(POP_ADDR() < POP_ADDR() ? 1 : 0);
            break;
        case I::LESS_OR_EQ16:
            PUSHI(POP_ADDR() <= POP_ADDR() ? 1 : 0);
            break;
        case I::GREATER16:
            PUSHI(POP_ADDR() > POP_ADDR() ? 1 : 0);
            break;
        case I::GREATER_OR_EQ16:
            PUSHI(POP_ADDR() >= POP_ADDR() ? 1 : 0);
            break;
        case I::ZERO16:
            PUSHI(POP_ADDR() == 0 ? 1 : 0);
            break;
        case I::NZERO16:
            PUSHI(POP_ADDR() != 0 ? 1 : 0);
            break;

        case I::AND:
            PUSHI(POP() & POP());
            break;
        case I::OR:
            PUSHI(POP() | POP());
            break;
        case I::LAND:
            PUSHI((POP() != 0) && (POP() != 0) ? 1 : 0);
            break;
        case I::LOR:
            PUSHI((POP() != 0) || (POP() != 0) ? 1 : 0);
            break;
        case I::XOR:
            PUSHI(POP() ^ POP());
            break;
        case I::LSH:
        {
            auto tmp1 = POP();
            auto tmp2 = POP();
            signedResult = tmp2 << tmp1;
            PUSHI(signedResult);
            break;
        }
        case I::RSH:
        {
            auto tmp1 = POP();
            auto tmp2 = POP();
            signedResult = tmp2 >> tmp1;
            PUSHI(signedResult);
            break;
        }
        case I::FLIP:
            PUSHI(~POP());
            break;


        case I::AND16:
            PUSHI_ADDR(POP_ADDR() & POP_ADDR());
            break;
        case I::OR16:
            PUSHI_ADDR(POP_ADDR() | POP_ADDR());
            break;
        case I::XOR16:
            PUSHI_ADDR(POP_ADDR() ^ POP_ADDR());
            break;
        case I::LSH16:
        {
            auto tmp1 = POP_ADDR();
            auto tmp2 = POP_ADDR();
            signedResult = tmp2 << tmp1;
            PUSHI_ADDR(signedResult);
            break;
        }
        case I::RSH16:
        {
            auto tmp1 = POP_ADDR();
            auto tmp2 = POP_ADDR();
            signedResult = tmp2 >> tmp1;
            PUSHI_ADDR(signedResult);
            break;
        }
        case I::FLIP16:
            PUSHI_ADDR(~POP_ADDR());
            break;

        case I::NOT:
            sp_value = READ_REGISTER(SP_REGISTER);
            memory[sp_value - 1] = (word)(memory[sp_value - 1] ? 0 : 1);
            break;
        case I::INC:
            sp_value = READ_REGISTER(SP_REGISTER);
            memory[sp_value - 1]++;
            break;
        case I::DEC:
            sp_value = READ_REGISTER(SP_REGISTER);
            memory[sp_value - 1]--;
            break;
        case I::INC16:
            offset = READ_REGISTER(SP_REGISTER) - ADDRESS_SIZE;
            write16(memory, offset, (addr)(read16(memory, offset) + 1));
            break;
        case I::DEC16:
            offset = READ_REGISTER(SP_REGISTER) - ADDRESS_SIZE;
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
            WRITE_REGISTER(IP_REGISTER, address);
            skip = 0;
            break;
        case I::JMP_REL:
            offset = read_offs_from_program(skip);
            ADD_TO_REGISTER(IP_REGISTER, offset);
            skip = 0;
            break;
        case I::JF:
            address = read_addr_from_program(skip);
            if (!POP())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::JF16:
            address = read_addr_from_program(skip);
            if (!POP_ADDR())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::JT:
            address = read_addr_from_program(skip);
            if (POP())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::JT16:
            address = read_addr_from_program(skip);
            if (POP_ADDR())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::JF_REL:
            offset = read_offs_from_program(skip);
            if (POP() == 0)
            {
                ADD_TO_REGISTER(IP_REGISTER, offset);
                skip = 0;
            }
            break;
        case I::JT_REL:
            offset = read_offs_from_program(skip);
            if (POP() != 0)
            {
                ADD_TO_REGISTER(IP_REGISTER, offset);
                skip = 0;
            }
            break;
        case I::JMP2:
            address = POP_ADDR();
            WRITE_REGISTER(IP_REGISTER, address);
            skip = 0;
            break;
        case I::JT2:
            address = POP_ADDR();
            if (POP())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::JF2:
            address = POP_ADDR();
            if (!POP())
            {
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::CASE:
            arg = read_next_program_byte(skip);
            address = read_addr_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            sp_value = READ_REGISTER(SP_REGISTER);
            if (memory[sp_value - 1] == arg)
            {
                POP();
                WRITE_REGISTER(IP_REGISTER, address);
                skip = 0;
            }
            break;
        case I::ELSE:
            POP();
            address = read_addr_from_program(skip);
            WRITE_REGISTER(IP_REGISTER, address);
            skip = 0;
            break;
        case I::CASE_REL:
            arg = read_next_program_byte(skip);
            offset = read_offs_from_program(skip, 2);
            skip = 2 + ADDRESS_SIZE;
            sp_value = READ_REGISTER(SP_REGISTER);
            if (memory[sp_value - 1] == arg)
            {
                POP();
                ADD_TO_REGISTER(IP_REGISTER, offset + 1);
                skip = 0;
            }
            break;
        case I::ELSE_REL:
            POP();
            offset = read_offs_from_program(skip);
            ADD_TO_REGISTER(IP_REGISTER, offset);
            skip = 0;
            break;
        case I::LOAD_GLOBAL:
            address = POP_ADDR();
            PUSH(memory[address]);
            break;
        case I::STORE_GLOBAL:
            address = POP_ADDR();
            arg = POP();
            memory[address] = arg;
            break;
        case I::STORE_GLOBAL2:
            arg = POP();
            address = POP_ADDR();
            memory[address] = arg;
            break;
        case I::LOAD_GLOBAL16:
            address = POP_ADDR();
            PUSH_ADDR(read16(memory, address));
            break;
        case I::STORE_GLOBAL16:
            address = POP_ADDR();
            val = POP_ADDR();
            write16(memory, address, val);
            break;
        case I::STORE_GLOBAL216:
            val = POP_ADDR();
            address = POP_ADDR();
            write16(memory, address, val);
            break;
        case I::LOAD: // merged cases optimize better
        case I::LOAD_LOCAL:
        case I::LOAD_ARG:
        case I::LOAD_LOCAL16:
        case I::LOAD_ARG16:
            arg = read_next_program_byte(skip);
            direction = (instr == I::LOAD || instr == I::LOAD_ARG || instr == I::LOAD_ARG16) ? -1 : 1;
            offset = (instr == I::LOAD_ARG || instr == I::LOAD_ARG16) ? 2 * ADDRESS_SIZE : 0;
            if (instr == I::LOAD_LOCAL16 || instr == I::LOAD_ARG16)
                PUSH_ADDR(read16(memory, READ_REGISTER(FP_REGISTER) + (arg + offset) * direction));
            else
                PUSH(memory[READ_REGISTER(FP_REGISTER) + (arg + offset) * direction]);
            break;
        case I::STORE:
        case I::STORE_LOCAL:
        case I::STORE_ARG:
        case I::STORE_LOCAL16:
        case I::STORE_ARG16:
            arg = read_next_program_byte(skip);
            direction = (instr == I::STORE || instr == I::STORE_ARG || instr == I::STORE_ARG16) ? -1 : 1;
            offset = (instr == I::STORE_ARG || instr == I::STORE_ARG16) ? 2 * ADDRESS_SIZE : 0;
            if (instr == I::STORE_LOCAL16 || instr == I::STORE_ARG16)
                write16(memory, READ_REGISTER(FP_REGISTER) + (arg + offset) * direction, POP_ADDR());
            else
                memory[READ_REGISTER(FP_REGISTER) + (arg + offset) * direction] = POP();
            break;
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
                address = (addr)(READ_REGISTER(IP_REGISTER) + offset);
            }
            else
            {
                address = instr == I::CALL ? read_addr_from_program(skip) : POP_ADDR();
            }
            CALL(address);
            skip = 0;
            break;
        case I::RET:
            WRITE_REGISTER(SP_REGISTER, READ_REGISTER(FP_REGISTER)); // clear stack after function execution
            WRITE_REGISTER(FP_REGISTER, POP_ADDR());
            address = POP_ADDR();
            WRITE_REGISTER(IP_REGISTER, (addr)(address + ADDRESS_SIZE + 1)); // skip address of call and go to next instruction
            skip = 0;
            break;
        case I::SWAP:
            sp_value = READ_REGISTER(SP_REGISTER);
            tmp = memory[sp_value - 1];
            memory[sp_value - 1] = memory[sp_value - 2];
            memory[sp_value - 2] = tmp;
            break;
        case I::SWAP16:
            sp_value = READ_REGISTER(SP_REGISTER);
            val = read16(memory, sp_value - ADDRESS_SIZE * 2);
            write16(memory, sp_value - ADDRESS_SIZE * 2, read16(memory, sp_value - ADDRESS_SIZE));
            write16(memory, sp_value - ADDRESS_SIZE, val);
            break;
        case I::DUP:
            sp_value = READ_REGISTER(SP_REGISTER);
            PUSH(memory[sp_value - 1]);
            break;
        case I::DUP16:
            sp_value = READ_REGISTER(SP_REGISTER);
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
                    HANDLE_EXCEPTION(result);
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
            memory[READ_REGISTER(FP_REGISTER) + arg] += 1;
            break;
        case I::MACRO_DEC_LOCAL:
            arg = read_next_program_byte(skip);
            memory[READ_REGISTER(FP_REGISTER) + arg] -= 1;
            break;
        case I::MACRO_INC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, READ_REGISTER(FP_REGISTER) + arg, read16(memory, READ_REGISTER(FP_REGISTER) + arg) + 1);
            break;
        case I::MACRO_DEC_LOCAL16:
            arg = read_next_program_byte(skip);
            write16(memory, READ_REGISTER(FP_REGISTER) + arg, read16(memory, READ_REGISTER(FP_REGISTER) + arg) - 1);
            break;
        case I::MACRO_X2:
        {
            PUSH(POP() << 1);
            break;
        }
        case I::MACRO_X216:
        {
            PUSH_ADDR(POP_ADDR() << 1);
            break;
        }

        default:
            throw std::runtime_error("Instruction not implemented: " + std::to_string(instr));
        }

        ADD_TO_REGISTER(IP_REGISTER, skip);
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
        sp_value = READ_REGISTER(SP_REGISTER);
        std::cout << (int)memory[sp_value - 1];
        break;
    case Stdlib::PrintInt16:
        sp_value = READ_REGISTER(SP_REGISTER);
        std::cout << (int)read16(memory, sp_value - ADDRESS_SIZE);
        break;
    case Stdlib::PrintNewLine:
        std::cout << std::endl;
        break;
    
    case Stdlib::PrintChar:
        sp_value = READ_REGISTER(SP_REGISTER);
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