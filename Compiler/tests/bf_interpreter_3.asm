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
MACRO_SET_LOCAL16 9 #0 ;strlen
:while2_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
MACRO_CONDITIONAL_JF 7 @while2_endwhile
MACRO_INC_LOCAL16 9 ;strlen
MACRO_INC_LOCAL16 5 ;instruction_pointer
JMP @while2_begin
:while2_endwhile
LOAD_LOCAL16 0 ; program
STORE_LOCAL16 5 ; instruction_pointer
PUSH_REG 1
STORE_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 9 ; strlen
DOWNCAST
MULC 2
PUSHN2
LOAD_LOCAL16 11 ; jump_cache
STORE_LOCAL16 13 ; cache_pointer
:while3_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
MACRO_CONDITIONAL_JF 7 @while3_endwhile
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
STORE_LOCAL_KEEP 4 ; instruction
PUSH 91
MACRO_CONDITIONAL_JF 0 @if1_endif
MACRO_SET_LOCAL 15 1 ;count_brackets
LOAD_LOCAL16 5 ; instruction_pointer
STORE_LOCAL16 16 ; ip1
:while4_begin
MACRO_INC_LOCAL16 5 ;instruction_pointer
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 91
MACRO_CONDITIONAL_JF 0 @if2_else
MACRO_INC_LOCAL 15 ;count_brackets
JMP @if2_endif
:if2_else
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
PUSH 93
MACRO_CONDITIONAL_JF 0 @if3_endif
MACRO_DEC_LOCAL 15 ;count_brackets
LOAD_LOCAL 15 ; count_brackets
MACRO_CONDITIONAL_JF 6 @if4_endif
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 16 ; ip1
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 5 ; instruction_pointer
INC16
LOAD_LOCAL16 13 ; cache_pointer
STORE_GLOBAL16
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL16 13 ; cache_pointer
LOAD_LOCAL16 16 ; ip1
LOAD_LOCAL16 13 ; cache_pointer
STORE_GLOBAL16
JMP @while4_endwhile
:if4_endif
:if3_endif
:if2_endif
JMP @while4_begin
:while4_endwhile
LOAD_LOCAL16 16 ; ip1
STORE_LOCAL16 5 ; instruction_pointer
:if1_endif
MACRO_INC_LOCAL16 5 ;instruction_pointer
JMP @while3_begin
:while3_endwhile
LOAD_LOCAL16 0 ; program
STORE_LOCAL16 5 ; instruction_pointer
:while5_begin
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_GLOBAL
STORE_LOCAL_KEEP 4 ; instruction
PUSH 91
MACRO_CONDITIONAL_JF 0 @if5_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
MACRO_CONDITIONAL_JF 6 @if6_endif
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL_KEEP16 13 ; cache_pointer
LOAD_GLOBAL16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while5_begin
:if6_endif
JMP @if5_endif
:if5_else
LOAD_LOCAL 4 ; instruction
PUSH 93
MACRO_CONDITIONAL_JF 0 @if7_else
LOAD_LOCAL16 11 ; jump_cache
LOAD_LOCAL16 5 ; instruction_pointer
LOAD_LOCAL16 0 ; program
SUB216
ADD16
STORE_LOCAL_KEEP16 13 ; cache_pointer
LOAD_GLOBAL16
STORE_LOCAL16 5 ; instruction_pointer
JMP @while5_begin
JMP @if7_endif
:if7_else
LOAD_LOCAL 4 ; instruction
PUSH 62
MACRO_CONDITIONAL_JF 0 @if8_else
MACRO_INC_LOCAL16 7 ;memory_pointer
JMP @if8_endif
:if8_else
LOAD_LOCAL 4 ; instruction
PUSH 60
MACRO_CONDITIONAL_JF 0 @if9_else
MACRO_DEC_LOCAL16 7 ;memory_pointer
JMP @if9_endif
:if9_else
LOAD_LOCAL 4 ; instruction
PUSH 43
MACRO_CONDITIONAL_JF 0 @if10_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
INC
STORE_GLOBAL_PTR
JMP @if10_endif
:if10_else
LOAD_LOCAL 4 ; instruction
PUSH 45
MACRO_CONDITIONAL_JF 0 @if11_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
DEC
STORE_GLOBAL_PTR
JMP @if11_endif
:if11_else
LOAD_LOCAL 4 ; instruction
PUSH 46
MACRO_CONDITIONAL_JF 0 @if12_else
LOAD_LOCAL16 7 ; memory_pointer
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP @if12_endif
:if12_else
LOAD_LOCAL 4 ; instruction
MACRO_CONDITIONAL_JF 6 @if13_endif
JMP @while5_endwhile
:if13_endif
:if12_endif
:if11_endif
:if10_endif
:if9_endif
:if8_endif
:if7_endif
:if5_endif
MACRO_INC_LOCAL16 5 ;instruction_pointer
JMP @while5_begin
:while5_endwhile
PUSH16 @string_1
SYSCALL Std.PrintString
HALT
:string_1
"Program finished\n"
:string_2
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"