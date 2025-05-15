; Byte program[]
; Byte memory[]
; Byte instruction
; Byte instruction_pointer[]
; Byte memory_pointer[]
; Byte count_brackets
PUSHN 10
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
:while2_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if1_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
PUSH 0
EQ
JF @if2_else
PUSH 1
STORE_LOCAL 9 ; count_brackets
:while3_begin
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
EQ
JF @if3_else
LOAD_LOCAL 9 ; count_brackets
INC
STORE_LOCAL 9 ; count_brackets
JMP @if3_endif
:if3_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
EQ
JF @if4_else
LOAD_LOCAL 9 ; count_brackets
DEC
STORE_LOCAL 9 ; count_brackets
LOAD_LOCAL 9 ; count_brackets
PUSH 0
EQ
JF @if5_else
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while3_endwhile
JMP @if5_endif
:if5_else
:if5_endif
JMP @if4_endif
:if4_else
:if4_endif
:if3_endif
JMP @while3_begin
:while3_endwhile
JMP @while2_begin
JMP @if2_endif
:if2_else
:if2_endif
JMP @if1_endif
:if1_else
LOAD_LOCAL 4 ; instruction
PUSH 93
EQ
JF @if6_else
PUSH 1
STORE_LOCAL 9 ; count_brackets
:while4_begin
LOAD_LOCAL16 5 ; instruction_pointer
DEC16
STORE_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
EQ
JF @if7_else
LOAD_LOCAL 9 ; count_brackets
INC
STORE_LOCAL 9 ; count_brackets
JMP @if7_endif
:if7_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
EQ
JF @if8_else
LOAD_LOCAL 9 ; count_brackets
DEC
STORE_LOCAL 9 ; count_brackets
LOAD_LOCAL 9 ; count_brackets
PUSH 0
EQ
JF @if9_else
JMP @while4_endwhile
JMP @if9_endif
:if9_else
:if9_endif
JMP @if8_endif
:if8_else
:if8_endif
:if7_endif
JMP @while4_begin
:while4_endwhile
JMP @while2_begin
JMP @if6_endif
:if6_else
LOAD_LOCAL 4 ; instruction
PUSH 62
EQ
JF @if10_else
LOAD_LOCAL16 7 ; memory_pointer
INC16
STORE_LOCAL16 7 ; memory_pointer
JMP @if10_endif
:if10_else
LOAD_LOCAL 4 ; instruction
PUSH 60
EQ
JF @if11_else
LOAD_LOCAL16 7 ; memory_pointer
DEC16
STORE_LOCAL16 7 ; memory_pointer
JMP @if11_endif
:if11_else
LOAD_LOCAL 4 ; instruction
PUSH 43
EQ
JF @if12_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
INC
STORE_GLOBAL2
JMP @if12_endif
:if12_else
LOAD_LOCAL 4 ; instruction
PUSH 45
EQ
JF @if13_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
DEC
STORE_GLOBAL2
JMP @if13_endif
:if13_else
LOAD_LOCAL 4 ; instruction
PUSH 46
EQ
JF @if14_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP @if14_endif
:if14_else
LOAD_LOCAL 4 ; instruction
PUSH 0
EQ
JF @if15_else
JMP @while2_endwhile
JMP @if15_endif
:if15_else
:if15_endif
:if14_endif
:if13_endif
:if12_endif
:if11_endif
:if10_endif
:if6_endif
:if1_endif
LOAD_LOCAL16 5 ; instruction_pointer
INC16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while2_begin
:while2_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
HALT

:string_1
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"
:string_2
"Program finished\n"