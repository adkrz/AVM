PUSHN 5
PUSH 3
PUSH 2
LSH
PUSH 12
EQ
JF @if1_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if1_endif
PUSH 12
PUSH 1
RSH
PUSH 6
EQ
JF @if2_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if2_endif
PUSH 12
PUSH 1
RSH
PUSH 5
OR
PUSH 7
EQ
JF @if3_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if3_endif
PUSH 12
PUSH 1
RSH
PUSH 5
AND
PUSH 4
EQ
JF @if4_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if4_endif
PUSH 12
PUSH 1
RSH
PUSH 5
XOR
PUSH 3
EQ
JF @if5_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if5_endif
SYSCALL Std.PrintNewLine
PUSH 3
STORE_LOCAL 0
PUSH16 #1
LOAD_LOCAL 0
MACRO_LSH16_BY8
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
PUSH_REG 1
STORE_LOCAL16 1
PUSH 3
PUSH 4
PUSH 5
PUSH16 #1
LOAD_LOCAL16 1
INC16
LOAD_GLOBAL
MACRO_LSH16_BY8
STORE_LOCAL16 3
LOAD_LOCAL16 3
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
LOAD_LOCAL16 3
FLIP16
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
PUSH16 #1
LOAD_LOCAL16 1
ADD16C #2
LOAD_GLOBAL
MACRO_LSH16_BY8
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
HALT
HALT
:string_1
"OK\n"