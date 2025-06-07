; Addr jump_cache[]
; Addr cache_pointer[]
; Addr X
; Addr loc[]
; Byte L
PUSHN 9
PUSH_REG 1
STORE_LOCAL16 0 ; jump_cache
PUSH 20
PUSHN2
LOAD_LOCAL16 0 ; jump_cache
STORE_LOCAL16 2 ; cache_pointer
LOAD_LOCAL16 2 ; cache_pointer
LOAD_GLOBAL16
INC16
STORE_LOCAL16 4 ; X
LOAD_LOCAL 8 ; L
EXTEND
INC16
LOAD_LOCAL16 6 ; loc
STORE_GLOBAL16
HALT