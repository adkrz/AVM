; Byte c1
; Byte c2
; Byte result
PUSHN 3
PUSH 1
STORE_LOCAL 0 ; c1
:while1_begin
LOAD_LOCAL 0 ; c1
PUSH 10
GREATER_OR_EQ
JF @while1_endwhile
PUSH 1
STORE_LOCAL 1 ; c2
:while2_begin
LOAD_LOCAL 1 ; c2
PUSH 10
GREATER_OR_EQ
JF @while2_endwhile
LOAD_LOCAL 0 ; c1
LOAD_LOCAL 1 ; c2
MUL
STORE_LOCAL 2 ; result
LOAD_LOCAL 2 ; result
SYSCALL Std.PrintInt
POP
PUSH16 @string_1
SYSCALL Std.PrintString
LOAD_LOCAL 1 ; c2
PUSH 1
ADD
STORE_LOCAL 1 ; c2
JMP @while2_begin
:while2_endwhile
SYSCALL Std.PrintNewLine
LOAD_LOCAL 0 ; c1
PUSH 1
ADD
STORE_LOCAL 0 ; c1
JMP @while1_begin
:while1_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
SYSCALL Std.PrintNewLine
PUSH 1
STORE_LOCAL 0 ; c1
:while3_begin
LOAD_LOCAL 0 ; c1
PUSH 10
GREATER_OR_EQ
JF @while3_endwhile
LOAD_LOCAL 0 ; c1
PUSH 3
EQ
JF @if1_else
LOAD_LOCAL 0 ; c1
PUSH 1
ADD
STORE_LOCAL 0 ; c1
JMP @while3_begin
JMP @if1_endif
:if1_else
:if1_endif
LOAD_LOCAL 0 ; c1
PUSH 8
EQ
JF @if2_else
JMP @while3_endwhile
JMP @if2_endif
:if2_else
:if2_endif
PUSH 1
STORE_LOCAL 1 ; c2
:while4_begin
LOAD_LOCAL 1 ; c2
PUSH 10
GREATER_OR_EQ
JF @while4_endwhile
LOAD_LOCAL 0 ; c1
LOAD_LOCAL 1 ; c2
MUL
STORE_LOCAL 2 ; result
LOAD_LOCAL 2 ; result
SYSCALL Std.PrintInt
POP
PUSH16 @string_1
SYSCALL Std.PrintString
LOAD_LOCAL 1 ; c2
PUSH 1
ADD
STORE_LOCAL 1 ; c2
JMP @while4_begin
:while4_endwhile
SYSCALL Std.PrintNewLine
LOAD_LOCAL 0 ; c1
PUSH 1
ADD
STORE_LOCAL 0 ; c1
JMP @while3_begin
:while3_endwhile
HALT

:string_1
" "
:string_2
"Now skip some rows!"