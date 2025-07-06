#pragma once
enum I
{
    /// <summary>
    /// No operation
    /// </summary>
    NOP,

    // byte reg_count
    NEW_FRAME,

    // reg_no, int32
    MOV_RI,
    // destination reg no, src reg no
    MOV_RR,

    //MOV_MR,
    //MOV_RM,
    //MOV_MM,
    //MOV8_MR,
    //MOV8_RM,
    
    //LEA,

    // reg no, int32
    ADD_RI,
    // reg no, byte
    ADD_RI8,
    // destination reg no, src reg no
    ADD_RR,

    // label
    JMP,
    // reg no with address
    JMP_R,
    // reg no, label
    JF,
    // reg no, reg no with address
    JF_R,
    // reg no, label
    JT,
    // reg no, reg no with address
    JT_R,

    // arg: label of function
    // prepare next stack frame, but does not execute anything
    // If function starts with NEW_FRAME, uses this information
    PREPARE_CALL,
    // reg no containing funcion address
    PREPARE_CALL_R,
    // no args -> everything done in PREPARE_CALL
    CALL,
    // copy local registers to prepared frame
    // args: local reg no, function reg no
    COPY_TO_FUNC,
    // write constant value to prepared function frame
    // function reg no, int32
    COPY_CONST_TO_FUNC,
    // after function return: copy data (e.g. ret value) from function regs back to us
    // function reg no, local reg no
    COPY_FROM_FUNC,
    // Restore previous stack frame. The old prepared frame is still available and can be reached via COPY_FROM_FUNC
    // no args
    RET,
    
    HALT,
    PRINT_FRAMES
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