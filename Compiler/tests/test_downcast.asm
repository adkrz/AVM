; Addr a
; Byte b
PUSHN 3
PUSH16 #33
STORE_LOCAL16 0 ; a
LOAD_LOCAL16 0 ; a
POP
STORE_LOCAL 2 ; b
LOAD_LOCAL 2 ; b
SYSCALL Std.PrintInt
POP
SYSCALL Std.PrintNewLine
LOAD_LOCAL16 0 ; a
POP
SYSCALL Std.PrintCharPop
SYSCALL Std.PrintNewLine
HALT
