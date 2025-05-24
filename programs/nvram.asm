; Simple demonstrator that loads value from disk file, increments it and saves back
; run program multiple times to see change in output value

PUSH16 #0
LOAD_NVRAM
SYSCALL Std.PrintInt
SYSCALL Std.PrintNewLine
INC
PUSH16 #0
STORE_NVRAM
