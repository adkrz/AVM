; simple check of call/ret instructions

PUSH 5
PUSH 9
PUSHN 1  // return value
CALL @dodaj
SYSCALL std.PrintInt
SYSCALL std.PrintNewLine
HALT
:dodaj
LOAD_ARG 2  // -4 fields: fp ip retval this one
LOAD_ARG 3
ADD
PUSHN 1  // return value from dodaj1 -> our true local variable
CALL @dodaj1
STORE_ARG 1
RET
:dodaj1
LOAD_ARG 2
PUSH 1
ADD
STORE_ARG 1
RET