# nullable disable
using AVM;
using System.Diagnostics;
using System.IO;


if (args.Length == 0)
{
    Console.WriteLine("Arguments: program_file.(asm|avm) -c [-r]\n" +
        "Option -c compiles the ASM to AVM file\n" +
        "Option -r runs the file in addition to compilation");
    return;
}

var run = false;
var compile = false;
var fromBinary = false;
var inputFile = args[0];

if (!File.Exists(inputFile))
{
    Console.WriteLine("Invalid input file!");
    return;
}

var ext = Path.GetExtension(inputFile).ToLower();
var directory = Path.GetDirectoryName(inputFile);
var baseName = Path.GetFileNameWithoutExtension(inputFile);
var nvramFile = Path.Combine(directory, baseName + "_nvram.bin");

if (ext == ".asm")
{
    if (args.Contains("-c"))
    {
        compile = true;
    }
    if (args.Contains("-r"))
    { 
        run = true;
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
    Console.WriteLine("Unsupported file format!");
    return;
}


byte[] program;

if (fromBinary)
{
    program = Compiler.ReadBinary(inputFile);
}
else
{
    if (compile)
    {
        var avmFile = Path.Combine(directory, baseName + ".avm");
        var dbgFile = Path.Combine(directory, baseName + ".dbg");
        using (var writer = new StreamWriter(dbgFile))
            program = Compiler.ReadAndCompile(new StreamReader(inputFile), writer);
        Compiler.WriteBinary(avmFile, program);

        Console.WriteLine($"Output file: {avmFile}");
        Console.WriteLine($"Debug file: {dbgFile}");

        if (!run)
            return;
    }
    else
    {
        program = Compiler.ReadAndCompile(new StreamReader(inputFile));
    }
}

var machine = new VM();

machine.LoadProgram(program, nvram_file: nvramFile);
Stopwatch sw = Stopwatch.StartNew();
try
{
    machine.RunProgram();
}
catch (Exception ex)
{ 
    Console.WriteLine(ex.ToString());
    Console.WriteLine("Backtrace:");
    var bt = machine.Backtrace;
    foreach (var a in bt)
        Console.Write(a.ToString() + " ");
    Console.WriteLine();
}
sw.Stop();
Console.WriteLine($"Program size: {program.Length}, Max SP: {machine.MaxStackPointer}, cycles {machine.ExecutedInstructionCount}");
Console.WriteLine($"Time: {sw.Elapsed.TotalSeconds} s");
