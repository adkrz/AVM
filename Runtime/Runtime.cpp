#include <iostream>
#include <fstream>
#include <vector>
#include "VM.hpp"
#include <chrono>
#include <filesystem>
#include "string_ops.hpp"
#include "Compiler.hpp"

int main(int argc, char** argv)
{
    if (argc <= 1)
    {
        std::cout << "Arguments: program_file.(asm|avm) -c [-r]\n"
            << "Option -c compiles the ASM to AVM file\n"
            << "Option -r runs the file in addition to compilation\n"
#ifdef WITH_PROFILER
            << "Option -p runs the profiler\n"
#endif
        ;
        return 1;
    }

    auto run = false;
    auto compile = false;
    auto fromBinary = false;
    auto profile = false;
    auto inputFile = argv[1];

    if (!std::filesystem::exists(inputFile))
    {
        std::cerr << "Invalid input file!\n";
        return 1;
    }

    auto path = std::filesystem::path(inputFile);
    auto ext = to_lower(path.extension().generic_string());
    auto directory = path.parent_path();
    auto basename = path.stem();
    auto nvr_file = directory / basename;
    nvr_file += "_nvram.bin";

    if (ext == ".asm")
    {
        for (int i = 0; i < argc; i++)
        {
            if (std::string(argv[i]) == "-c")
                compile = true;
            else if (std::string(argv[i]) == "-r")
                run = true;
#ifdef WITH_PROFILER
            else if (std::string(argv[i]) == "-p")
                profile = true;
#endif
        }
    }
    else if (ext == ".avm")
    {
        compile = false;
        run = true;
        fromBinary = true;
    }
    else
    {
        std::cerr << "Unsupported file format!\n";
        return 1;
    }

    std::vector<word> program;

    if (fromBinary)
    {
        std::ifstream infile(inputFile, std::ios::binary);

        //get length of file
        infile.seekg(0, std::ios::end);
        auto length = infile.tellg();
        infile.seekg(0, std::ios::beg);

        //read file
        program.resize(length);
        infile.read(reinterpret_cast<char*>(program.data()), length);
    }
    else
    {
        if (compile)
        {
            auto avmFile = directory / basename;
            auto dbgFile = avmFile;
            avmFile += ".avm";
			dbgFile += ".dbg";
            auto stream = std::ifstream(inputFile);
            program = Compiler().ReadAndCompile(stream);
            std::ofstream outfile(avmFile, std::ios::binary);
            outfile.write(reinterpret_cast<const char*>(program.data()), program.size());
            if (!run)
                return 0;
        }
        else
        {
            auto stream = std::ifstream(inputFile);
            program = Compiler().ReadAndCompile(stream);
        }
    }

    VM vm;
    vm.LoadProgram(program.data(), (int)program.size(), 65535, nvr_file.string().c_str());

    using std::chrono::high_resolution_clock;
    using std::chrono::duration_cast;
    using std::chrono::duration;
    using std::chrono::milliseconds;

    auto t1 = high_resolution_clock::now();
    if (profile)
        vm.RunProgram(true);
    else
        vm.RunProgram();
    auto t2 = high_resolution_clock::now();
    duration<double, std::milli> ms_double = t2 - t1;
    std::cout << std::endl << ms_double.count() << "ms\n";
    return 0;
}
