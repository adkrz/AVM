; Byte program[]
; Byte memory[]
; Byte instruction
; Byte instruction_pointer
; Addr memory_pointer
; Byte count_brackets
PUSHN 9
PUSH16 @string_2
STORE_LOCAL16 0 ; program
PUSH16 #10000
STORE_LOCAL16 2 ; memory
PUSH 0
STORE_LOCAL 5 ; instruction_pointer
PUSH16 #0
STORE_LOCAL16 6 ; memory_pointer
:while1_begin
LOAD_LOCAL16 6 ; memory_pointer
PUSH16 #30000
GREATER_OR_EQ16
JF @while1_endwhile
PUSH 0
LOAD_LOCAL16 2 ; memory
LOAD_LOCAL16 6 ; memory_pointer
ADD16
STORE_GLOBAL
MACRO_INC_LOCAL16 6 ;memory_pointer
JMP @while1_begin
:while1_endwhile
PUSH16 #0
STORE_LOCAL16 6 ; memory_pointer
:while2_begin
LOAD_LOCAL16 0 ; program
LOAD_LOCAL 5 ; instruction_pointer
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
ZERO
JF @if1_endif
JMP @while2_endwhile
:if1_endif
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if2_else
LOAD_LOCAL16 2 ; memory
LOAD_LOCAL16 6 ; memory_pointer
ADD16
LOAD_GLOBAL
ZERO
JF @if3_endif
PUSH 1
STORE_LOCAL 8 ; count_brackets
:while3_begin
MACRO_INC_LOCAL 5 ;instruction_pointer
LOAD_LOCAL16 0 ; program
LOAD_LOCAL 5 ; instruction_pointer
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if4_endif
MACRO_INC_LOCAL 8 ;count_brackets
:if4_endif
LOAD_LOCAL 4 ; instruction
PUSH 93
EQ
JF @if5_endif
MACRO_DEC_LOCAL 8 ;count_brackets
LOAD_LOCAL 8 ; count_brackets
ZERO
JF @if6_endif
MACRO_INC_LOCAL 5 ;instruction_pointer
JMP @while3_endwhile
:if6_endif
:if5_endif
JMP @while3_begin
:while3_endwhile
JMP @while2_begin
:if3_endif
JMP @if2_endif
:if2_else
LOAD_LOCAL 4 ; instruction
PUSH 93
EQ
JF @if7_else
PUSH 1
STORE_LOCAL 8 ; count_brackets
:while4_begin
MACRO_DEC_LOCAL 5 ;instruction_pointer
LOAD_LOCAL16 0 ; program
LOAD_LOCAL 5 ; instruction_pointer
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4 ; instruction
LOAD_LOCAL 4 ; instruction
PUSH 93
EQ
JF @if8_endif
MACRO_INC_LOCAL 8 ;count_brackets
:if8_endif
LOAD_LOCAL 4 ; instruction
PUSH 91
EQ
JF @if9_endif
MACRO_DEC_LOCAL 8 ;count_brackets
LOAD_LOCAL 8 ; count_brackets
ZERO
JF @if10_endif
JMP @while4_endwhile
:if10_endif
:if9_endif
JMP @while4_begin
:while4_endwhile
JMP @while2_begin
JMP @if7_endif
:if7_else
LOAD_LOCAL 4 ; instruction
PUSH 62
EQ
JF @if11_else
MACRO_INC_LOCAL16 6 ;memory_pointer
JMP @if11_endif
:if11_else
LOAD_LOCAL 4 ; instruction
PUSH 60
EQ
JF @if12_else
MACRO_DEC_LOCAL16 6 ;memory_pointer
JMP @if12_endif
:if12_else
LOAD_LOCAL 4 ; instruction
PUSH 43
EQ
JF @if13_else
LOAD_LOCAL16 2 ; memory
LOAD_LOCAL16 6 ; memory_pointer
ADD16
LOAD_GLOBAL
INC
STORE_GLOBAL_PTR
JMP @if13_endif
:if13_else
LOAD_LOCAL 4 ; instruction
PUSH 45
EQ
JF @if14_else
LOAD_LOCAL16 2 ; memory
LOAD_LOCAL16 6 ; memory_pointer
ADD16
LOAD_GLOBAL
DEC
STORE_GLOBAL_PTR
JMP @if14_endif
:if14_else
LOAD_LOCAL 4 ; instruction
PUSH 46
EQ
JF @if15_endif
LOAD_LOCAL16 2 ; memory
LOAD_LOCAL16 6 ; memory_pointer
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
:if15_endif
:if14_endif
:if13_endif
:if12_endif
:if11_endif
:if7_endif
:if2_endif
MACRO_INC_LOCAL 5 ;instruction_pointer
JMP @while2_begin
:while2_endwhile
PUSH16 @string_1
SYSCALL Std.PrintString
HALT
:string_1
"Program finished\n"
:string_2
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"