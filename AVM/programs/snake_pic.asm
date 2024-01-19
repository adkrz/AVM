; Snake game implemented in terminal
; use W,S,A,D to control movement
;
; Principle of snake movement: the body shape is kept in memory array (16bit)
; where each snake "pixel" is described by number. The oldest tail part has value 1, next has 2... etc
; until head, which has value == snake length. When snake moves, whole array is decremented by 1.
; If value reaches 0, snake pixel is cleared. In this way history of motions (the trail) is preserved,
; so the tail follows head motion.

CONST WIDTH 50
CONST HEIGHT 22
CONST16 MEMORYLOCATION 10000
CONST MEMORY_ROW_STRIDE 98 ; (width-2+1) * 2bits
CONST INITIAL_X 20
CONST INITIAL_HEAD_X 24 ; initial x + len - 1
CONST INITIAL_Y 10
CONST INITIAL_LEN 5
CONST BODY_CHAR 111 ; o
CONST HEAD_CHAR 79 ; O
CONST WALL_CHAR 35 ; #
CONST FRUIT_CHAR 37 ; %
CONST KeyW 119
CONST KeyS 115
CONST KeyA 97
CONST KeyD 100
CONST16 DELAY 200

; -------------------------------------------------------------

PUSH 0
Syscall Std.ShowConsoleCursor
Syscall Std.ConsoleClear
CALL_REL @memset
CALL_REL @drawborders
CALL_REL @initial_draw

PUSH16 #5 ; length 16bit
PUSH 1 ; direction: 1 right 2 left 3 up 4 down
PUSH Const.INITIAL_HEAD_X; head X
PUSH Const.INITIAL_Y; head Y
PUSH 0 ; fruit position. 0 = need to generate
PUSH 0

;PUSH16 #5 ; length
;CALL_REL @redraw
;POPN 2

:main_loop
	SYSCALL Std.ReadKey
	DUP
	JF_REL @main_no_key
	LOAD_LOCAL 2 ; direction
	CALL_REL @new_direction ; by ref
	STORE_LOCAL 2

	:main_no_key
	POP
	LOAD_LOCAL 3
	LOAD_LOCAL 4
	LOAD_LOCAL 2
	CALL_REL @next_head_position ; call by ref!
	POP ; direction not needed

	; if the head is outside borders, game over
	LOAD_LOCAL 7
	JF_REL @game_over
	LOAD_LOCAL 7
	PUSH Const.WIDTH
	EQ
	JT_REL @game_over
	LOAD_LOCAL 8
	JF_REL @game_over
	LOAD_LOCAL 8
	PUSH Const.HEIGHT
	EQ
	JT_REL @game_over

	; if we hit the snake, game over
	PUSHN 2
	LOAD_LOCAL 7
	LOAD_LOCAL 8
	CALL_REL @xy_to_mem_loc
	POPN 2
	LOAD_GLOBAL16
	ZERO16
	JF_REL @game_over

	; if we hit the fruit, make snake longer and generate another fruit
	LOAD_LOCAL 7
	LOAD_LOCAL 5
	EQ
	LOAD_LOCAL 8
	LOAD_LOCAL 6
	EQ
	AND
	JF_REL @just_move
	; increase length
	LOAD_LOCAL16 0
	INC16
	STORE_LOCAL16 0
	; mark the fruit to be generated after memory is updated - clear its X
	PUSH 0
	STORE_LOCAL 5
	; show points
	PUSH CONST.INITIAL_LEN
	EXTEND
	LOAD_LOCAL16 0
	SUB16
	PUSH CONST.WIDTH
	PUSH 5
	ADD
	PUSH 2
	PUSH CONST.HEIGHT
	DIV
	SYSCALL Std.SetConsoleCursorPosition
	SYSCALL Std.PrintInt16
	POPN 2


	:just_move
	; Write new head position to memory. Value = snake length + 1, so after decrement will be equal to HEAD value
	LOAD_LOCAL16 0
	INC16
	PUSHN 2
	LOAD_LOCAL 7
	LOAD_LOCAL 8
	CALL_REL @xy_to_mem_loc
	POPN 2
	STORE_GLOBAL16

	; if the fruit is eaten, generate new one:
	LOAD_LOCAL 5
	ZERO
	JF_REL @main_move_body
	PUSHN 2
	CALL_REL @random_fruit_position
	STORE_LOCAL 6
	STORE_LOCAL 5
	LOAD_LOCAL 5
	LOAD_LOCAL 6
	CALL_REL @draw_fruit
	POPN 2

	:main_move_body
	CALL_REL @move_body

	; show next head pos
	LOAD_LOCAL 7
	LOAD_LOCAL 8
	Syscall Std.SetConsoleCursorPosition
	CALL_REL @draw_head

	; update head position in local variable
	STORE_LOCAL 4
	STORE_LOCAL 3

	PUSH16 Const16.DELAY
	Syscall Std.Sleep

JMP_REL @main_loop

:game_over

