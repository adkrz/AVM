; struct point3d pt
PUSHN 3
PUSH_REG 2
PUSH16 #0
ADD16
PUSH16 #0
ADD16
PUSH 11
STORE_GLOBAL2
PUSH_REG 2
PUSH16 #0
ADD16
PUSH16 #1
ADD16
PUSH 22
STORE_GLOBAL2
PUSH_REG 2
PUSH16 #0
ADD16
PUSH16 #2
ADD16
PUSH 33
STORE_GLOBAL2
;printpt(Struct pt)
PUSH_REG 2
PUSH16 #0
ADD16
CALL @function_printpt
; stack cleanup
POPN 2
;setxy_only(Struct pt)
PUSH_REG 2
PUSH16 #0
ADD16
CALL @function_setxy_only
; stack cleanup
POPN 2
;printpt(Struct pt)
PUSH_REG 2
PUSH16 #0
ADD16
CALL @function_printpt
; stack cleanup
POPN 2
HALT

:function_printpt
;(Struct pt)
PUSH16 @string_1
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
PUSH16 #0
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
PUSH16 @string_2
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
PUSH16 #1
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
PUSH16 @string_3
SYSCALL Std.PrintString
LOAD_ARG16 2 ; pt
PUSH16 #2
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
RET

:function_setxy_only
;(Struct pt)
LOAD_ARG16 2 ; pt
PUSH16 #0
ADD16
PUSH 44
STORE_GLOBAL2
LOAD_ARG16 2 ; pt
PUSH16 #1
ADD16
PUSH 55
STORE_GLOBAL2
RET

:string_1
"X="
:string_2
" Y="
:string_3
" Z="