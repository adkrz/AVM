PUSHN 28 ; struct additional zmienna
PUSHN 2 ; Struct zmienna_tablica[]
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
PUSH_NEXT_SP
PUSH16 #2
SUB216
STORE_LOCAL16 28 ; zmienna_tablica
PUSH 5
PUSH 28
MUL
PUSHN2 ; zmienna_tablica alloc
;modify_by_global2()
CALL @function_modify_by_global2
; stack cleanup
PUSH16 #2
PUSH16 #28
MUL16
LOAD_LOCAL16 28 ; zmienna_tablica
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

:function_modify_by_global2
;()
PUSH16 #2
PUSH16 #28
MUL16
PUSH_STACK_START
#28
ADD16
LOAD_GLOBAL16
ADD16
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
PUSH 6
ROLL3
STORE_GLOBAL
RET