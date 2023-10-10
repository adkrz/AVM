enum I
{
    /// <summary>
    /// No operation
    /// </summary>
    NOP,

    // Stack operations

    /// <summary>
    /// Push fixed value to the stack
    /// read: val8bit push: val8bit
    /// </summary>
    PUSH,
    /// <summary>
    /// Move SP forward by fixed value from program (malloc-like), memory not initialized
    /// read: val8bit
    /// </summary>
    PUSHN,
    /// <summary>
    /// Move SP forward by value from stack (malloc-like), memory not initialized
    /// pop: val8bit
    /// </summary>
    PUSHN2,
    /// <summary>
    /// Pops and forgets one argument
    /// pop: val8bit
    /// </summary>
    POP,
    /// <summary>
    /// Pop N values from stack (like free), value from program
    /// read: val8bit
    /// </summary>
    POPN,
    /// <summary>
    /// Pop N values from stack (like free), value from stack
    /// pop: val8bit
    /// </summary>
    POPN2,
    /// <summary>
    /// Swap last 2 8-bit values on the stack
    /// </summary>
    SWAP,
    /// <summary>
    /// Duplicate last 8 bit value
    /// push: val8bit
    /// </summary>
    DUP,

    // Direct operations on registers (careful!)

    /// <summary>
    /// Read the register (1-IP, 2-SP 3-FP) to the stack
    /// read: val8bit, push: address16bit
    /// </summary>
    PUSH_REG,
    /// <summary>
    /// Read 16 bit value and write to register of number (1-IP, 2-SP 3-FP)
    /// read: val8bit, pop: address16bit
    /// </summary>
    POP_REG,

    // Math operations

    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    ADD,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    SUB,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    MUL,
    /// <summary>
    /// Raises <see cref="InterruptCodes.DivisionByZeroError"/>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    DIV,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    MOD,
    /// <summary>
    /// Increment value
    /// pop: val8bit, push: val8bit
    /// </summary>
    INC,
    /// <summary>
    /// Decrement value
    /// pop: val8bit, push: val8bit
    /// </summary>
    DEC,

    // Byte operations

    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    AND,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    OR,
    /// <summary>
    /// Bitwise NOT (flip bits)
    /// pop: val8bit, push: val8bit
    /// </summary>
    FLIP,
    /// <summary>
    /// Logical NOT - returns 0 or 1
    /// pop: val8bit, push: val8bit
    /// </summary>
    NOT,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    XOR,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    LSH,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit
    /// </summary>
    RSH,

    // Comparison operations

    /// <summary>
    /// Combine with NOT to get not eq
    /// pop: 2x val8bit, push: val8bit 0 or 1
    /// </summary>
    EQ,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit 0 or 1
    /// </summary>
    LESS,
    /// <summary>
    /// pop: 2x val8bit, push: val8bit 0 or 1
    /// </summary>
    LESS_OR_EQ,
    /// <summary>
    /// Checks if value is zero
    /// pop: val8bit, push: val8bit 0 or 1
    /// </summary>
    ZERO,

    // Control flow

    /// <summary>
    /// Unconditional jump
    /// read: address16bit
    /// </summary>
    JMP,
    /// <summary>
    /// Unconditional jump to user defined location
    /// pop: address16bit
    /// </summary>
    JMP2,
    /// <summary>
    /// Jump if value on stack is false (=0). Combine with NOT to get JT
    /// read: address16bit, pop: val8bit
    /// </summary>
    JF,
    /// <summary>
    /// Jump if value on stack is false(=0), to user defined location
    /// pop: val8bit, address16bit
    /// </summary>
    JF2,
    /// <summary>
    /// Jump if value on stack is true (!=0). Combine with NOT to get JT
    /// read: address16bit, pop: val8bit
    /// </summary>
    JT,
    /// <summary>
    /// Jump if value on stack is true (!=0), to user defined location
    /// pop: val8bit, address16bit
    /// </summary>
    JT2,
    /// <summary>
    /// If value on stack is equal the constant value, pops it and jumps to the address.
    /// Otherwise, leaves the value on stack so subsequent CASE or ELSE can consume it
    /// read: val8bit, address16bit, pop optional val8bit
    /// </summary>
    CASE,
    /// <summary>
    /// Pops the value on top of stack and unconditionally jumps to an address.
    /// To be used as a final jump after all CASEs.
    /// read: address16bit, pop val8bit
    /// </summary>
    ELSE,


    // Function calls

    /// <summary>
    /// read: address16bit
    /// </summary>
    CALL,
    /// <summary>
    /// Must be at the end of function or interrupt handler
    /// </summary>
    RET,
    /// <summary>
    /// Call function which pointer is on the stack
    /// pop: address16bit
    /// </summary>
    CALL2,

    // Pointers

    /// <summary>
    /// Load from address indicated by the value at the top of the stack
    /// pop: address16bit push: value8bit
    /// </summary>
    LOAD_GLOBAL,
    /// <summary>
    /// Store the 8bit value from stack at address
    /// pop: address16bit, value8bit (address on top of stack)
    /// </summary>
    STORE_GLOBAL,
    /// <summary>
    /// Load 16bit value from address indicated by the value at the top of the stack
    /// pop: address16bit push: address16bit
    /// </summary>
    LOAD_GLOBAL16,
    /// <summary>
    /// Store the 16bit value from stack at address
    /// pop: address16bit, address16bit (address on top of stack)
    /// </summary>
    STORE_GLOBAL16,

    /// <summary>
    /// Load data before frame pointer. E.g. offset 3 usually is return value, because we are skipping IP and FP backed up by CALL.
    /// read: offset8bit, push: value8bit
    /// </summary>
    LOAD,
    /// <summary>
    /// Write data before frame pointer. E.g. offset 3 usually is return value, because we are skipping IP and FP backed up by CALL.
    /// read: offset8bit, pop: value8bit
    /// </summary>
    STORE,
    /// <summary>
    /// shortcut for LOAD which adds 2 to offset -> skips saved instruction and frame pointers, so offset 1 is return value or last argument
    /// read: offset8bit, push: value8bit
    /// </summary>
    LOAD_ARG,
    /// <summary>
    /// shortcut for STORE which adds 2 to offset -> skips saved instruction and frame pointers, so offset 1 is return value or last argument
    /// read: offset8bit, pop: value8bit
    /// </summary>
    STORE_ARG,
    /// <summary>
    /// Copy data from after frame pointer to top of the stack, used to random access local variables. Offset counts from 0
    /// read: offset8bit, push: value8bit
    /// </summary>
    LOAD_LOCAL,
    /// <summary>
    /// Move data from stack top to place after frame pointer, used to random access local variables. Offset counts from 0
    /// read: offset8bit, pop: value8bit
    /// </summary>
    STORE_LOCAL,

    /// <summary>
    /// Register particular address (function) as interrupt handler for particular error/interrupt type. <see cref="InterruptCodes"/>
    /// 0 to unregister
    /// read: val8bit, address16bit
    /// </summary>
    INTERRUPT_HANDLER,
    /// <summary>
    /// Call the standard library of VM, <see cref="Stdlib"/>. Note: this does not work like normal CALL (no saving of IP and FP etc).
    /// Arg = call number,
    /// Refer to documentation of StdLib what a particular call requires on the stack or returns back
    /// read: val8bit
    /// </summary>
    SYSCALL,
    /// <summary>
    /// Call the standard library of VM, <see cref="Stdlib"/>. Note: this does not work like normal CALL (no saving of IP and FP etc).
    /// Arg = call number, taken dynamically from the user
    /// Refer to documentation of StdLib what a particular call requires on the stack or returns back
    /// pop: val8bit
    /// </summary>
    SYSCALL2,

    /// <summary>
    /// Trigger the debugger if VM is debugged in Visual Studio
    /// </summary>
    DEBUGGER,

    // 16-bit instruction set in addition to jumps and calls:

    /// <summary>
    /// Push current value of SP + ADDRESS_SIZE, use at beginning of memory allocation to get address of allocated data beginning
    /// push: address16bit
    /// </summary>
    PUSH_NEXT_SP,
    /// <summary>
    /// 16bit version of <see cref="I.PUSH"/>
    /// read: address16bit, push: address16bit
    /// </summary>
    PUSH16,
    /// <summary>
    /// 16bit version of <see cref="I.ADD"/>
    /// pop 2x address16bit, push: address16bit
    /// </summary>
    ADD16,
    /// <summary>
    /// Adds constant value from program to the address on the stack.
    /// Useful for computing fixed offsets
    /// read address16bit, pop address16bit, push: address16bit
    /// </summary>
    ADD16C,
    /// <summary>
    /// 16bit version of <see cref="I.MOD"/>
    /// pop 2x address16bit, push: address16bit
    /// </summary>
    MOD16,
    /// <summary>
    /// 16bit version of <see cref="I.SUB"/>
    /// pop 2x address16bit, push: address16bit
    /// </summary>
    SUB16,
    /// <summary>
    /// 16bit version of <see cref="I.MUL"/>
    /// pop 2x address16bit, push: address16bit
    /// </summary>
    MUL16,
    /// <summary>
    /// Multiplies constant value from program by the address on the stack.
    /// Useful for computing fixed offsets
    /// read address16bit, pop address16bit, push: address16bit
    /// </summary>
    MUL16C,
    /// <summary>
    /// 16bit version of <see cref="I.INC"/>
    /// pop: address16bit, push: address16bit
    /// </summary>
    INC16,
    /// <summary>
    /// 16bit version of <see cref="I.DEC"/>
    /// pop: address16bit, push: address16bit
    /// </summary>
    DEC16,
    /// <summary>
    /// Convert 8 bit value to 16 bit
    /// pop: val8bit, push: address16bit
    /// </summary>
    EXTEND,
    /// <summary>
    /// 16bit version of <see cref="I.LOAD_LOCAL"/>
    /// read: offset8bit, push: address16bit
    /// </summary>
    LOAD_LOCAL16,
    /// <summary>
    /// 16bit version of <see cref="I.LOAD_ARG"/>
    /// read: offset8bit, push: address16bit
    /// </summary>
    LOAD_ARG16,
    /// <summary>
    /// 16bit version of <see cref="I.STORE_LOCAL"/>
    /// read: offset8bit, pop: address16bit
    /// </summary>
    STORE_LOCAL16,
    /// <summary>
    /// 16bit version of <see cref="I.STORE_ARG"/>
    /// read: offset8bit, pop: address16bit
    /// </summary>
    STORE_ARG16,
    /// <summary>
    /// 16bit version of <see cref="I.LESS"/>. Note: result is 1 byte.
    /// pop: 2x address16bit, push: val8bit
    /// </summary>
    LESS16,
    /// <summary>
    /// 16bit version of <see cref="I.LESS_OR_EQ"/>. Note: result is 1 byte.
    /// pop: 2x address16bit, push: val8bit
    /// </summary>
    LESS_OR_EQ16,
    /// <summary>
    /// 16bit version of <see cref="I.ZERO"/>. Note: result is 1 byte.
    /// pop: address16bit, push: val8bit
    /// </summary>
    ZERO16,
    /// <summary>
    /// 16bit version of <see cref="I.EQ"/>. Note: result is 1 byte.
    /// pop: 2x address16bit, push: val8bit
    /// </summary>
    EQ16,
    /// <summary>
    /// 16bit version of<see cref="I.DUP"/>
    /// push: address16bit
    /// </summary>
    DUP16,
    /// <summary>
    /// 16-bit version of <see cref="I.SWAP"/> 
    /// </summary>
    SWAP16,

    // NVRAM interface, just like other globals:

    /// <summary>
    /// Load address indicated by the value at the top of the stack
    /// pop: address16bit push: value8bit
    /// </summary>
    LOAD_NVRAM,
    /// <summary>
    /// Store the 8bit value from stack at address
    /// pop: address16bit, value8bit (address on top of stack)
    /// </summary>
    STORE_NVRAM,

    /// <summary>
    /// Stop execution.
    /// </summary>
    HALT = 99
};

