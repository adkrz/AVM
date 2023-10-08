#pragma once
#include "types.hpp"
#include <map>
#include <string>
class Enums
{
public:
	Enums();
private:
	static std::map<I, std::string> Instructions;
};