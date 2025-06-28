; Byte direction
; Addr length
; Byte head_x
; Byte head_y
; Byte fruit_x
; Byte fruit_y
; Addr mem_ptr[]
; Byte key
PUSHN 10
PUSH 0
SYSCALL Std.ShowConsoleCursor
SYSCALL Std.ConsoleClear
MACRO_SET_LOCAL 0 1 ;direction
MACRO_SET_LOCAL16 1 #5 ;length
MACRO_SET_LOCAL 3 24 ;head_x
MACRO_SET_LOCAL 4 10 ;head_y
MACRO_SET_LOCAL 5 0 ;fruit_x
MACRO_SET_LOCAL 6 0 ;fruit_y
CALL @function_clear_memory
CALL @function_draw_borders
CALL @function_write_initial_body
LOAD_LOCAL16 1 ; length
CALL @function_redraw
POPN 2
:while10_begin
SYSCALL Std.ReadKey
STORE_LOCAL_KEEP 9 ; key
JF @if19_endif
LOAD_LOCAL 9 ; key
LOAD_LOCAL 0 ; direction
CALL @function_new_direction
STORE_LOCAL 0 ; direction
POPN 1
:if19_endif
LOAD_LOCAL 3 ; head_x
LOAD_LOCAL 4 ; head_y
LOAD_LOCAL 0 ; direction
CALL @function_next_head_position
POPN 1
STORE_LOCAL 4 ; head_y
STORE_LOCAL_KEEP 3 ; head_x
PUSH 1
GREATER_OR_EQ
DUP
JT @cond1_expr_end
LOAD_LOCAL 4 ; head_y
ZERO
OR
DUP
JT @cond1_expr_end
LOAD_LOCAL 3 ; head_x
PUSH 50
EQ
OR
DUP
JT @cond1_expr_end
LOAD_LOCAL 4 ; head_y
PUSH 22
EQ
OR
:cond1_expr_end
JF @if20_endif
JMP @while10_endwhile
:if20_endif
LOAD_LOCAL 3 ; head_x
LOAD_LOCAL 4 ; head_y
LOAD_LOCAL16 7 ; mem_ptr
CALL @function_xy_to_mem_loc
STORE_LOCAL16 7 ; mem_ptr
POPN 2
LOAD_LOCAL16 7 ; mem_ptr
LOAD_GLOBAL16
JF16 @if21_endif
JMP @while10_endwhile
:if21_endif
LOAD_LOCAL 3 ; head_x
LOAD_LOCAL 5 ; fruit_x
EQ
DUP
JF @cond2_expr_end
LOAD_LOCAL 4 ; head_y
LOAD_LOCAL 6 ; fruit_y
EQ
AND
:cond2_expr_end
JF @if22_endif
MACRO_INC_LOCAL16 1 ;length
MACRO_SET_LOCAL 5 0 ;fruit_x
PUSH 55
PUSH 11
SYSCALL Std.SetConsoleCursorPosition
LOAD_LOCAL16 1 ; length
SUB16C #5
SYSCALL Std.PrintInt16
POPN 2
:if22_endif
LOAD_LOCAL16 1 ; length
INC16
LOAD_LOCAL16 7 ; mem_ptr
STORE_GLOBAL16
LOAD_LOCAL 5 ; fruit_x
MACRO_CONDITIONAL_JF 6 @if23_endif
LOAD_LOCAL 5 ; fruit_x
LOAD_LOCAL 6 ; fruit_y
CALL @function_random_fruit_position
STORE_LOCAL 6 ; fruit_y
STORE_LOCAL_KEEP 5 ; fruit_x
LOAD_LOCAL 6 ; fruit_y
CALL @function_draw_fruit
POPN 2
:if23_endif
CALL @function_move_body
LOAD_LOCAL 3 ; head_x
LOAD_LOCAL 4 ; head_y
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
;(Byte x, Byte y, Addr loc&)
LOAD_ARG 3 ; y
EXTEND
DEC16
MUL16C #98
ADD16C #10000
LOAD_ARG 4 ; x
EXTEND
DEC16
MACRO_X216
ADD16
STORE_ARG16 2 ; loc
RET
:function_clear_memory
;()
; Addr endloc[]
PUSHN 2
PUSH 50
PUSH 22
LOAD_LOCAL16 0 ; endloc
CALL @function_xy_to_mem_loc
STORE_LOCAL16 0 ; endloc
POPN 2
:while1_begin
PUSH16 #0
LOAD_LOCAL16 0 ; endloc
STORE_GLOBAL16
MACRO_DEC_LOCAL16 0 ;endloc
LOAD_LOCAL16 0 ; endloc
PUSH16 #10000
LESS_OR_EQ16
JT @while1_begin
:while1_endwhile
RET
:function_draw_borders
;()
; Byte w
PUSHN 1
PUSH 0
PUSH 16
SYSCALL Std.SetConsoleColors
MACRO_SET_LOCAL 0 50 ;w
:while2_begin
LOAD_LOCAL 0 ; w
PUSH 0
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
LOAD_LOCAL 0 ; w
PUSH 22
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
MACRO_DEC_LOCAL 0 ;w
LOAD_LOCAL 0 ; w
MACRO_CONDITIONAL_JF 6 @if1_endif
JMP @while2_endwhile
:if1_endif
JMP @while2_begin
:while2_endwhile
MACRO_SET_LOCAL 0 22 ;w
:while3_begin
PUSH 1
LOAD_LOCAL 0 ; w
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
PUSH 50
LOAD_LOCAL 0 ; w
SYSCALL Std.SetConsoleCursorPosition
PUSH 35
SYSCALL Std.PrintCharPop
MACRO_DEC_LOCAL 0 ;w
LOAD_LOCAL 0 ; w
MACRO_CONDITIONAL_JF 6 @if2_endif
JMP @while3_endwhile
:if2_endif
JMP @while3_begin
:while3_endwhile
RET
:function_write_initial_body
;()
; Byte X
; Byte Y
; Byte L
; Addr loc[]
PUSHN 5
MACRO_SET_LOCAL 0 20 ;X
MACRO_SET_LOCAL 1 10 ;Y
MACRO_SET_LOCAL 2 0 ;L
:while4_begin
LOAD_LOCAL 2 ; L
PUSH 5
MACRO_CONDITIONAL_JF 4 @while4_endwhile
LOAD_LOCAL 0 ; X
LOAD_LOCAL 1 ; Y
LOAD_LOCAL16 3 ; loc
CALL @function_xy_to_mem_loc
STORE_LOCAL16 3 ; loc
POPN 2
LOAD_LOCAL 2 ; L
EXTEND
INC16
LOAD_LOCAL16 3 ; loc
STORE_GLOBAL16
MACRO_INC_LOCAL 2 ;L
MACRO_INC_LOCAL 0 ;X
JMP @while4_begin
:while4_endwhile
RET
:function_redraw
;(Addr current_length)
; Byte X
; Byte Y
; Addr loc[]
; Addr value
PUSHN 6
MACRO_SET_LOCAL 0 49 ;X
:while5_begin
MACRO_SET_LOCAL 1 21 ;Y
:while6_begin
LOAD_LOCAL 0 ; X
LOAD_LOCAL 1 ; Y
LOAD_LOCAL16 2 ; loc
CALL @function_xy_to_mem_loc
STORE_LOCAL16 2 ; loc
POPN 2
LOAD_LOCAL16 2 ; loc
LOAD_GLOBAL16
STORE_LOCAL16 4 ; value
LOAD_LOCAL 0 ; X
LOAD_LOCAL 1 ; Y
SYSCALL Std.SetConsoleCursorPosition
LOAD_LOCAL16 4 ; value
ZERO16
JF @if3_else
PUSH 32
SYSCALL Std.PrintCharPop
JMP @if3_endif
:if3_else
LOAD_LOCAL16 4 ; value
LOAD_ARG16 2 ; current_length
EQ16
JF @if4_else
CALL @function_draw_head
JMP @if4_endif
:if4_else
PUSH 111
SYSCALL Std.PrintCharPop
:if4_endif
:if3_endif
MACRO_DEC_LOCAL 1 ;Y
LOAD_LOCAL 1 ; Y
MACRO_CONDITIONAL_JF 6 @if5_endif
JMP @while6_endwhile
:if5_endif
JMP @while6_begin
:while6_endwhile
MACRO_DEC_LOCAL 0 ;X
LOAD_LOCAL 0 ; X
PUSH 1
MACRO_CONDITIONAL_JF 0 @if6_endif
JMP @while5_endwhile
:if6_endif
JMP @while5_begin
:while5_endwhile
RET
:function_draw_head
;()
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
;(Byte X, Byte Y)
LOAD_ARG 2 ; X
LOAD_ARG 1 ; Y
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
;(Byte key, Byte direction&)
LOAD_ARG 2 ; key
PUSH 119
MACRO_CONDITIONAL_JF 0 @if7_else
PUSH 3
STORE_ARG 1 ; direction
JMP @if7_endif
:if7_else
LOAD_ARG 2 ; key
PUSH 115
MACRO_CONDITIONAL_JF 0 @if8_else
PUSH 4
STORE_ARG 1 ; direction
JMP @if8_endif
:if8_else
LOAD_ARG 2 ; key
PUSH 97
MACRO_CONDITIONAL_JF 0 @if9_else
PUSH 2
STORE_ARG 1 ; direction
JMP @if9_endif
:if9_else
LOAD_ARG 2 ; key
PUSH 100
MACRO_CONDITIONAL_JF 0 @if10_endif
PUSH 1
STORE_ARG 1 ; direction
:if10_endif
:if9_endif
:if8_endif
:if7_endif
RET
:function_next_head_position
;(Byte headX&, Byte headY&, Byte direction)
LOAD_ARG 1 ; direction
PUSH 3
MACRO_CONDITIONAL_JF 0 @if11_else
LOAD_ARG 2 ; headY
DEC
STORE_ARG 2 ; headY
JMP @if11_endif
:if11_else
LOAD_ARG 1 ; direction
PUSH 4
MACRO_CONDITIONAL_JF 0 @if12_else
LOAD_ARG 2 ; headY
INC
STORE_ARG 2 ; headY
JMP @if12_endif
:if12_else
LOAD_ARG 1 ; direction
PUSH 2
MACRO_CONDITIONAL_JF 0 @if13_else
LOAD_ARG 3 ; headX
DEC
STORE_ARG 3 ; headX
JMP @if13_endif
:if13_else
LOAD_ARG 1 ; direction
PUSH 1
MACRO_CONDITIONAL_JF 0 @if14_endif
LOAD_ARG 3 ; headX
INC
STORE_ARG 3 ; headX
:if14_endif
:if13_endif
:if12_endif
:if11_endif
RET
:function_random_fruit_position
;(Byte fruit_x&, Byte fruit_y&)
; Addr mem_ptr[]
PUSHN 2
:while7_begin
PUSH 2
PUSH 49
SYSCALL Std.GetRandomNumber
STORE_ARG 2 ; fruit_x
PUSH 1
PUSH 21
SYSCALL Std.GetRandomNumber
STORE_ARG 1 ; fruit_y
LOAD_ARG 2 ; fruit_x
LOAD_ARG 1 ; fruit_y
LOAD_LOCAL16 0 ; mem_ptr
CALL @function_xy_to_mem_loc
STORE_LOCAL16 0 ; mem_ptr
POPN 2
LOAD_LOCAL16 0 ; mem_ptr
LOAD_GLOBAL16
PUSH16 #0
LESS16
JT @while7_begin
:while7_endwhile
RET
:function_move_body
;()
; Byte Y
; Addr loc[]
; Byte X
; Addr value
PUSHN 6
MACRO_SET_LOCAL 0 21 ;Y
:while8_begin
MACRO_SET_LOCAL 3 49 ;X
LOAD_LOCAL 3 ; X
LOAD_LOCAL 0 ; Y
LOAD_LOCAL16 1 ; loc
CALL @function_xy_to_mem_loc
STORE_LOCAL16 1 ; loc
POPN 2
:while9_begin
LOAD_LOCAL16 1 ; loc
LOAD_GLOBAL16
STORE_LOCAL16 4 ; value
LOAD_LOCAL16 4 ; value
PUSH16 #0
LESS16
JF @if15_endif
LOAD_LOCAL 3 ; X
LOAD_LOCAL 0 ; Y
SYSCALL Std.SetConsoleCursorPosition
MACRO_DEC_LOCAL16 4 ;value
LOAD_LOCAL16 4 ; value
ZERO16
JF @if16_else
PUSH 32
SYSCALL Std.PrintCharPop
JMP @if16_endif
:if16_else
PUSH 111
SYSCALL Std.PrintCharPop
:if16_endif
LOAD_LOCAL16 4 ; value
LOAD_LOCAL16 1 ; loc
STORE_GLOBAL16
:if15_endif
MACRO_DEC_LOCAL 3 ;X
LOAD_LOCAL16 1 ; loc
SUB16C #2
STORE_LOCAL16 1 ; loc
LOAD_LOCAL 3 ; X
PUSH 1
MACRO_CONDITIONAL_JF 0 @if17_endif
JMP @while9_endwhile
:if17_endif
JMP @while9_begin
:while9_endwhile
MACRO_DEC_LOCAL 0 ;Y
LOAD_LOCAL 0 ; Y
MACRO_CONDITIONAL_JF 6 @if18_endif
JMP @while8_endwhile
:if18_endif
JMP @while8_begin
:while8_endwhile
RET