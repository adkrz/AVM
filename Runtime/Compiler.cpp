#include "Compiler.hpp"
#include "string_ops.hpp"
#include <memory>
#include <ranges>
#include <string_view>
#include <charconv>
#include "magic_enum.hpp"

std::vector<word> Compiler::ReadAndCompile(std::ifstream& inputFile)
{
    std::string line;
    int lineNo = 0;
    std::vector<word> program;
    addr address = 0;

    std::map<std::string, addr> labels;
    std::map<addr, std::string> labelsToFill;

    std::map<std::string, int> constants;
    std::map<std::string, unsigned short int> constants16;
    //bool relativeMode = false;

    auto check = [&](const std::vector<std::string_view> vct, size_t index){
        if (index>=vct.size())
            throw std::runtime_error("Invalid token count in line " + std::to_string(lineNo));
        return vct[index];
    };

    auto processInt8 = [&](const std::vector<std::string_view> vct, size_t index){
            auto token = check(vct, index);
            uint8_t ii;
            auto result = std::from_chars(token.data(), token.data() + token.size(), ii);
            if (result.ec == std::errc())
            {
                program.push_back((word)ii);
                address++;
            }
        };
    auto processUInt32 = [&](const std::vector<std::string_view> vct, size_t index){
            auto token = check(vct, index);
            uint32_t i32 = 0;
            auto result = std::from_chars(token.data(), token.data() + token.size(), i32);
            if (result.ec == std::errc::invalid_argument)
                throw std::runtime_error("Invalid number {" + std::string(token) + "} at line {" + std::to_string(lineNo) + "}");
            program.push_back((word)i32);
            program.push_back((word)(i32 >> 8));
            program.push_back((word)(i32 >> 16));
            program.push_back((word)(i32 >> 24));
            address += 4;
        };
    auto processInt32 = [&](const std::vector<std::string_view> vct, size_t index){
            auto token = check(vct, index);
            int32_t i32 = 0;
            auto result = std::from_chars(token.data(), token.data() + token.size(), i32);
            if (result.ec == std::errc::invalid_argument)
                throw std::runtime_error("Invalid number {" + std::string(token) + "} at line {" + std::to_string(lineNo) + "}");
            program.push_back((word)i32);
            program.push_back((word)(i32 >> 8));
            program.push_back((word)(i32 >> 16));
            program.push_back((word)(i32 >> 24));
            address += 4;
        };
    auto processLabelReference = [&](const std::vector<std::string_view> vct, size_t index){
            auto token = check(vct, index);
            auto l = std::string(token.substr(1)); // cut @
            labelsToFill[address] = l;
            for (int ii = 0; ii < VM::ADDRESS_SIZE; ii++)
            {
                program.push_back(0);
                address++;
            }
        };
    auto processSyscall = [&](const std::vector<std::string_view> vct, size_t index){
            auto token = check(vct, index);
            auto tokenU = to_upper(token);
            auto ic = magic_enum::enum_cast<Stdlib>(tokenU.substr(4), magic_enum::case_insensitive);
                if (ic.has_value())
                {
                    program.push_back((word)ic.value());
                    address++;
                }
                else
                    throw std::runtime_error("Invalid stdlib code {" + tokenU + "} at line {" + std::to_string(lineNo) + "}");
        };
    auto processInstruction = [&](I instr){
            program.push_back((word)instr);
            address++;
    };

    while (std::getline(inputFile, line))
    {
        lineNo++;

        auto trimmed = strip_line(line);
        if (trimmed.length() == 0) continue;
        
        if (trimmed.starts_with("\""))
        {
            trimmed = trimmed.substr(1, trimmed.length() - 2);
            auto escaped = ParseEscapeCodes(trimmed);
            bool generateTerminator = true;
            for (size_t i = 0; i < escaped.size(); i++)
            {
                if (i == 0 && escaped[i] == '!')
                {
                    generateTerminator = true;
                    continue;
                }
                program.push_back(escaped[i]);
                address++;
            }
            if (generateTerminator)
            {
                program.push_back(0);
                address++;
            }
            continue;
        }
        else if (trimmed.starts_with(":"))
        {
            auto l = std::string(trimmed.substr(1));
            if (labels.count(l))
                throw std::runtime_error("Duplicate label " + l);
            labels[l] = address;
            continue;
        }

        auto tokens = split(trimmed, ' ');
        if (!tokens.size())
            continue;

        auto instr = magic_enum::enum_cast<I>(tokens[0], magic_enum::case_insensitive);

        if (!instr.has_value())
        {
            throw std::runtime_error("Invalid code {" + std::string(tokens[0]) + "} at line {" + std::to_string(lineNo) + "}");
        }

        auto i = instr.value();
        processInstruction(i);

        switch (i)
        {
            case I::NOP:
            case I::HALT:
            case I::PRINT_FRAMES:
                break;;
            case I::NEW_FRAME:
                processInt8(tokens, 1);
                break;
            case I::MOV_RU:
                processInt8(tokens, 1);
                processUInt32(tokens, 2);
                break;
            case I::MOV_RI:
                processInt8(tokens, 1);
                processInt32(tokens, 2);
                break;
            case I::MOV_RR:
                processInt8(tokens, 1);
                processInt8(tokens, 2);
                break;
            default:
                throw std::runtime_error("Missing implementation of instruction " + std::string(tokens[0]));
        }

    }

    for (auto& pair : labelsToFill)
    {
        writeU32(program.data(), pair.first, labels[pair.second]);
    }

    program.push_back((word)I::HALT);

    return program;
}

std::string Compiler::ParseEscapeCodes(const std::string_view& data)
{
    auto ret = std::string(data);
    replace(ret, "\\n", "\n");
    replace(ret, "\\r", "\r");
    replace(ret, "\\t", "\t");
    replace(ret, "\\0", "\0");
    return ret;
}