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
JF @if1_else
PUSH16 @string_1
SYSCALL Std.PrintString
JMP @if1_endif
:if1_else
:if1_endif
SYSCALL Std.PrintNewLine
LOAD_LOCAL 0 ; a
PUSH 4
EQ
JF @if2_else
LOAD_LOCAL 0 ; a
PUSH 0
LESS
JF @if3_else
PUSH16 @string_2
SYSCALL Std.PrintString
JMP @if3_endif
:if3_else
:if3_endif
JMP @if2_endif
:if2_else
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