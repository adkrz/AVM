#pragma once
#include <vector>
#include "VM.hpp"
class Compiler
{
public:
	std::vector<word> ReadAndCompile(std::ifstream& inputFile);
private:
	std::string ParseEscapeCodes(const std::string_view& data);
};