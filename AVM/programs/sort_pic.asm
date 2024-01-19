; Bubble sort an array, showing intermediate steps

CONST arraysize 10
:outer_loop
CALL_REL @printarray

push 0 ; number of replacements
push 0; counter of inner loop
push const.arraysize ; array size - 1, because we compare arr[i] and arr[i+1]
dec

	:inner_loop
	dup ; copy array size -1
	load_local 1 ; copy counter
	LESS ; true if counter < 9
	JF_REL @check ; else exit inner loop

	; Make pointer to arr[i]
	PUSH16_REL @data
	load_local 1 ; copy counter
	EXTEND ; and make it 16 bit
	ADD16 ; pointer to arr[i]

	; Make pointer to arr[i+1]
	load_local16 3
	INC16

	; load data at arr[i] but keep the ptr on stack
	load_local16 3
	LOAD_GLOBAL
	; the same for arr[i+1]
	load_local16 5
	LOAD_GLOBAL
	
	; Sort or continue
	LESS
	JT_REL @replace
	POPN 4 ; pop our 2 pointers before going to contiune
	JMP_REL @continue
	
	:replace
	; Pointers are already on the stack, execute swap
	PUSH 1; swap 1 byte
	SYSCALL Std.MemSwap
	; increment number of replacements made
	load_local 0
	inc
	store_local 0
	
	:continue
	; increment counter and continue inner loop:
	load_local 1
	inc
	store_local 1
	jmp_rel @inner_loop
	
:check
; if number of replacements made is > 0, continue outer loop
load_local 0
POPN 3 ; reset local variables
NOT
JF_REL @outer_loop

CALL_REL @printarray
halt

:printarray
; print sorted array, directly using pointers without counter
PUSH16_REL @data ; final ptr -1
PUSH const.arraysize
EXTEND
ADD16
PUSH16_REL @data ; current ptr

:printloop
LOAD_LOCAL16 0
LOAD_LOCAL16 2
LESS16
JF_REL @exit
LOAD_LOCAL16 2
LOAD_GLOBAL
SYSCALL Std.PrintInt
PUSH 32 ; space
SYSCALL Std.PrintChar
POPN 2

; increment ptr
INC16

jmp_rel @printloop
:exit
SYSCALL Std.PrintNewLine
ret

halt
:data
1 8 6 0 4 9 5 2 7 3
