; struct additional zmienna
; Struct zmienna_tablica[]
PUSHN 30
;modify_by_ref(Struct Z)
PUSH_REG 2
PUSH16 #0
ADD16
CALL @function_modify_by_ref
; stack cleanup
POPN 2
PUSH_REG 2
PUSH16 #0
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
;modify_by_ref2(Struct Z[])
LOAD_LOCAL16 28 ; zmienna_tablica
CALL @function_modify_by_ref2
; stack cleanup
POPN 2
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

:function_modify_by_ref
;(Struct Z)
LOAD_ARG 28 ; Z
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
PUSH 5
STORE_GLOBAL2
RET

:function_modify_by_ref2
;(Struct Z[])
PUSH16 #2
PUSH16 #28
MUL16
LOAD_ARG16 28 ; Z
ADD16
PUSH16 #0
PUSH16 #13
MUL16
PUSH16 #0
ADD16
PUSH 6
STORE_GLOBAL2
RET
