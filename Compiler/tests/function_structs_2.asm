; struct point3d pt
PUSHN 3
PUSH 11
PUSH_REG 2
STORE_GLOBAL
PUSH 22
PUSH_REG 2
ADD16C #1
STORE_GLOBAL
PUSH 33
PUSH_REG 2
ADD16C #2
STORE_GLOBAL
PUSH_REG 2
CALL @function_printpt
POPN 2
PUSH_REG 2
CALL @function_setxy_only
POPN 2
PUSH_REG 2
CALL @function_printpt
POPN 2
HALT
:function_printpt
;(Struct pt)
PUSH16 @string_1
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
PUSH16 @string_2
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
ADD16C #1
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
PUSH16 @string_3
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
ADD16C #2
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
RET
:function_setxy_only
;(Struct pt)
PUSH 44
LOAD_ARG16 2 ; pt
STORE_GLOBAL
PUSH 55
LOAD_ARG16 2 ; pt
ADD16C #1
STORE_GLOBAL
RET
:string_1
"X="
:string_2
" Y="
:string_3
" Z="