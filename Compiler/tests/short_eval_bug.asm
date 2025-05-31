; Addr expr
PUSHN 2
PUSH16 #1
DUP16
JT16 @cond1_expr_end
PUSH16 #1
MACRO_ORX
:cond1_expr_end
STORE_LOCAL16 0 ; expr
HALT