enum InterruptCodes
{
    DivisionByZeroError,
    ParseError
};

/// <summary>
/// Standard library call numbers
/// </summary>
enum class Stdlib
{
    /// <summary>
    /// Print 8 bit value as int, does not pop it
    /// </summary>
    PrintInt,
    /// <summary>
    /// Print 16 bit value as int, does not pop it
    /// </summary>
    PrintInt16,
    /// <summary>
    /// Print 8 bit value as char, does not pop it
    /// </summary>
    PrintChar,
    /// <summary>
    /// Print 8 bit value as char
    /// pop: val8bit
    /// </summary>
    PrintCharPop,
    /// <summary>
    /// Prints 0-terminated string from address
    /// pop: address16bit
    /// </summary>
    PrintString,
    /// <summary>
    /// Print new line character
    /// </summary>
    PrintNewLine,
    /// <summary>
    /// read string from command line and copies to address. First arg - target address, second - max number of chars (including 0 terminator), args popped from stack
    /// pop: address16bit, val8bit
    /// </summary>
    ReadString,
    /// <summary>
    /// Read key and push to the stack. Pushes 0 if no key available
    /// push: val8bit
    /// </summary>
    ReadKey,
    /// <summary>
    /// Read left and top position from the stack and set cursor XY location
    /// pop: 2x val8bit
    /// </summary>
    SetConsoleCursorPosition,
    /// <summary>
    /// Pops 0 or 1 from the stack and turns off/on the cursor
    /// pop: val8bit
    /// </summary>
    ShowConsoleCursor,
    /// <summary>
    /// Sets background and foreground colors of the console
    /// pop 2x val8bit
    /// </summary>
    SetConsoleColors,
    /// <summary>
    /// Clear the console, no arguments
    /// </summary>
    ConsoleClear,

