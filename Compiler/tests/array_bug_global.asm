PUSHN 2
PUSH_REG 1
STORE_LOCAL16 0
PUSH 0
CALL @function_print_sudoku
HALT
:function_print_sudoku
PUSHN 2
PUSH 0
STORE_LOCAL 0
:while1_begin
LOAD_LOCAL 0
PUSH 9
GREATER
JF @while1_endwhile
PUSH 0
STORE_LOCAL 1
:while2_begin
LOAD_LOCAL 1
PUSH 9
GREATER
JF @while2_endwhile
LOAD_LOCAL 1
SYSCALL Std.PrintInt
POP
PUSH 32
SYSCALL Std.PrintCharPop
MACRO_INC_LOCAL 1
JMP @while2_begin
:while2_endwhile
SYSCALL Std.PrintNewLine
MACRO_INC_LOCAL 0
JMP @while1_begin
:while1_endwhile
RET