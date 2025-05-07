PUSHN 28 ; struct additional zmienna
;modify_by_ref(Struct Z)
LOAD_LOCAL 0 ; zmienna
CALL @function_modify_by_ref
; stack cleanup
STORE_LOCAL 0 ; zmienna
PUSH_REG 2
PUSH16 #0 ; struct additional
ADD16
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
HALT

:function_modify_by_ref
;(Struct Z)
LOAD_ARG 28 ; Z
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
PUSH 5
ROLL3
STORE_GLOBAL
RET
