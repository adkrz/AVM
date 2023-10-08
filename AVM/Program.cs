# nullable disable
using AVM;
using System.Diagnostics;


var programName = "snake";
var path = @$"..\..\..\programs\{programName}.asm";
var dbgInfo = @$"..\..\..\programs\{programName}.dbg";

//Read the ASM file and produce binary bytecode + debug info text file
var program = Compiler.ReadAndCompile(new StreamReader(path), new StreamWriter(dbgInfo));

// The bytecode can be either loaded to machine directly, or saved to disk
//var binaryPath = @$"..\..\..\programs\{programName}.avm";
//Compiler.WriteBinary(binaryPath, program);
// If loading from disk, there is ready to use procedure to read it:
//var program2 = Compiler.ReadBinary(binaryPath);

var machine = new VM();

machine.LoadProgram(program, nvram_file: @$"..\..\..\programs\{programName}_nvram.bin");
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
