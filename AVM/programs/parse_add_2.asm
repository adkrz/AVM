; Read string from keyboard, parse it as int and add 2 to it
; In case of invalid input, exception is raised

INTERRUPT_HANDLER INT.ParseError @err
PUSH16 @msg1
SYSCALL STD.PrintString
PUSH_NEXT_SP
PUSHN 6 ; "65535" + "\0"
LOAD_LOCAL16 0 ;address of buffer
PUSH 10
SYSCALL STD.ReadString
LOAD_LOCAL16 0
SYSCALL STD.StringToInt
SYSCALL STD.PrintInt
PUSH 2
ADD
PUSH16 @msg2
SYSCALL STD.PrintString
SYSCALL STD.PrintInt
SYSCALL STD.PrintNewLine
HALT
:msg1 "Enter integer: "
:msg2 " + 2 = "
:msg3 "Invalid value!\n"
:err
PUSH16 @msg3
SYSCALL STD.PrintString
HALT