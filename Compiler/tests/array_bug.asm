; Addr jump_cache[]
; Addr cache_pointer[]
; Addr X
; Addr loc[]
; Byte L
PUSHN 9
PUSH_NEXT_SP
PUSH16 #2
SUB216
STORE_LOCAL16 0 ; jump_cache
PUSH 10
PUSH 2
MUL
PUSHN2 ; jump_cache alloc
LOAD_LOCAL16 0 ; jump_cache
STORE_LOCAL16 2 ; cache_pointer
LOAD_LOCAL16 2 ; cache_pointer
LOAD_GLOBAL16
INC16
STORE_LOCAL16 4 ; X
LOAD_LOCAL16 6 ; loc
LOAD_LOCAL 8 ; L
EXTEND
PUSH16 #1
ADD16
STORE_GLOBAL216
HALT