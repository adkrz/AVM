; Addr a
; Byte b
PUSHN 3
PUSH16 #2
PUSH16 #3
PUSH16 #5
ADD16
MUL16
PUSH16 #9
SUB216
PUSH16 #65
ADD16
STORE_LOCAL16 0 ; a
PUSH16 #123
STORE_LOCAL16 0 ; a
PUSH16 #123
DOWNCAST
STORE_LOCAL 2 ; b
HALT