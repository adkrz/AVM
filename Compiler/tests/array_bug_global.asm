; Byte mat[]
PUSHN 2
PUSH_REG 1
STORE_LOCAL16 0 ; mat
PUSH 0
CALL @function_print_sudoku
HALT
:function_print_sudoku
;()
; Byte r
; Byte c
PUSHN 2
MACRO_SET_LOCAL 0 0
:while1_begin
LOAD_LOCAL 0 ; r
PUSH 9
MACRO_CONDITIONAL_JF 4 @while1_endwhile
MACRO_SET_LOCAL 1 0
:while2_begin
LOAD_LOCAL 1 ; c
PUSH 9
MACRO_CONDITIONAL_JF 4 @while2_endwhile
LOAD_LOCAL 1 ; c
SYSCALL Std.PrintInt
POP
PUSH 32
SYSCALL Std.PrintCharPop
MACRO_INC_LOCAL 1 ;c
JMP @while2_begin
:while2_endwhile
SYSCALL Std.PrintNewLine
MACRO_INC_LOCAL 0 ;r
JMP @while1_begin
:while1_endwhile
RET