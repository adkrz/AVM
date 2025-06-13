; struct additional zmienna
; Struct zmienna_tablica[]
PUSHN 30
CALL @function_modify_by_global
PUSH_REG 2
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
CALL @function_modify_by_global2
LOAD_LOCAL16 28 ; zmienna_tablica
ADD16C #56
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
HALT
:function_modify_by_global
;()
PUSH 5
PUSH_STACK_START
STORE_GLOBAL
RET
:function_modify_by_global2
;()
PUSH 6
PUSH_STACK_START
PUSH16 #28
ADD16
LOAD_GLOBAL16
ADD16C #56
STORE_GLOBAL
RET