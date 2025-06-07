; Byte string[]
; Byte index
; Byte char
PUSHN 4
PUSH 84
SYSCALL Std.PrintCharPop
PUSH 69
SYSCALL Std.PrintCharPop
PUSH 83
SYSCALL Std.PrintCharPop
PUSH 84
SYSCALL Std.PrintCharPop
PUSH 10
SYSCALL Std.PrintCharPop
PUSH16 @string_1
STORE_LOCAL16 0 ; string
PUSH 0
STORE_LOCAL 2 ; index
:while1_begin
PUSH 1
JF @while1_endwhile
LOAD_LOCAL16 0 ; string
LOAD_LOCAL 2 ; index
EXTEND
ADD16
LOAD_GLOBAL
STORE_LOCAL 3 ; char
LOAD_LOCAL 3 ; char
PUSH 0
EQ
JF @if1_endif
JMP @while1_endwhile
:if1_endif
LOAD_LOCAL 3 ; char
SYSCALL Std.PrintCharPop
LOAD_LOCAL 2 ; index
PUSH 1
ADD
STORE_LOCAL 2 ; index
JMP @while1_begin
:while1_endwhile
SYSCALL Std.PrintNewLine
HALT

:string_1
"hello world"