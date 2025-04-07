; Self modifying code example 2
; Program searches its own memory to replace constant
:begin
PUSH16 @str1
SYSCALL Std.PrintString
PUSH 41
SYSCALL Std.PrintInt
SYSCALL Std.PrintNewLine
POP
:jmp_instr
JMP @patch

:patch
PUSH16 #0
:find_constant
DUP16
LOAD_GLOBAL
PUSH 41
EQ
JT @do_patch
INC16
JMP @find_constant

:do_patch
PUSH 42
LOAD_LOCAL16 0
STORE_GLOBAL
; patch the "jmp @patch" with halt to avoid infinite loop
PUSH16 @exit
PUSH16 @jmp_instr
INC16
STORE_GLOBAL16
; restart the program
JMP #0

:exit
HALT

:str1
"The constant is "