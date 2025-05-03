PUSHN 1 ; Byte a
PUSH 1
STORE_LOCAL 0 ; a
;func()
CALL @function_func
; stack cleanup
LOAD_LOCAL 0 ; a
PUSH 4
EQ
DUP
JF @cond1_expr_end
LOAD_LOCAL 0 ; a
PUSH 0
LESS_OR_EQ
AND
:cond1_expr_end
JF @if1_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if1_endif
:if1_else
:if1_endif
HALT

:function_func
;()
PUSH_STACK_START
LOAD_GLOBAL
PUSH 3
ADD
PUSH_STACK_START
STORE_GLOBAL
RET

:string_1
"OK!"