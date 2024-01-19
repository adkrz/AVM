; Classic Fibonacci calculator using recursive definition.
; Optimized version: value of function is passed and returned by reference
; Used to show high stack usages, check stack trace functions etc.

PUSH 6 ; result should be 8
CALL_REL @fib
SYSCALL Std.PrintInt
SYSCALL Std.PrintNewLine
HALT

:fib
LOAD_ARG 1 ; number
DUP
JF_REL @ret0 ; if 0, return 0
DUP
PUSH 1
EQ
JT_REL @ret1; if 1 return 1
JMP_REL @recurse
:ret0
PUSH 0
STORE_ARG 1 ; return
RET
:ret1
PUSH 1
STORE_ARG 1 ; return
RET
:recurse
; n-1:
DUP
DEC
; n -2
DUP
DEC
; fib (n-2)
CALL_REL @fib
; fib (n-1)
SWAP
CALL_REL @fib
; return sum of fibs
ADD
STORE_ARG 1
RET
