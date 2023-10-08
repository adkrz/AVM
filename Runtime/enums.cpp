#include "enums.hpp"

Enums::Enums()
{
	if (Instructions.empty())
	{
		Instructions[I::NOP] = "NOP";
		Instructions[I::PUSH] = "PUSH";
		Instructions[I::PUSHN] = "PUSHN";
		Instructions[I::PUSHN2] = "PUSHN2";
		Instructions[I::POP] = "POP";
		Instructions[I::POPN] = "POPN";
		Instructions[I::POPN2] = "POPN2";
		Instructions[I::SWAP] = "SWAP";
		Instructions[I::DUP] = "DUP";
		Instructions[I::PUSH_REG] = "PUSH_REG";
		Instructions[I::POP_REG] = "POP_REG";
		Instructions[I::ADD] = "ADD";
		Instructions[I::SUB] = "SUB";
		Instructions[I::MUL] = "MUL";
		Instructions[I::DIV] = "DIV";
		Instructions[I::MOD] = "MOD";
		Instructions[I::INC] = "INC";
		Instructions[I::DEC] = "DEC";
		Instructions[I::AND] = "AND";
		Instructions[I::OR] = "OR";
		Instructions[I::FLIP] = "FLIP";
		Instructions[I::NOT] = "NOT";
		Instructions[I::XOR] = "XOR";
		Instructions[I::LSH] = "LSH";
		Instructions[I::RSH] = "RSH";
		Instructions[I::EQ] = "EQ";
		Instructions[I::LESS] = "LESS";
		Instructions[I::LESS_OR_EQ] = "LESS_OR_EQ";
		Instructions[I::ZERO] = "ZERO";
		Instructions[I::JMP] = "JMP";
		Instructions[I::JMP2] = "JMP2";
		Instructions[I::JF] = "JF";
		Instructions[I::JF2] = "JF2";
		Instructions[I::JT] = "JT";
		Instructions[I::JT2] = "JT2";
		Instructions[I::CALL] = "CALL";
		Instructions[I::RET] = "RET";
		Instructions[I::CALL2] = "CALL2";
		Instructions[I::LOAD_GLOBAL] = "LOAD_GLOBAL";
		Instructions[I::STORE_GLOBAL] = "STORE_GLOBAL";
		Instructions[I::LOAD_GLOBAL16] = "LOAD_GLOBAL16";
		Instructions[I::STORE_GLOBAL16] = "STORE_GLOBAL16";
		Instructions[I::LOAD] = "LOAD";
		Instructions[I::STORE] = "STORE";
		Instructions[I::LOAD_ARG] = "LOAD_ARG";
		Instructions[I::STORE_ARG] = "STORE_ARG";
		Instructions[I::LOAD_LOCAL] = "LOAD_LOCAL";
		Instructions[I::STORE_LOCAL] = "STORE_LOCAL";
	}
}