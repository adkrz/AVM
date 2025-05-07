PUSHN 28 ; struct additional zmienna
;modify_by_global()
CALL @function_modify_by_global
; stack cleanup
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

:function_modify_by_global
;()
PUSH_STACK_START
PUSH16 #0 ; struct additional
ADD16
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
PUSH 5
ROLL3
STORE_GLOBAL
RET