PUSH Const.WIDTH
PUSH Const.HEIGHT
INC
Syscall Std.SetConsoleCursorPosition
Syscall Std.PrintNewLine
HALT

; -------------------------------------------------------------
:memset
PUSH16 Const16.MEMORYLOCATION
PUSH16 Const16.MEMORYLOCATION
PUSH16 #0 ; end of memory address to be computed
PUSH Const.WIDTH
DEC ; border
PUSH Const.HEIGHT
DEC;
CALL_REL @xy_to_mem_loc
POPN 2
SUB16
INC16 ; len + 2bytes
INC16
PUSH 0
SYSCALL Std.MemSet
RET

; -------------------------------------------------------------

:drawborders
PUSH 0
PUSH 16
Syscall Std.SetConsoleColors

PUSH Const.WIDTH

:borderloop1
DUP
PUSH 0
Syscall Std.SetConsoleCursorPosition
PUSH Const.WALL_CHAR
Syscall Std.PrintCharPop

DUP
PUSH Const.HEIGHT
Syscall Std.SetConsoleCursorPosition
PUSH Const.WALL_CHAR
Syscall Std.PrintCharPop

DUP
ZERO
JT_REL @next

DEC
JMP_REL @borderloop1

:next
PUSH Const.HEIGHT
:borderloop2
DUP
PUSH 0
SWAP
Syscall Std.SetConsoleCursorPosition
PUSH Const.WALL_CHAR
Syscall Std.PrintCharPop

DUP
PUSH Const.WIDTH
SWAP
Syscall Std.SetConsoleCursorPosition
PUSH Const.WALL_CHAR
Syscall Std.PrintCharPop

DEC
DUP
ZERO
JF_REL @borderloop2

PUSH 0
PUSH 15
Syscall Std.SetConsoleColors

RET

; -------------------------------------------------------------

:xy_to_mem_loc
; first is return value (easier to clean!)
; returns calculated address of array (16 bit)
; takes X and Y snake location (8 bit)
; 
LOAD_ARG 1 ; y
DEC ; we have 1 px of border
EXTEND
PUSH Const.MEMORY_ROW_STRIDE
EXTEND
MUL16
LOAD_ARG 2 ; x
DEC ; border
PUSH 2
MUL ; 16bit
EXTEND
ADD16
PUSH16 Const16.MEMORYLOCATION
ADD16
STORE_ARG16 4
RET

; -------------------------------------------------------------

:initial_draw
PUSH Const.INITIAL_X
PUSH 0 ; counter

:initial_draw_loop
PUSHN 2
LOAD_LOCAL 0
PUSH Const.INITIAL_Y
CALL_REL @xy_to_mem_loc
POPN 2
LOAD_LOCAL 1 ; current snake length
INC ; loop is counting from 0
EXTEND
SWAP16
STORE_GLOBAL16

LOAD_LOCAL 0
PUSH Const.INITIAL_Y
SYSCALL Std.SetConsoleCursorPosition


LOAD_LOCAL 0
INC
STORE_LOCAL 0

LOAD_LOCAL 1
INC
DUP
STORE_LOCAL 1

PUSH Const.INITIAL_LEN
EQ
JF_REL @initial_draw_loop

RET

; -------------------------------------------------------------
:redraw
; arg: current length 16b
; full redraw: quite slow, but can be used as debugging tool
; that checks, if memory array is correct
PUSH 1 ; X
PUSH 1 ; Y
:redraw_outerloop
	; reset the Y
	PUSH 1
	STORE_LOCAL 1

	:redraw_innerloop
		LOAD_LOCAL 0
		LOAD_LOCAL 1
		SYSCALL Std.SetConsoleCursorPosition

		PUSHN 2
		LOAD_LOCAL 0
		LOAD_LOCAL 1
		CALL_REL @xy_to_mem_loc
		POPN 2
		LOAD_GLOBAL16
		DUP16
		ZERO16
		JT_REL @redraw_clear_pixel
			; Check if this is a head or body
			LOAD_ARG16 2
			EQ16
			JT_REL @redraw_head
			PUSH Const.BODY_CHAR
			SYSCALL Std.PrintCharPop
			JMP_REL @redraw_innerloop_continue
			:redraw_head
			CALL_REL @draw_head
			JMP_REL @redraw_innerloop_continue
		:redraw_clear_pixel
			PUSH 32
			SYSCALL Std.PrintCharPop
			POPN 2

		:redraw_innerloop_continue
		LOAD_LOCAL 1
		INC
		DUP
		STORE_LOCAL 1
		PUSH CONST.HEIGHT
		EQ
		NOT
		JT_REL @redraw_innerloop

	LOAD_LOCAL 0
	INC
	DUP
	STORE_LOCAL 0
	PUSH CONST.WIDTH
	EQ
	NOT
	JT_REL @redraw_outerloop

RET

