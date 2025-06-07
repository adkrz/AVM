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
LESS
AND
:cond1_expr_end
JF @if1_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if1_endif
SYSCALL Std.PrintNewLine
LOAD_LOCAL 0 ; a
PUSH 4
EQ
JF @if2_endif
LOAD_LOCAL 0 ; a
PUSH 0
LESS
JF @if3_endif
PUSH16 @string_2
SYSCALL Std.PrintString
:if3_endif
:if2_endif
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
:string_2
"OK2!"