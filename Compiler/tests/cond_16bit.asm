; Addr a
PUSHN 2
PUSH16 #6
STORE_LOCAL16 0 ; a
LOAD_LOCAL16 0 ; a
PUSH16 #5
LESS16
JF @if1_endif
PUSH16 @string_1
SYSCALL Std.PrintString
:if1_endif
HALT

:string_1
"OK"