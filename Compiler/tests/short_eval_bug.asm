; Addr expr
PUSHN 2
PUSH16 #1
DUP16
POP
JT @cond1_expr_end
PUSH16 #1
OR
:cond1_expr_end
STORE_LOCAL16 0 ; expr
HALT
