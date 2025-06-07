; Byte arr[]
; Byte X
; Byte counter
; Byte sum8
; Addr arr2[]
; Addr sum16
PUSHN 9
PUSH16 @string_1
SYSCALL Std.PrintString
PUSH_REG 1
STORE_LOCAL16 0 ; arr
PUSH 5
PUSHN2
PUSH 11
LOAD_LOCAL16 0 ; arr
STORE_GLOBAL
PUSH 22
LOAD_LOCAL16 0 ; arr
INC16
STORE_GLOBAL
PUSH 33
LOAD_LOCAL16 0 ; arr
ADD16C #2
STORE_GLOBAL
PUSH 44
LOAD_LOCAL16 0 ; arr
ADD16C #3
STORE_GLOBAL
PUSH 4
STORE_LOCAL 2 ; X
PUSH 55
LOAD_LOCAL16 0 ; arr
LOAD_LOCAL 2 ; X
MACRO_ADD8_TO_16
STORE_GLOBAL
PUSH 0
STORE_LOCAL 3 ; counter
:while3_begin
LOAD_LOCAL 3 ; counter
PUSH 4
GREATER_OR_EQ
JF @while3_endwhile
LOAD_LOCAL16 0 ; arr
LOAD_LOCAL 3 ; counter
MACRO_ADD8_TO_16
LOAD_GLOBAL
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
MACRO_INC_LOCAL 3 ;counter
JMP @while3_begin
:while3_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
PUSH 0
STORE_LOCAL 4 ; sum8
LOAD_LOCAL16 0 ; arr
LOAD_LOCAL 4 ; sum8
CALL @function_sum8bit
STORE_LOCAL 4 ; sum8
POPN 2
LOAD_LOCAL 4 ; sum8
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
PUSH16 @string_3
SYSCALL Std.PrintString
PUSH_REG 1
STORE_LOCAL16 5 ; arr2
PUSH 10
PUSHN2
PUSH16 #11
LOAD_LOCAL16 5 ; arr2
STORE_GLOBAL16
PUSH16 #22
LOAD_LOCAL16 5 ; arr2
ADD16C #2
STORE_GLOBAL16
PUSH16 #33
LOAD_LOCAL16 5 ; arr2
ADD16C #4
STORE_GLOBAL16
PUSH16 #44
LOAD_LOCAL16 5 ; arr2
ADD16C #6
STORE_GLOBAL16
PUSH16 #55
LOAD_LOCAL16 5 ; arr2
ADD16C #8
STORE_GLOBAL16
PUSH 0
STORE_LOCAL 3 ; counter
:while4_begin
LOAD_LOCAL 3 ; counter
PUSH 4
GREATER_OR_EQ
JF @while4_endwhile
LOAD_LOCAL16 5 ; arr2
LOAD_LOCAL 3 ; counter
MACRO_POP_EXT_X2_ADD16
LOAD_GLOBAL16
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
MACRO_INC_LOCAL 3 ;counter
JMP @while4_begin
:while4_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
PUSH16 #0
STORE_LOCAL16 7 ; sum16
LOAD_LOCAL16 5 ; arr2
LOAD_LOCAL16 7 ; sum16
CALL @function_sum16bit
STORE_LOCAL16 7 ; sum16
POPN 2
LOAD_LOCAL16 7 ; sum16
SYSCALL Std.PrintInt16
POPN 2
SYSCALL Std.PrintNewLine
HALT
:function_sum8bit
;(Byte data[], Byte sum&)
; Byte counter
PUSHN 1
PUSH 0
STORE_LOCAL 0 ; counter
PUSH 0
STORE_ARG 1 ; sum
:while1_begin
LOAD_LOCAL 0 ; counter
PUSH 4
GREATER_OR_EQ
JF @while1_endwhile
LOAD_ARG 1 ; sum
LOAD_ARG16 3 ; data
LOAD_LOCAL 0 ; counter
MACRO_ADD8_TO_16
LOAD_GLOBAL
ADD
STORE_ARG 1 ; sum
MACRO_INC_LOCAL 0 ;counter
JMP @while1_begin
:while1_endwhile
RET
:function_sum16bit
;(Addr data[], Addr sum&)
; Byte counter
PUSHN 1
PUSH 0
STORE_LOCAL 0 ; counter
PUSH16 #0
STORE_ARG16 2 ; sum
:while2_begin
LOAD_LOCAL 0 ; counter
PUSH 4
GREATER_OR_EQ
JF @while2_endwhile
LOAD_ARG16 2 ; sum
LOAD_ARG16 4 ; data
LOAD_LOCAL 0 ; counter
MACRO_POP_EXT_X2_ADD16
LOAD_GLOBAL16
ADD16
STORE_ARG16 2 ; sum
MACRO_INC_LOCAL 0 ;counter
JMP @while2_begin
:while2_endwhile
RET
:string_1
"8-bit version\n"
:string_2
"Sum="
:string_3
"16-bit version\n"