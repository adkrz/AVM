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
    addr address = VM::PROGRAM_BEGIN;

    std::map<std::string, addr> labels;
    std::map<addr, std::string> labelsToFill;
    std::map<addr, std::string> relLabelsToFill;

    std::map<std::string, int> constants;
    std::map<std::string, unsigned short int> constants16;
    bool relativeMode = false;

    while (std::getline(inputFile, line))
    {
        lineNo++;

        auto trimmed = strip_line(line);
        if (trimmed.length() == 0) continue;
        auto trimmedU = to_upper(trimmed);

        if (trimmedU.starts_with("CONST "))
        {
            auto tokens = split(trimmed, ' ');
            if (tokens.size() != 3)
                throw std::runtime_error("Invalid const at line" + std::to_string(lineNo) + ", expected CONST NAME intValue");
            int cValue = 0;
            auto cName = std::string(tokens[1]);
            auto result = std::from_chars(tokens[2].data(), tokens[2].data() + tokens[2].size(), cValue);
            if (result.ec == std::errc::invalid_argument)
                throw std::runtime_error("Invalid const at line" + std::to_string(lineNo) + ", expected CONST NAME intValue");
            constants[cName] = cValue;
            continue;
        }
        else if (trimmedU.starts_with("CONST16 "))
        {
            auto tokens = split(trimmed, ' ');
            if (tokens.size() != 3)
                throw std::runtime_error("Invalid const16 at line" + std::to_string(lineNo) + ", expected CONST16 NAME intValue");
            auto cName = std::string(tokens[1]);
            int cValue = 0;
            auto result = std::from_chars(tokens[2].data(), tokens[2].data() + tokens[2].size(), cValue);
            if (result.ec == std::errc::invalid_argument)
                throw std::runtime_error("Invalid const16 at line" + std::to_string(lineNo) + ", expected CONST16 NAME intValue");
            constants16[cName] = cValue;
            continue;
        }
        else if (trimmed.starts_with("\""))
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

        for (const auto token : split(trimmed, ' '))
        {
            if (token.starts_with(':'))
            {
                auto l = std::string(token.substr(1));
                if (labels.count(l))
                    throw std::runtime_error("Duplicate label " + l);
                labels[l] = address;
                continue;
            }
            else if (token.starts_with('@'))
            {
                auto l = std::string(token.substr(1));
                if (relativeMode)
                    relLabelsToFill[address] = l;
                else
                    labelsToFill[address] = l;
                for (int ii = 0; ii < VM::ADDRESS_SIZE; ii++)
                {
                    program.push_back(0);
                    address++;
                }
                relativeMode = false;
                continue;
            }

            auto tokenU = to_upper(token);

            if (tokenU.starts_with("INT."))
            {
                // Output interrupt code
                auto ic = magic_enum::enum_cast<InterruptCodes>(tokenU.substr(4), magic_enum::case_insensitive);
                if (ic.has_value())
                {
                    program.push_back((word)ic.value());
                    address++;
                    continue;
                }
                else
                    throw std::runtime_error("Invalid interrupt code {" + tokenU + "} at line {" + std::to_string(lineNo) + "}");
            }
            if (tokenU.starts_with("STD."))
            {
                // Output stdlib code
                auto ic = magic_enum::enum_cast<Stdlib>(tokenU.substr(4), magic_enum::case_insensitive);
                if (ic.has_value())
                {
                    program.push_back((word)ic.value());
                    address++;
                    continue;
                }
                else
                    throw std::runtime_error("Invalid stdlib code {" + tokenU + "} at line {" + std::to_string(lineNo) + "}");
            }
            if (tokenU.starts_with("CONST."))
            {
                auto ts = std::string(token.substr(6));
                if (!constants.count(ts))
                    throw std::runtime_error("Unknown constant {" + tokenU + "} at line {" + std::to_string(lineNo) + "}");
                program.push_back((word)constants[ts]);
                address++;
                continue;
            }
            if (tokenU.starts_with("CONST16."))
            {
                auto ts = std::string(token.substr(8));
                if (!constants16.count(ts))
                    throw std::runtime_error("Unknown constant16 {" + tokenU + "} at line {" + std::to_string(lineNo) + "}");
                program.push_back((word)constants16[ts]);
                address++;
                continue;
            }
            if (token.starts_with("#"))
            {
                // 16 bit int
                unsigned short int i16 = 0;
                auto ts = token.substr(1);
                auto result = std::from_chars(ts.data(), ts.data() + ts.size(), i16);
                if (result.ec == std::errc::invalid_argument)
                    throw std::runtime_error("Invalid number {" + std::string(token) + "} at line {" + std::to_string(lineNo) + "}");
                program.push_back((word)i16);
                program.push_back((word)(i16 >> 8));
                address += 2;
                continue;
            }

            int ii;
            auto result = std::from_chars(token.data(), token.data() + token.size(), ii);
            if (result.ec == std::errc())
            {
                // Output ordinary integer 8bit
                program.push_back((word)ii);
                address++;
                continue;
            }

            // Output instruction:
            auto instr = magic_enum::enum_cast<I>(tokenU, magic_enum::case_insensitive);
            if (instr.has_value())
            {
                if (tokenU.ends_with("_REL"))
                    relativeMode = true;
                program.push_back((word)instr.value());
                address++;
                continue;
            }

            throw std::runtime_error("Invalid code {" + std::string(token) + "} at line {" + std::to_string(lineNo) + "}");
        }

    }

    for (auto& pair : labelsToFill)
    {
        write16(program.data(), pair.first - VM::PROGRAM_BEGIN, labels[pair.second]);
    }
    for (auto& pair : relLabelsToFill)
    {
        write16(program.data(), pair.first - VM::PROGRAM_BEGIN, (offs)(labels[pair.second] - pair.first + 1));
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