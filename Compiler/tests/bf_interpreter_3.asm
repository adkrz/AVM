; Byte program[]
; Byte memory[]
; Byte instruction
; Byte instruction_pointer[]
; Byte memory_pointer[]
; Addr strlen
; Addr jump_cache[]
; Addr cache_pointer[]
; Byte count_brackets
; Addr ip1
PUSHN 18
PUSH16 @string_1
STORE_LOCAL16 0 ; program
PUSH16 #10000
STORE_LOCAL16 2 ; memory
LOAD_LOCAL16 0 ; program
STORE_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 2 ; memory
STORE_LOCAL16 7 ; memory_pointer
:while1_begin
LOAD_LOCAL16 7 ; memory_pointer
PUSH16 #40000
SWAP16
LESS_OR_EQ16
JF @while1_endwhile
LOAD_LOCAL16 7 ; memory_pointer
PUSH 0
STORE_GLOBAL2
LOAD_LOCAL16 7 ; memory_pointer
INC16
STORE_LOCAL16 7 ; memory_pointer
JMP @while1_begin
:while1_endwhile
LOAD_LOCAL16 2 ; memory
STORE_LOCAL16 7 ; memory_pointer
PUSH16 #0
STORE_LOCAL16 9 ; strlen
:while2_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 0
NE
JF @while2_endwhile
LOAD_LOCAL16 9 ; strlen
INC16
STORE_LOCAL16 9 ; strlen
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while2_begin
:while2_endwhile
LOAD_LOCAL16 0 ; program
STORE_LOCAL16 5 ; instruction_pointer
PUSH_NEXT_SP
PUSH16 #2
SUB216
STORE_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 9 ; strlen
POP
PUSH 2
MUL
PUSHN2 ; jump_cache alloc
LOAD_LOCAL16 11 ; jump_cache
STORE_LOCAL16 13 ; cache_pointer
:while3_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 0
NE
JF @while3_endwhile
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if1_else
PUSH 1
STORE_LOCAL 15 ; count_brackets
LOAD_LOCAL16 5 ; instruction_pointer
STORE_LOCAL16 16 ; ip1
:while4_begin
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
EQ
JF @if2_else
LOAD_LOCAL 15 ; count_brackets
INC
STORE_LOCAL 15 ; count_brackets
JMP @if2_endif
:if2_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
EQ
JF @if3_else
LOAD_LOCAL 15 ; count_brackets
DEC
STORE_LOCAL 15 ; count_brackets
LOAD_LOCAL 15 ; count_brackets
PUSH 0
EQ
JF @if4_else
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 16 ; ip1
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_GLOBAL216
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 16 ; ip1
STORE_GLOBAL216
JMP @while4_endwhile
JMP @if4_endif
:if4_else
:if4_endif
JMP @if3_endif
:if3_else
:if3_endif
:if2_endif
JMP @while4_begin
:while4_endwhile
LOAD_LOCAL16 16 ; ip1
STORE_LOCAL16 5 ; instruction_pointer
JMP @if1_endif
:if1_else
:if1_endif
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while3_begin
:while3_endwhile
LOAD_LOCAL16 0 ; program
STORE_LOCAL16 5 ; instruction_pointer
:while5_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if5_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
PUSH 0
EQ
JF @if6_else
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 13 ; cache_pointer
LOAD_GLOBAL16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while5_begin
JMP @if6_endif
:if6_else
:if6_endif
JMP @if5_endif
:if5_else
LOAD_LOCAL 4 ; instruction
PUSH 93
EQ
JF @if7_else
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 13 ; cache_pointer
LOAD_GLOBAL16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while5_begin
JMP @if7_endif
:if7_else
LOAD_LOCAL 4 ; instruction
PUSH 62
EQ
JF @if8_else
LOAD_LOCAL16 7 ; memory_pointer
INC16
STORE_LOCAL16 7 ; memory_pointer
JMP @if8_endif
:if8_else
LOAD_LOCAL 4 ; instruction
PUSH 60
EQ
JF @if9_else
LOAD_LOCAL16 7 ; memory_pointer
DEC16
STORE_LOCAL16 7 ; memory_pointer
JMP @if9_endif
:if9_else
LOAD_LOCAL 4 ; instruction
PUSH 43
EQ
JF @if10_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
INC
STORE_GLOBAL2
JMP @if10_endif
:if10_else
LOAD_LOCAL 4 ; instruction
PUSH 45
EQ
JF @if11_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
DEC
STORE_GLOBAL2
JMP @if11_endif
:if11_else
LOAD_LOCAL 4 ; instruction
PUSH 46
EQ
JF @if12_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP @if12_endif
:if12_else
LOAD_LOCAL 4 ; instruction
PUSH 0
EQ
JF @if13_else
JMP @while5_endwhile
JMP @if13_endif
:if13_else
:if13_endif
:if12_endif
:if11_endif
:if10_endif
:if9_endif
:if8_endif
:if7_endif
:if5_endif
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while5_begin
:while5_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
HALT

:string_1
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"
:string_2
"Program finished\n"