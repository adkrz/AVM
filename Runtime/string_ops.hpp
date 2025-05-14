#pragma once
#include <algorithm>
#include <string>
#include <string_view>
#include <iostream>

inline std::string to_lower(const std::string& str)
{
    std::string ret = str;
    std::transform(ret.begin(), ret.end(), ret.begin(), ::tolower);
    return ret;
}

inline std::string to_upper(const std::string& str)
{
    std::string ret = str;
    std::transform(ret.begin(), ret.end(), ret.begin(), ::toupper);
    return ret;
}

inline std::string to_upper(const std::string_view& str)
{
    std::string ret = std::string(str);
    std::transform(ret.begin(), ret.end(), ret.begin(), ::toupper);
    return ret;
}

inline std::string_view strip_line(const std::string& code_line)
{
    if (!code_line.length())
        return std::string_view();
    bool begin = true;
    size_t beg = 0;
    size_t end = code_line.length() - 1;
    for (size_t i = 0; i < code_line.size(); i++)
    {
        auto chr = code_line[i];
        if (begin)
        {
            if (chr == ' ' || chr == '\t')
            {
                beg = i + 1;
                continue;
            }
            else
                begin = false;
        }
        if (chr == ';')
        {
            if (i > 0)
            {
                end = i - 1;
                break;
            }
            else
                return std::string_view();
        }
    }
    for (size_t i = end; i >= beg; i--)
    {
        auto chr = code_line[i];
        if (chr == ' ' || chr == '\t')
        {
            end = i - 1;
            continue;
        }
        else break;
    }
    return std::string_view(code_line).substr(beg, end - beg + 1);
}

/*
void _mkTest(const std::string& input, const std::string& expected)
{
            auto output = strip_line(input);
            auto result = output == expected ? "OK" : "NOK";
            std::cout << "\"" << input << "\" -> \"" << output << "\" - " << result << std::endl;
}

void test_strip_line()
{
            _mkTest("", "");
            _mkTest("test", "test");
            _mkTest("test   ", "test");
            _mkTest("   test", "test");
            _mkTest("\ttest", "test");
            _mkTest("test ; comment ", "test");
            _mkTest("\ttest\t;comment\t", "test");
}*/

inline bool replace(std::string& str, const std::string& from, const std::string& to) {
    size_t start_pos = str.find(from);
    if (start_pos == std::string::npos)
        return false;
    str.replace(start_pos, from.length(), to);
    return true;
}


inline std::vector<std::string_view> split(const std::string_view& s, char delimiter) {
    size_t pos_start = 0, pos_end, delim_len = 1;
    std::vector<std::string_view> res;

    while ((pos_end = s.find(delimiter, pos_start)) != std::string::npos) {
        if (pos_start != pos_end)
        {
            auto token = s.substr(pos_start, pos_end - pos_start);
            pos_start = pos_end + delim_len;
            res.push_back(token);
        }
    }

    res.push_back(s.substr(pos_start));
    return res;
}
