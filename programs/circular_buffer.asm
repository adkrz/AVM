; Creates circular buffer container, ubiquitous in systems with small amount of memory.
; Shows accessing data somewhere in the memory using LOAD_GLOBAL / STORE_GLOBAL
; Buffer stores 16 bit values

CONST16 BUFFER_ADDRESS 1000
CONST16 BUFFER_SIZE 10

PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #10 ; capacity
call @create_buffer

PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #0
call @size
SYSCALL Std.PrintInt16
SYSCALL Std.PrintNewLine

PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #123
call @push_front
PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #124
call @push_front
PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #125
call @push_front

PUSH16 CONST16.BUFFER_ADDRESS
PUSH16 #123
call @size
SYSCALL Std.PrintInt16
SYSCALL Std.PrintNewLine

PUSH16 CONST16.BUFFER_ADDRESS
call @print_contents

HALT


; ===================================================

:create_buffer
; args: address and max length
; return none
; tail index
PUSH16 #0
LOAD_ARG16 4 ; address
STORE_GLOBAL16; val, address
; head index
PUSH16 #0
LOAD_ARG16 4
INC16 ; skip 2 bytes!
INC16
STORE_GLOBAL16 
; max length
LOAD_ARG16 2
LOAD_ARG16 4
PUSH16 #4
ADD16
STORE_GLOBAL16
; is full? (8 bit)
PUSH 0
LOAD_ARG16 4
PUSH16 #6
ADD16
STORE_GLOBAL
RET

; ===================================================

:size
;arg: address
; return current length
LOAD_ARG16 4
LOAD_GLOBAL16 ; tail
LOAD_ARG16 4
ADD16C #2
LOAD_GLOBAL16 ; head
LOAD_ARG16 4
ADD16C #4
LOAD_GLOBAL16 ; max length
LOAD_ARG16 4
ADD16C #6
LOAD_GLOBAL ; is full?
JT @size_isfull ; if (full) return max size
; if head >= tail return head - tail: inverse as tail<head:
LOAD_LOCAL16 2 ; head
LOAD_LOCAL16 0 ; tail
LESS_OR_EQ16
JF @size_else
LOAD_LOCAL16 0
LOAD_LOCAL16 2
SUB16
STORE_ARG16 2
RET
:size_else ; else return max_size +  head - tail
LOAD_LOCAL16 0
LOAD_LOCAL16 4
LOAD_LOCAL16 2
ADD16
SUB16
STORE_ARG16 2
RET
:size_isfull
; max len is on stack:
STORE_ARG16 2
RET

; ===================================================
:push_front
; args: address and value
LOAD_ARG16 4
LOAD_GLOBAL16 ; tail
LOAD_ARG16 4
ADD16C #2
LOAD_GLOBAL16 ; head
LOAD_ARG16 4
ADD16C #4
LOAD_GLOBAL16 ; max length
LOAD_ARG16 4
ADD16C #6
LOAD_GLOBAL ; is full?

; buffer[head] = data
; actually, head + 7 because we have variables at the beginning, *2 because we have 16 bit addresses
LOAD_ARG16 2 ; value
LOAD_ARG16 4
ADD16C #7
LOAD_LOCAL16 2 ; head
MUL16C #2
ADD16

STORE_GLOBAL16

; if full, increment tail
LOAD_LOCAL 6
JF @push_front_rest
; tail = (tail + 1) mod maxsize
LOAD_LOCAL16 4
LOAD_LOCAL16 0
ADD16C #1
MOD16
LOAD_ARG16 4
STORE_GLOBAL16

:push_front_rest
; head = (head + 1) mod maxsize
LOAD_LOCAL16 4
LOAD_LOCAL16 2
ADD16C #1
MOD16
DUP16
LOAD_ARG16 4
ADD16C #2
STORE_GLOBAL16

; full = head == tail, we must use refreshed values:
LOAD_ARG16 4
LOAD_GLOBAL16 ; tail
LOAD_ARG16 4
ADD16C #2
LOAD_GLOBAL16 ; head
EQ16
LOAD_ARG16 4
ADD16C #6
STORE_GLOBAL ; not 16
RET

; ===================================================
:remove_back
; arg: address
; clear "is full"
PUSH 0
LOAD_ARG16 2
ADD16C #6
STORE_GLOBAL
; move tail
LOAD_ARG16 2
ADD16C #4
LOAD_GLOBAL16 ; max length
LOAD_ARG16 2
LOAD_GLOBAL16 ; tail
INC16
MOD16
LOAD_ARG16 2
STORE_GLOBAL16
RET


; ===================================================
:print_contents
; arg = address
LOAD_ARG16 2 ; addr
LOAD_GLOBAL16 ; tail
LOAD_ARG16 2
ADD16C #4
LOAD_GLOBAL16 ; max length
LOAD_ARG16 2
PUSH16 #0
call @size  ; current size

DUP16
ZERO16
JT @print_contents_exit

PUSH16 #0 ; counter

:print_contents_loop
LOAD_LOCAL16 2; max size
LOAD_LOCAL16 8; counter
LOAD_LOCAL16 0 ; tail
ADD16 ; tail+i
MOD16 ; mod maxsize
MUL16C #2
LOAD_ARG16 2; address
ADD16
ADD16C #7 ; need to skip variables at the begin of memory address, mul*2 because of 16 bits

LOAD_GLOBAL16
SYSCALL Std.PrintInt16
PUSH 32 ; space
SYSCALL Std.PrintChar
POPN 3
LOAD_LOCAL16 8; counter
INC16
STORE_LOCAL16 8
; if counter==size exit
LOAD_LOCAL16 8
LOAD_LOCAL16 6
EQ16
JT @print_contents_exit
JMP @print_contents_loop

:print_contents_exit
SYSCALL Std.PrintNewLine
RET