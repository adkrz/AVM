; Byte a
PUSHN 1
PUSH 5
STORE_LOCAL 0 ; a
:while1_begin
LOAD_LOCAL 0 ; a
SYSCALL Std.PrintInt
POP
LOAD_LOCAL 0 ; a
PUSH 1
SUB2
STORE_LOCAL 0 ; a
LOAD_LOCAL 0 ; a
PUSH 0
LESS_OR_EQ
JT @while1_begin
:while1_endwhile
HALT
