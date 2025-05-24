; This program is a simple Brain***k language interpreter
; Reads program and input from hardcoded array

CONST16 MEMORYADDRESS 1000
PUSH16_REL @program ; program pointer [0]
PUSH16_REL @input ; input pointer [2]

PUSH16_REL @program
Syscall Std.Strlen ; program length [4]
PUSH16 CONST16.MEMORYADDRESS ; memory pointer [6]

PUSH16 CONST16.MEMORYADDRESS
PUSH16 #30000
PUSH 0
Syscall Std.MemSet

:loop
; check if program pointer == len(program):
LOAD_LOCAL16 0
LOAD_LOCAL16 4
EQ16
JT_REL @halt

; fetch instruction
LOAD_LOCAL16 0
LOAD_GLOBAL

CASE_REL 43 @plus
CASE_REL 45 @minus
CASE_REL 60 @left
CASE_REL 62 @right
CASE_REL 46 @dot
CASE_REL 44 @comma
CASE_REL 91 @open
CASE_REL 93 @close
CASE_REL 0 @halt
ELSE_REL @next

:plus
LOAD_LOCAL16 6
LOAD_GLOBAL
INC
LOAD_LOCAL16 6
STORE_GLOBAL
JMP_REL @next

:minus
LOAD_LOCAL16 6
LOAD_GLOBAL
DEC
LOAD_LOCAL16 6
STORE_GLOBAL
JMP_REL @next

:left
LOAD_LOCAL16 6
DEC16
STORE_LOCAL16 6
JMP_REL @next

:right
LOAD_LOCAL16 6
INC16
STORE_LOCAL16 6
JMP_REL @next

:dot
LOAD_LOCAL16 6
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP_REL @next

:comma
LOAD_LOCAL16 2
LOAD_GLOBAL
LOAD_LOCAL16 6
STORE_GLOBAL
LOAD_LOCAL16 2
INC16
STORE_LOCAL16 2
JMP_REL @next

:open
	LOAD_LOCAL16 6
	LOAD_GLOBAL
	ZERO
	JF_REL @next
	PUSH 1 ; count open braces [8]
	:loop_openbracket
	; increment program ptr
	LOAD_LOCAL16 0
	INC16
	STORE_LOCAL16 0
	; check the instruction
	LOAD_LOCAL16 0
	LOAD_GLOBAL

	CASE_REL 91 @increment_counter1
	CASE_REL 93 @decrement_counter1
	ELSE_REL @loop_openbracket_cont
	
		:increment_counter1
		INC
		JMP_REL @loop_openbracket_cont
		:decrement_counter1
		DEC
		JMP_REL @loop_openbracket_cont

	:loop_openbracket_cont
	LOAD_LOCAL 8 ; open braces
	ZERO
	JF_REL @loop_openbracket
	POP ; counter
	JMP_REL @next

:close
	PUSH 1 ; count open braces [8]
	:loop_closebracket
	; decrement program ptr
	LOAD_LOCAL16 0
	DEC16
	STORE_LOCAL16 0
	; check the instruction
	LOAD_LOCAL16 0
	LOAD_GLOBAL

	CASE_REL 91 @decrement_counter2
	CASE_REL 93 @increment_counter2
	ELSE_REL @loop_closebracket_cont

		:increment_counter2
		INC
		JMP_REL @loop_closebracket_cont
		:decrement_counter2
		DEC
		JMP_REL @loop_closebracket_cont

	:loop_closebracket_cont
	LOAD_LOCAL 8 ; open braces
	ZERO
	JF_REL @loop_closebracket
	POP ; counter
	; decrenent program ptr once again
	LOAD_LOCAL16 0
	DEC16
	STORE_LOCAL16 0
	JMP_REL @next

:next
; increment program ptr
LOAD_LOCAL16 0
INC16
STORE_LOCAL16 0
JMP_REL @loop

:halt
HALT

0 ; sentinel
:program
; Hello World
;"++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
; Sierpinski Triangle
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"
:input
""