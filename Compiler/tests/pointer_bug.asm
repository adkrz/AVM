; Byte instruction_pointer[]
PUSHN 2
PUSH16 #9999
STORE_LOCAL16 0 ; instruction_pointer
LOAD_LOCAL16 0 ; instruction_pointer
PUSH16 #1
ADD16
STORE_LOCAL16 0 ; instruction_pointer
HALT