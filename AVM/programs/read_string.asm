; Simple string IO. Also, shows how to use fixed strings in program code
; Input string has maximum length limit

PUSH16 @msg1
SYSCALL std.PrintString
PUSH_NEXT_SP
PUSHN 10
LOAD_LOCAL16 0 // addr
PUSH 10
SYSCALL std.ReadString
PUSH16 @msg2
SYSCALL std.PrintString
LOAD_LOCAL16 0 // addr
SYSCALL std.PrintString
PUSH16 @nl
SYSCALL std.PrintString
HALT
:msg1 "Emter your name: "
:msg2 "Nice to meet you, "
:nl "\n"
