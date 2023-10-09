; This program is a simple Brain***k language interpreter
; Reads program and input from hardcoded array

CONST16 MEMORYADDRESS 1000
PUSH16 @program ; program pointer [0]
PUSH16 @input ; input pointer [2]

PUSH16 @program
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
JT @halt

; fetch instruction
LOAD_LOCAL16 0
LOAD_GLOBAL

DUP
PUSH 43
EQ
JT @plus
DUP
PUSH 45
EQ
JT @minus
DUP
PUSH 60
EQ
JT @left
DUP
PUSH 62
EQ
JT @right
DUP
PUSH 46
EQ
JT @dot
DUP
PUSH 44
EQ
JT @comma
DUP
PUSH 91
EQ
JT @open
DUP
PUSH 93
EQ
JT @close
POP
JMP @next

:plus
POP
LOAD_LOCAL16 6
LOAD_GLOBAL
INC
LOAD_LOCAL16 6
STORE_GLOBAL
jmp @next

:minus
POP
LOAD_LOCAL16 6
LOAD_GLOBAL
DEC
LOAD_LOCAL16 6
STORE_GLOBAL
jmp @next

:left
POP
LOAD_LOCAL16 6
DEC16
STORE_LOCAL16 6
jmp @next

:right
POP
LOAD_LOCAL16 6
INC16
STORE_LOCAL16 6
jmp @next

:dot
POP
LOAD_LOCAL16 6
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
jmp @next

:comma
POP
LOAD_LOCAL16 2
LOAD_GLOBAL
LOAD_LOCAL16 6
STORE_GLOBAL
LOAD_LOCAL16 2
INC16
STORE_LOCAL16 2
jmp @next

:open
POP
	LOAD_LOCAL16 6
	LOAD_GLOBAL
	ZERO
	JF @next
	PUSH 1 ; count open braces [8]
	:loop_openbracket
	; increment program ptr
	LOAD_LOCAL16 0
	INC16
	STORE_LOCAL16 0
	; check the instruction
	LOAD_LOCAL16 0
	LOAD_GLOBAL
	PUSH 91
	EQ
	JT @increment_counter1
	LOAD_LOCAL16 0
	LOAD_GLOBAL
	PUSH 93
	EQ
	JT @decrement_counter1
	JMP @loop_openbracket_cont

		:increment_counter1
		INC
		JMP @loop_openbracket_cont
		:decrement_counter1
		DEC
		JMP @loop_openbracket_cont

	:loop_openbracket_cont
	LOAD_LOCAL 8 ; open braces
	ZERO
	JF @loop_openbracket
	POP ; counter
	jmp @next

:close
POP
	PUSH 1 ; count open braces [8]
	:loop_closebracket
	; decrement program ptr
	LOAD_LOCAL16 0
	DEC16
	STORE_LOCAL16 0
	; check the instruction
	LOAD_LOCAL16 0
	LOAD_GLOBAL
	PUSH 91
	EQ
	JT @decrement_counter2
	LOAD_LOCAL16 0
	LOAD_GLOBAL
	PUSH 93
	EQ
	JT @increment_counter2
	JMP @loop_closebracket_cont

		:increment_counter2
		INC
		JMP @loop_closebracket_cont
		:decrement_counter2
		DEC
		JMP @loop_closebracket_cont

	:loop_closebracket_cont
	LOAD_LOCAL 8 ; open braces
	ZERO
	JF @loop_closebracket
	POP ; counter
	; decrenent program ptr once again
	LOAD_LOCAL16 0
	DEC16
	STORE_LOCAL16 0
	jmp @next

:next
; increment program ptr
LOAD_LOCAL16 0
INC16
STORE_LOCAL16 0
jmp @loop

:halt
HALT

:program
; Hello World
;"++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
; Sierpinski Triangle
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"
:input
""