; -------------------------------------------------------------
:next_head_position
; gets X and Y of head and direction
; sets new XY by ref
; direction: 1 right 2 left 3 up 4 down
; note: Y goes down
LOAD_ARG 1
PUSH 1
EQ
JT_REL @next_head_position_right
LOAD_ARG 1
PUSH 2
EQ
JT_REL @next_head_position_left
LOAD_ARG 1
PUSH 3
EQ
JT_REL @next_head_position_up
JMP_REL @next_head_position_down
:next_head_position_right
LOAD_ARG 3
INC
STORE_ARG 3
RET
:next_head_position_left
LOAD_ARG 3
DEC
STORE_ARG 3
RET
:next_head_position_up
LOAD_ARG 2
DEC
STORE_ARG 2
RET
:next_head_position_down
LOAD_ARG 2
INC
STORE_ARG 2
RET

; -------------------------------------------------------------
:move_body
; Loops over array and decrements the counters
; updates/clears pixels on screen
PUSH 1 ; X
PUSH 1 ; Y
PUSH16 Const16.MEMORYLOCATION
:move_body_outerloop ; loop over y, order of loop matters for pointer increment
	; reset the X
	PUSH 1
	STORE_LOCAL 0

	:move_body_innerloop ; over x
		LOAD_LOCAL16 2

		LOAD_GLOBAL16

		; if pixel == 0, ignore it for performance
		DUP16
		ZERO16
		JT_REL @move_body_innerloop_continue
		
		LOAD_LOCAL 0
		LOAD_LOCAL 1
		SYSCALL Std.SetConsoleCursorPosition

		DEC16
		; if pixel decremented == 0, clear pixel:
		DUP16
		ZERO16
		JT_REL @move_body_clear_pixel
		; else print body pixel. Head is not computed in this loop
		PUSH Const.BODY_CHAR
		SYSCALL Std.PrintCharPop
		JMP_REL @move_body_innerloop_store

		:move_body_clear_pixel
			PUSH 32
			SYSCALL Std.PrintCharPop
		
		:move_body_innerloop_store
		DUP16
		LOAD_LOCAL16 2
		STORE_GLOBAL16

		:move_body_innerloop_continue
		; increment pointer by 2 bytes
		LOAD_LOCAL16 2
		ADD16C #2
		STORE_LOCAL16 2
		; increment loop counter
		POPN 2
		LOAD_LOCAL 0
		INC
		DUP
		STORE_LOCAL 0
		PUSH CONST.WIDTH
		EQ
		NOT
		JT_REL @move_body_innerloop

	LOAD_LOCAL 1
	INC
	DUP
	STORE_LOCAL 1
	PUSH CONST.HEIGHT
	EQ
	NOT
	JT_REL @move_body_outerloop

RET

; -------------------------------------------------------------
:new_direction
; arg: key+direction, direction changed by ref
;  direction: 1 right 2 left 3 up 4 down
LOAD_ARG 2
PUSH Const.KeyW
EQ
JT_REL @new_directionW
LOAD_ARG 2
PUSH Const.KeyS
EQ
JT_REL @new_directionS
LOAD_ARG 2
PUSH Const.KeyA
EQ
JT_REL @new_directionA
LOAD_ARG 2
PUSH Const.KeyD
EQ
JT_REL @new_directionD
RET
:new_directionW
PUSH 3
STORE_ARG 1
RET
:new_directionS
PUSH 4
STORE_ARG 1
RET
:new_directionA
PUSH 2
STORE_ARG 1
RET
:new_directionD
PUSH 1
STORE_ARG 1
RET

; -------------------------------------------------------------
:random_fruit_position
; returns X and Y
:random_fruit_position_try_again
PUSH 1
PUSH Const.WIDTH
DEC
SYSCALL Std.GetRandomNumber
PUSH 1
PUSH Const.HEIGHT
DEC
SYSCALL Std.GetRandomNumber
; check if we do not collide with the snake
PUSHN 2
LOAD_LOCAL 0
LOAD_LOCAL 1
CALL_REL @xy_to_mem_loc
POPN 2
LOAD_GLOBAL16
ZERO16
JF_REL @clear

LOAD_LOCAL 0
STORE_ARG 2
LOAD_LOCAL 1
STORE_ARG 1
RET

:clear
POPN 2
JMP_REL @random_fruit_position_try_again

RET

; -------------------------------------------------------------
:draw_fruit
; args: x, y
LOAD_ARG 2
LOAD_ARG 1
Syscall Std.SetConsoleCursorPosition
PUSH 10
PUSH 15
Syscall Std.SetConsoleColors
PUSH Const.FRUIT_CHAR
Syscall Std.PrintCharPop
PUSH 0
PUSH 15
Syscall Std.SetConsoleColors
RET
; -------------------------------------------------------------
:draw_head
; draws at current cursor position
PUSH 0
PUSH 3
Syscall Std.SetConsoleColors
PUSH Const.HEAD_CHAR
Syscall Std.PrintCharPop
PUSH 0
PUSH 15
Syscall Std.SetConsoleColors
RET