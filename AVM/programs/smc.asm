; Self modifying code example
; Prints "42" by preparing the code on stack and jumping to it
PUSH_NEXT_SP
PUSH PUSH ; we can push opcodes, because why not ;)
PUSH 42
PUSH SYSCALL
PUSH Std.PrintInt ; syscall codes will be output as well, there is no special syntax checking in compiler for that
PUSH SYSCALL
PUSH Std.PrintNewLine
PUSH HALT
LOAD_LOCAL16 0
JMP2
HALT