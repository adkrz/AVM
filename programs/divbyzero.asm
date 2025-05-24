; Shows catching error from division by zero

INTERRUPT_HANDLER Int.DivisionByZeroError @err
PUSH 0
PUSH 1
DIV
PUSH 222
PUSH Std.PrintInt SYSCALL2
SYSCALL Std.PrintNewLine
HALT
:err
PUSH16 @data
SYSCALL Std.PrintString
RET
HALT
:data
"division by zero!\n"