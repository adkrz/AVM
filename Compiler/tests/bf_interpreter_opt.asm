PUSHN 9
PUSH16 @string_1
STORE_LOCAL16 0
PUSH16 #10000
STORE_LOCAL16 2
PUSH 0
STORE_LOCAL 5
PUSH16 #0
STORE_LOCAL16 6
:while1_begin
LOAD_LOCAL16 6
PUSH16 #30000
GREATER_OR_EQ16
JF @while1_endwhile
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
PUSH 0
STORE_GLOBAL2
MACRO_INC_LOCAL16 6
JMP @while1_begin
:while1_endwhile
PUSH16 #0
STORE_LOCAL16 6
:while2_begin
LOAD_LOCAL16 0
LOAD_LOCAL 5
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4
LOAD_LOCAL 4
ZERO
JF @if1_else
JMP @while2_endwhile
JMP @if1_endif
:if1_else
:if1_endif
LOAD_LOCAL 4
PUSH 91
EQ
JF @if2_else
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_GLOBAL
ZERO
JF @if3_else
PUSH 1
STORE_LOCAL 8
:while3_begin
MACRO_INC_LOCAL 5
LOAD_LOCAL16 0
LOAD_LOCAL 5
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4
LOAD_LOCAL 4
PUSH 91
EQ
JF @if4_else
MACRO_INC_LOCAL 8
JMP @if4_endif
:if4_else
:if4_endif
LOAD_LOCAL 4
PUSH 93
EQ
JF @if5_else
MACRO_DEC_LOCAL 8
LOAD_LOCAL 8
ZERO
JF @if6_else
MACRO_INC_LOCAL 5
JMP @while3_endwhile
JMP @if6_endif
:if6_else
:if6_endif
JMP @if5_endif
:if5_else
:if5_endif
JMP @while3_begin
:while3_endwhile
JMP @while2_begin
JMP @if3_endif
:if3_else
:if3_endif
JMP @if2_endif
:if2_else
LOAD_LOCAL 4
PUSH 93
EQ
JF @if7_else
PUSH 1
STORE_LOCAL 8
:while4_begin
MACRO_DEC_LOCAL 5
LOAD_LOCAL16 0
LOAD_LOCAL 5
MACRO_ADD8_TO_16
LOAD_GLOBAL
STORE_LOCAL 4
LOAD_LOCAL 4
PUSH 93
EQ
JF @if8_else
MACRO_INC_LOCAL 8
JMP @if8_endif
:if8_else
:if8_endif
LOAD_LOCAL 4
PUSH 91
EQ
JF @if9_else
MACRO_DEC_LOCAL 8
LOAD_LOCAL 8
ZERO
JF @if10_else
JMP @while4_endwhile
JMP @if10_endif
:if10_else
:if10_endif
JMP @if9_endif
:if9_else
:if9_endif
JMP @while4_begin
:while4_endwhile
JMP @while2_begin
JMP @if7_endif
:if7_else
LOAD_LOCAL 4
PUSH 62
EQ
JF @if11_else
MACRO_INC_LOCAL16 6
JMP @if11_endif
:if11_else
LOAD_LOCAL 4
PUSH 60
EQ
JF @if12_else
MACRO_DEC_LOCAL16 6
JMP @if12_endif
:if12_else
LOAD_LOCAL 4
PUSH 43
EQ
JF @if13_else
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_GLOBAL
INC
STORE_GLOBAL2
JMP @if13_endif
:if13_else
LOAD_LOCAL 4
PUSH 45
EQ
JF @if14_else
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_GLOBAL
DEC
STORE_GLOBAL2
JMP @if14_endif
:if14_else
LOAD_LOCAL 4
PUSH 46
EQ
JF @if15_else
LOAD_LOCAL16 2
LOAD_LOCAL16 6
ADD16
LOAD_GLOBAL
SYSCALL Std.PrintCharPop
JMP @if15_endif
:if15_else
:if15_endif
:if14_endif
:if13_endif
:if12_endif
:if11_endif
:if7_endif
:if2_endif
MACRO_INC_LOCAL 5
JMP @while2_begin
:while2_endwhile
PUSH16 @string_2
SYSCALL Std.PrintString
HALT
:string_1
"++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]"
:string_2
"Program finished\n"