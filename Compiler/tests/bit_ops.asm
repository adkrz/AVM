PUSHN 7
PUSH 3
PUSH 2
LSH
PUSH 12
EQ
JF @if1_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if1_endif
:if1_else
:if1_endif
PUSH 12
PUSH 1
RSH
PUSH 6
EQ
JF @if2_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if2_endif
:if2_else
:if2_endif
PUSH 12
PUSH 1
RSH
PUSH 5
OR
PUSH 7
EQ
JF @if3_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if3_endif
:if3_else
:if3_endif
PUSH 12
PUSH 1
RSH
PUSH 5
AND
PUSH 4
EQ
JF @if4_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if4_endif
:if4_else
:if4_endif
PUSH 12
PUSH 1
RSH
PUSH 5
XOR
PUSH 3
EQ
JF @if5_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if5_endif
:if5_else
:if5_endif
SYSCALL Std.PrintNewLine
PUSH 3
STORE_LOCAL 0
PUSH16 #1
LOAD_LOCAL 0
EXTEND
LSH16
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
EXTEND
LSH16
STORE_LOCAL16 5
LOAD_LOCAL16 5
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
HALT
HALT
:string_1
"OK\n"