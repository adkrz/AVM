; Byte result
PUSHN 1
;fibonacci(Byte @ret&, Byte X)
PUSH 0 ; rv
PUSH 6
CALL @function_fibonacci
; stack cleanup
POPN 1
STORE_LOCAL 0 ; result
LOAD_LOCAL 0 ; result
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
HALT

:function_fibonacci
;(Byte @ret&, Byte X)
LOAD_ARG 1 ; X
PUSH 0
EQ
JF @if1_else
PUSH 0
STORE_ARG 2 ; @ret
RET
JMP @if1_endif
:if1_else
LOAD_ARG 1 ; X
PUSH 1
EQ
JF @if2_endif
PUSH 1
STORE_ARG 2 ; @ret
RET
JMP @if2_endif
:if2_endif
:if1_endif
;fibonacci(Byte @ret&, Byte X)
PUSH 0 ; rv
LOAD_ARG 1 ; X
PUSH 2
SUB2
CALL @function_fibonacci
; stack cleanup
POPN 1
;fibonacci(Byte @ret&, Byte X)
PUSH 0 ; rv
LOAD_ARG 1 ; X
PUSH 1
SUB2
CALL @function_fibonacci
; stack cleanup
POPN 1
ADD
STORE_ARG 2 ; @ret
RET
RET
