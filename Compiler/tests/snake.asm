PUSHN 10
PUSH 0
SYSCALL Std.ShowConsoleCursor
SYSCALL Std.ConsoleClear
PUSH 1
STORE_LOCAL 0
PUSH16 #5
STORE_LOCAL16 1
PUSH 24
STORE_LOCAL 3
PUSH 10
STORE_LOCAL 4
PUSH 0
STORE_LOCAL 5
PUSH 0
STORE_LOCAL 6
CALL @function_clear_memory
CALL @function_draw_borders
CALL @function_write_initial_body
LOAD_LOCAL16 1
CALL @function_redraw
POPN 2
:while10_begin
SYSCALL Std.ReadKey
STORE_LOCAL 9
LOAD_LOCAL 9
JF @if19_else
LOAD_LOCAL 9
LOAD_LOCAL 0
CALL @function_new_direction
STORE_LOCAL 0
POPN 1
JMP @if19_endif
:if19_else
:if19_endif
LOAD_LOCAL 3
LOAD_LOCAL 4
LOAD_LOCAL 0
CALL @function_next_head_position
POPN 1
STORE_LOCAL 4
STORE_LOCAL 3
LOAD_LOCAL 3
PUSH 1
GREATER_OR_EQ
DUP
JT @cond1_expr_end
LOAD_LOCAL 4
ZERO
OR
DUP
JT @cond1_expr_end
LOAD_LOCAL 3
PUSH 50
EQ
OR
DUP
JT @cond1_expr_end
LOAD_LOCAL 4
PUSH 22
EQ
OR
:cond1_expr_end
JF @if20_else
JMP @while10_endwhile
JMP @if20_endif
:if20_else
:if20_endif
LOAD_LOCAL 3
LOAD_LOCAL 4
LOAD_LOCAL16 7
CALL @function_xy_to_mem_loc
STORE_LOCAL16 7
POPN 2
LOAD_LOCAL16 7
LOAD_GLOBAL16
JF16 @if21_else
JMP @while10_endwhile
JMP @if21_endif
:if21_else
:if21_endif
LOAD_LOCAL 3
LOAD_LOCAL 5
EQ
DUP
JF @cond2_expr_end
LOAD_LOCAL 4
LOAD_LOCAL 6
EQ
AND
:cond2_expr_end
JF @if22_else
MACRO_INC_LOCAL16 1
PUSH 0
STORE_LOCAL 5
PUSH 55
PUSH 22
PUSH 2
DIV2
SYSCALL Std.SetConsoleCursorPosition
LOAD_LOCAL16 1
PUSH16 #5
SUB216
SYSCALL Std.PrintInt16
POPN 2
JMP @if22_endif
:if22_else
:if22_endif
LOAD_LOCAL16 7
LOAD_LOCAL16 1
INC16
STORE_GLOBAL216
LOAD_LOCAL 5
ZERO
JF @if23_else
LOAD_LOCAL 5
LOAD_LOCAL 6
CALL @function_random_fruit_position
STORE_LOCAL 6
STORE_LOCAL 5
LOAD_LOCAL 5
LOAD_LOCAL 6
CALL @function_draw_fruit
POPN 2
JMP @if23_endif
:if23_else
:if23_endif
CALL @function_move_body
LOAD_LOCAL 3
LOAD_LOCAL 4
SYSCALL Std.SetConsoleCursorPosition
CALL @function_draw_head
PUSH16 #200
SYSCALL Std.Sleep
JMP @while10_begin
:while10_endwhile
PUSH 50
PUSH 22
SYSCALL Std.SetConsoleCursorPosition
SYSCALL Std.PrintNewLine
SYSCALL Std.PrintNewLine
HALT
:function_xy_to_mem_loc
PUSH16 #10000
LOAD_ARG 3
EXTEND
DEC16
MUL16C #98
ADD16
LOAD_ARG 4
EXTEND
DEC16
MUL16C #2
ADD16
STORE_ARG16 2
RET
:function_clear_memory
PUSHN 2
PUSH 50
PUSH 22
LOAD_LOCAL16 0
CALL @function_xy_to_mem_loc
STORE_LOCAL16 0
POPN 2
:while1_begin
LOAD_LOCAL16 0
PUSH16 #0
STORE_GLOBAL216
MACRO_DEC_LOCAL16 0
LOAD_LOCAL16 0
PUSH16 #10000
LESS_OR_EQ16
JT @while1_begin
RET
:function_draw_borders
PUSHN 1
PUSH 0
PUSH 16
SYSCALL Std.SetConsoleColors
PUSH 50
STORE_LOCAL 0
:while2_begin
LOAD_LOCAL 0
PUSH 0
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
LOAD_LOCAL 0
PUSH 22
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
MACRO_DEC_LOCAL 0
LOAD_LOCAL 0
ZERO
JF @if1_else
JMP @while2_endwhile
JMP @if1_endif
:if1_else
:if1_endif
JMP @while2_begin
:while2_endwhile
PUSH 22
STORE_LOCAL 0
:while3_begin
PUSH 1
LOAD_LOCAL 0
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
PUSH 50
LOAD_LOCAL 0
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
MACRO_DEC_LOCAL 0
LOAD_LOCAL 0
ZERO
JF @if2_else
JMP @while3_endwhile
JMP @if2_endif
:if2_else
:if2_endif
JMP @while3_begin
:while3_endwhile
RET
:function_write_initial_body
PUSHN 5
PUSH 20
STORE_LOCAL 0
PUSH 10
STORE_LOCAL 1
PUSH 0
STORE_LOCAL 2
:while4_begin
LOAD_LOCAL 2
PUSH 5
GREATER
JF @while4_endwhile
LOAD_LOCAL 0
LOAD_LOCAL 1
LOAD_LOCAL16 3
CALL @function_xy_to_mem_loc
STORE_LOCAL16 3
POPN 2
LOAD_LOCAL16 3
LOAD_LOCAL 2
EXTEND
INC16
STORE_GLOBAL216
MACRO_INC_LOCAL 2
MACRO_INC_LOCAL 0
JMP @while4_begin
:while4_endwhile
RET
:function_redraw
PUSHN 6
PUSH 49
STORE_LOCAL 0
:while5_begin
PUSH 21
STORE_LOCAL 1
:while6_begin
LOAD_LOCAL 0
LOAD_LOCAL 1
LOAD_LOCAL16 2
CALL @function_xy_to_mem_loc
STORE_LOCAL16 2
POPN 2
LOAD_LOCAL16 2
LOAD_GLOBAL16
STORE_LOCAL16 4
LOAD_LOCAL 0
LOAD_LOCAL 1
SYSCALL Std.SetConsoleCursorPosition
LOAD_LOCAL16 4
ZERO16
JF @if3_else
PUSH 32
SYSCALL Std.PrintCharPop
JMP @if3_endif
:if3_else
LOAD_LOCAL16 4
LOAD_ARG16 2
EQ16
JF @if4_else
CALL @function_draw_head
JMP @if4_endif
:if4_else
PUSH 111
SYSCALL Std.PrintCharPop
:if4_endif
:if3_endif
MACRO_DEC_LOCAL 1
LOAD_LOCAL 1
ZERO
JF @if5_else
JMP @while6_endwhile
JMP @if5_endif
:if5_else
:if5_endif
JMP @while6_begin
:while6_endwhile
MACRO_DEC_LOCAL 0
LOAD_LOCAL 0
PUSH 1
EQ
JF @if6_else
JMP @while5_endwhile
JMP @if6_endif
:if6_else
:if6_endif
JMP @while5_begin
:while5_endwhile
RET
:function_draw_head
PUSH 0
PUSH 3
SYSCALL Std.SetConsoleColors
PUSH 79
SYSCALL Std.PrintCharPop
PUSH 0
PUSH 15
SYSCALL Std.SetConsoleColors
RET
:function_draw_fruit
LOAD_ARG 2
LOAD_ARG 1
SYSCALL Std.SetConsoleCursorPosition
PUSH 10
PUSH 15
SYSCALL Std.SetConsoleColors
PUSH 37
SYSCALL Std.PrintCharPop
PUSH 0
PUSH 15
SYSCALL Std.SetConsoleColors
RET
:function_new_direction
LOAD_ARG 2
PUSH 119
EQ
JF @if7_else
PUSH 3
STORE_ARG 1
JMP @if7_endif
:if7_else
LOAD_ARG 2
PUSH 115
EQ
JF @if8_else
PUSH 4
STORE_ARG 1
JMP @if8_endif
:if8_else
LOAD_ARG 2
PUSH 97
EQ
JF @if9_else
PUSH 2
STORE_ARG 1
JMP @if9_endif
:if9_else
LOAD_ARG 2
PUSH 100
EQ
JF @if10_else
PUSH 1
STORE_ARG 1
JMP @if10_endif
:if10_else
:if10_endif
:if9_endif
:if8_endif
:if7_endif
RET
:function_next_head_position
LOAD_ARG 1
PUSH 3
EQ
JF @if11_else
LOAD_ARG 2
DEC
STORE_ARG 2
JMP @if11_endif
:if11_else
LOAD_ARG 1
PUSH 4
EQ
JF @if12_else
LOAD_ARG 2
INC
STORE_ARG 2
JMP @if12_endif
:if12_else
LOAD_ARG 1
PUSH 2
EQ
JF @if13_else
LOAD_ARG 3
DEC
STORE_ARG 3
JMP @if13_endif
:if13_else
LOAD_ARG 1
PUSH 1
EQ
JF @if14_else
LOAD_ARG 3
INC
STORE_ARG 3
JMP @if14_endif
:if14_else
:if14_endif
:if13_endif
:if12_endif
:if11_endif
RET
:function_random_fruit_position
PUSHN 2
:while7_begin
PUSH 2
PUSH 49
PUSH 2
PUSH 49
SYSCALL Std.GetRandomNumber
STORE_ARG 2
PUSH 1
PUSH 21
PUSH 1
PUSH 21
SYSCALL Std.GetRandomNumber
STORE_ARG 1
LOAD_ARG 2
LOAD_ARG 1
LOAD_LOCAL16 0
CALL @function_xy_to_mem_loc
STORE_LOCAL16 0
POPN 2
LOAD_LOCAL16 0
LOAD_GLOBAL16
PUSH16 #0
LESS16
JT @while7_begin
RET
:function_move_body
PUSHN 6
PUSH 21
STORE_LOCAL 0
:while8_begin
PUSH 49
STORE_LOCAL 3
LOAD_LOCAL 3
LOAD_LOCAL 0
LOAD_LOCAL16 1
CALL @function_xy_to_mem_loc
STORE_LOCAL16 1
POPN 2
:while9_begin
LOAD_LOCAL16 1
LOAD_GLOBAL16
STORE_LOCAL16 4
LOAD_LOCAL16 4
PUSH16 #0
LESS16
JF @if15_else
LOAD_LOCAL 3
LOAD_LOCAL 0
SYSCALL Std.SetConsoleCursorPosition
MACRO_DEC_LOCAL16 4
LOAD_LOCAL16 4
ZERO16
JF @if16_else
PUSH 32
SYSCALL Std.PrintCharPop
JMP @if16_endif
:if16_else
PUSH 111
SYSCALL Std.PrintCharPop
:if16_endif
LOAD_LOCAL16 1
LOAD_LOCAL16 4
STORE_GLOBAL216
JMP @if15_endif
:if15_else
:if15_endif
MACRO_DEC_LOCAL 3
LOAD_LOCAL16 1
PUSH16 #2
SUB216
STORE_LOCAL16 1
LOAD_LOCAL 3
PUSH 1
EQ
JF @if17_else
JMP @while9_endwhile
JMP @if17_endif
:if17_else
:if17_endif
JMP @while9_begin
:while9_endwhile
MACRO_DEC_LOCAL 0
LOAD_LOCAL 0
ZERO
JF @if18_else
JMP @while8_endwhile
JMP @if18_endif
:if18_else
:if18_endif
JMP @while8_begin
:while8_endwhile
RET