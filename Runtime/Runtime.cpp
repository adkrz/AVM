// Runtime.cpp : This file contains the 'main' function. Program execution begins and ends there.
//

#include <iostream>
#include <fstream>
#include <vector>
#include "VM.hpp"
#include <chrono>

int main(int argc, char** argv)
{
    std::ifstream infile(argv[1], std::ios::binary);

    //get length of file
    infile.seekg(0, std::ios::end);
    size_t length = infile.tellg();
    infile.seekg(0, std::ios::beg);

    //read file
    auto buffer = new word[length];
    infile.read(reinterpret_cast<char*>(buffer), length);

    VM vm;
    vm.LoadProgram(buffer, (int)length, 65535);

    using std::chrono::high_resolution_clock;
    using std::chrono::duration_cast;
    using std::chrono::duration;
    using std::chrono::milliseconds;

    auto t1 = high_resolution_clock::now();
    vm.RunProgram();
    auto t2 = high_resolution_clock::now();
    duration<double, std::milli> ms_double = t2 - t1;
    std::cout << ms_double.count() << "ms\n";

}