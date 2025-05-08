PUSHN 1 ; Byte X
PUSH 6
STORE_LOCAL 0 ; X
;fibonacci(Byte X, Byte ret&)
LOAD_LOCAL 0 ; X
LOAD_LOCAL 0 ; X
CALL @function_fibonacci
; stack cleanup
STORE_LOCAL 0 ; X
POPN 1
LOAD_LOCAL 0 ; X
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
HALT

:function_fibonacci
;(Byte X, Byte ret&)
; Byte A
; Byte B
PUSHN 2
LOAD_ARG 2 ; X
PUSH 0
EQ
JF @if1_else
PUSH 0
STORE_ARG 1 ; ret
RET
JMP @if1_endif
:if1_else
:if1_endif
LOAD_ARG 2 ; X
PUSH 1
EQ
JF @if2_else
PUSH 1
STORE_ARG 1 ; ret
RET
JMP @if2_endif
:if2_else
:if2_endif
PUSH 0
STORE_LOCAL 0 ; A
PUSH 0
STORE_LOCAL 1 ; B
;fibonacci(Byte X, Byte ret&)
LOAD_ARG 2 ; X
PUSH 2
SUB2
LOAD_LOCAL 0 ; A
CALL @function_fibonacci
; stack cleanup
STORE_LOCAL 0 ; A
POPN 1
;fibonacci(Byte X, Byte ret&)
LOAD_ARG 2 ; X
PUSH 1
SUB2
LOAD_LOCAL 1 ; B
CALL @function_fibonacci
; stack cleanup
STORE_LOCAL 1 ; B
POPN 1
LOAD_LOCAL 0 ; A
LOAD_LOCAL 1 ; B
ADD
STORE_ARG 1 ; ret
RET