    /// <summary>
    /// Read 0-terminated string from address from stack and then pushes int value to the stack. Raises <see cref="InterruptCodes.ParseError"/>
    /// pop: address16bit, push: val8bit
    /// </summary>
    StringToInt,
    /// <summary>
    /// Converts int value to string
    /// Expects 3 values on stack: target address, max number of chars (including 0 terminator), int to convert
    /// pop: address16bit, val8bit, val8bit
    /// </summary>
    IntToString,
    /// <summary>
    /// Copy memory, expects 3 values on stack: source address, target address, length 
    /// pop: address16bit, address16bit, val8bit
    /// </summary>
    MemCpy,
    /// <summary>
    /// Initialize memory with fixed value, expects 3 values: address, length, value
    /// pop: address16bit, address16bit, val8bit
    /// </summary>
    MemSet,
    /// <summary>
    /// swaps 2 chunks of memory, expects 3 values on stack, 2 addresses and length
    /// pop: address16bit, address16bit, val8bit
    /// </summary>
    MemSwap,
    /// <summary>
    /// pushes 0 if 2 chunks of memory are equal, or address where 1st inequality happens in 1st chunk. Expects 2 addresses and length
    /// pop: address16bit, address16bit, val8bit, push: address16bit
    /// </summary>
    MemCmp,
    /// <summary>
    /// pushes length of string at address from stack, does not count null terminator
    /// pop: address16bit push: address16bit
    /// </summary>
    Strlen,
    /// <summary>
    /// Suspends execution for number of milliseconds. Value is 16bit
    /// pop: address16bit
    /// </summary>
    Sleep,
    /// <summary>
    /// Gets the random integer within range using time-based seed.
    /// pop: min and max val8bit, push: val8bit
    /// </summary>
    GetRandomNumber
};

enum class Colors
{
    Black,
    Red,
    Green,
    Yellow,
    Blue,
    Magenta,
    Cyan,
    White,
    BrightBlack,
    BrightRed,
    BrightGreen,
    BrightYellow,
    BrightBlue,
    BrightMagenta,
    BrightCyan,
    BrightWhite,
    Gray,
    BrightGray
};