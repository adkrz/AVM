# AVM - adkrz Virtual Machine

This project is a toy stack based virtual machine, made for fun and education.
The code is written in C#, with runtime engine also ported to C++ (Windows only).

Despite its simplicity, it is capable of running quite complex programs written in text assembly - see the Snake game from Examples!

Aim of the project was also to create simple assembler for convenient program writing and debugging aid for Visual Studio.

For the brave souls, there is also a working Brainfuck language interpreter, written using this virtual machine - see Examples folder.

# Running examples
- From text file: `AVM.exe program.asm`
- From binary file: `AVM.exe program.avm`
- Compile binary from text: `AVM.exe program.asm -c`. Optionally add -r to run afterwards.


# Machine architecture
- 8 bit instructions, with 16 bit addressing = 64KiB of usable memory
- stack based architecture, no general purpose registers. All operands and operation results are using the stack top.
- 3 16bit system registers (instruction pointer IP, frame pointer FP, stack pointer SP), not directly programmed by the user. This follows usual CALL/RET architecture found in other systems.
- program and stack is in the same memory, stack grows up from the last instruction of loaded program. Instructions can read directly data from program area without extra copying. This also makes it a great tool for playing with self modifying code
- variables of type word (uchar) or addr (uint16), no support for negative numbers (numbers will overflow)
- random access to reach values outside the top of the stack, like local variables, function arguments, memory on heap -> using LOAD\*/STORE\* instructions
- set of all required operations: aritmetic, logic, control flow + subset of 16 bit instructions to compute addresses
- exception handling via interrupt handlers
- simple standard libary with console IO, memory operations, random number generator
- simple "nvram" interface to store data on the disk

# Instruction set
Please read comments in `Types.cs` and refer to examples. Please note, that instructions with "16" in name operate on 2 bytes.

# Assembler
Unlike many other toy virtual machines found in the internet, this one has a Compiler class, which reads the assembly code from text file, does basic parsing and outputs bytecode.

Most helpful feature is the **labels**, Instead of calculating jump and call addresses manually (and updating these if program changes in the future...) the compiler calculates them automatically. When the `:label` statement is found, its address is stored, and when the `@label` is found, 16-bit address of the label is inserted there. This greatly simplifies programming - use labels in CALL, JMP, JT, JF instructions.

Another useful option is the **constants** - to define 8bit `const` or 16-bit `const16` fixed values to use later in program.

The numbers are by default written as 8bit. If number is preceded with #, will be written as 16 bit.

The assembler is also capable of processing comments, indicated by `;` or `//`.

Raw strings in `"double quotes"` will be also dumped to the code, e.g. to create strings to display to the user, see example `read_string`. Simple escape codes like \r, \n, \t, \0 are supported.

Optionally, the Compiler class can output a file with debug symbols. It is the same source file as input one, but each line will be prefixed with generated address number. When debugging, one may refer to the file to compare with instruction pointer, what line is currently executed.

# Programming tips
- Calling convention is up to the programmer. The CALL instruction saves current IP and FP to the stack, RET recovers them and clears the stack. If function has any arguments, they must be placed on the stack before CALL. Also, if function returns something, place for the return value must be made on the stack by the caller. It does not matter, if the return value will be first or last function arguments. Function can also return value by reference, by directly modifying its argument values. If the caller prepares arguments and/or retval on stack, the caller is also responsible for cleaning them up.
- To access the function args and return value, use LOAD_ARG, LOAD_ARG16, STORE_ARG, STORE_ARG16. These instructions take current FP value, skip saved IP and SP on the stack and use negative offset to reach variables BEFORE the actual function stack.
- To access local variables pushed to the stack in current function body, use LOAD_LOCAL, STORE_LOCAL, LOAD_LOCAL16, STORE_LOCAL16. These functions reach memory AFTER frame pointer - with positive offset counted from 0.

Example accessing of variables on stack may look like this, looking at current stack contents:

```
-- caller local variables  --
SomeReturnValue 8bit ; prepared place for return, write it using STORE_ARG 4, 4 because it is -4 bytes from frame begin, automatically skipping saved ptrs
SomeArgument16bit ; copy to local stack using LOAD_ARG 3 (-3 bytes from stack frame beginning, skipping saved ptrs)
SomeArgument8bit ; copy to local stack using LOAD_ARG 1 ; -1 byte
[saved instruction pointer] ; these 16bit stack items are automaticallty omitted by LOAD_ARG(16) / STORE_ARG(16)
[saved stack pointer]
-- here begins the frame of called function --
some pushed value 8 bit ; copy/write using LOAD_LOCAL 0 because it is just at frame beginning
some other pushed value 16bit ; LOAD_LOCAL1, STORE_LOCAL 1
some other 8 bit value ; LOAD_LOCAL 3, STORE_LOCAL3 ; 3 bytes from beginning, since there is 16 bit value on the way
```

# Debugging
By debugging the VM class in Visual Studio, one can debug the program operations. For example, place the breakpoint before the big switch inside VM.StepProgram to get current instruction.
There is a special assembler instruction DEBUGGER which triggers VS debugging at the point desired in the code.
Moreover, the VM class has a couple of properties, that can be added to VS watchpoint list, that decode internal state of machine in a more readable way:

- `InstructionPointer` -> current position in program. You can use file with addresses, produced by assembler, to check where you are.
- `StackFrameContents` - the local variables of currently executed function
- `Backtrace` - call stack (what instructions called the currently executed function). Again - check the addresses against debug output file.
- `memory` array - the 65K array of program memory, contains program code, stack and heap, can be examined in VS watch window as well
- `registers` array - with IP, SP and FP

# C++ version
Part of C# code (runtime only, no compiler) is also ported to C++. With some effort (TODO) console-related commands can be rewritten so the code can potentially run on Linux.

