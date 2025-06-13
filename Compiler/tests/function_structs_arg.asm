; struct additional zmienna
; Struct zmienna_tablica[]
; Addr index
PUSHN 32
PUSH_REG 2
CALL @function_modify_by_ref
POPN 2
PUSH_REG 2
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
LOAD_LOCAL16 28 ; zmienna_tablica
CALL @function_modify_by_ref2
POPN 2
PUSH16 #2
STORE_LOCAL16 56 ; index
LOAD_LOCAL16 28 ; zmienna_tablica
LOAD_LOCAL16 56 ; index
MUL16C #28
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
HALT
:function_modify_by_ref
;(Struct Z)
PUSH 5
LOAD_ARG16 2 ; Z
STORE_GLOBAL
RET
:function_modify_by_ref2
;(Struct Z[])
PUSH 6
LOAD_ARG16 2 ; Z
ADD16C #56
STORE_GLOBAL
RET