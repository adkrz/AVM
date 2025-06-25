; Byte program[]
; Byte memory[]
; Byte instruction
; Byte instruction_pointer[]
; Byte memory_pointer[]
; Byte count_brackets
PUSHN 10
PUSH16 @string_2
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
GREATER_OR_EQ16
JF @while1_endwhile
PUSH 0
LOAD_LOCAL16 7 ; memory_pointer
STORE_GLOBAL
MACRO_INC_LOCAL16 7 ;memory_pointer
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
MACRO_CONDITIONAL_JF 0 @if1_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
MACRO_CONDITIONAL_JF 6 @if2_endif
MACRO_SET_LOCAL 9 1
:while3_begin
MACRO_INC_LOCAL16 5 ;instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
MACRO_CONDITIONAL_JF 0 @if3_else
MACRO_INC_LOCAL 9 ;count_brackets
JMP @if3_endif
:if3_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
MACRO_CONDITIONAL_JF 0 @if4_endif
MACRO_DEC_LOCAL 9 ;count_brackets
LOAD_LOCAL 9 ; count_brackets
MACRO_CONDITIONAL_JF 6 @if5_endif
MACRO_INC_LOCAL16 5 ;instruction_pointer
JMP @while3_endwhile
:if5_endif
:if4_endif
:if3_endif
JMP @while3_begin
:while3_endwhile
JMP @while2_begin
:if2_endif
JMP @if1_endif
:if1_else
LOAD_LOCAL 4 ; instruction
PUSH 93
MACRO_CONDITIONAL_JF 0 @if6_else
MACRO_SET_LOCAL 9 1
:while4_begin
MACRO_DEC_LOCAL16 5 ;instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
MACRO_CONDITIONAL_JF 0 @if7_else
MACRO_INC_LOCAL 9 ;count_brackets
JMP @if7_endif
:if7_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
MACRO_CONDITIONAL_JF 0 @if8_endif
MACRO_DEC_LOCAL 9 ;count_brackets
LOAD_LOCAL 9 ; count_brackets
MACRO_CONDITIONAL_JF 6 @if9_endif
JMP @while4_endwhile
:if9_endif
:if8_endif
:if7_endif
JMP @while4_begin
:while4_endwhile
JMP @while2_begin
JMP @if6_endif
:if6_else
LOAD_LOCAL 4 ; instruction
PUSH 62
MACRO_CONDITIONAL_JF 0 @if10_else
MACRO_INC_LOCAL16 7 ;memory_pointer
JMP @if10_endif
:if10_else
LOAD_LOCAL 4 ; instruction
PUSH 60
MACRO_CONDITIONAL_JF 0 @if11_else
MACRO_DEC_LOCAL16 7 ;memory_pointer
JMP @if11_endif
:if11_else
LOAD_LOCAL 4 ; instruction
PUSH 43
MACRO_CONDITIONAL_JF 0 @if12_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
INC
STORE_GLOBAL_PTR
JMP @if12_endif
:if12_else
LOAD_LOCAL 4 ; instruction
PUSH 45
MACRO_CONDITIONAL_JF 0 @if13_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
DEC
STORE_GLOBAL_PTR
JMP @if13_endif
:if13_else
LOAD_LOCAL 4 ; instruction
PUSH 46
MACRO_CONDITIONAL_JF 0 @if14_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP @if14_endif
:if14_else
LOAD_LOCAL 4 ; instruction
MACRO_CONDITIONAL_JF 6 @if15_endif
JMP @while2_endwhile
:if15_endif
:if14_endif
:if13_endif
:if12_endif
:if11_endif
:if10_endif
:if6_endif
:if1_endif
MACRO_INC_LOCAL16 5 ;instruction_pointer
JMP @while2_begin
:while2_endwhile
PUSH16 @string_1
SYSCALL Std.PrintString
HALT
:string_1
"Program finished\n"
:string_2
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"