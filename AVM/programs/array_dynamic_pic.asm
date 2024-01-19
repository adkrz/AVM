; Create some array on stack, pass address of stack array to another function
; and compute its sum

PUSH 42 ; some random data in the beginning
CALL_REL @doit
HALT
:doit
PUSH_NEXT_SP ; current stack top + 1, 16 bit value
PUSH 5
PUSH 4
PUSH 3
PUSH 2
PUSH 1
PUSH 5 ; array length
; Prepare arguments: beginning and length
LOAD_LOCAL16 0
LOAD_LOCAL 7
CALL_REL @print_sum
RET
:print_sum
PUSH 0 ; sum
LOAD_ARG 1 ; Array size, 
PUSH 0 ; counter
:loop
DUP ; copy of counter
EXTEND; make counter 16 bit
LOAD_ARG16 3 ; base address
ADD16 ; ptr+counter
LOAD_GLOBAL ; *ptr
SYSCALL std.PrintInt
SYSCALL std.PrintNewLine
LOAD_LOCAL 0 ; sum
ADD
STORE_LOCAL 0
; Increment and check counter:
INC
DUP
LOAD_LOCAL 1
LESS_OR_EQ
JF_REL @loop
LOAD_LOCAL 0 ; sum
SYSCALL std.PrintInt
SYSCALL std.PrintNewLine
RET