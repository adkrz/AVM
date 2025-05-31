; Addr expr
PUSHN 2
PUSH16 #1
DUP16
DOWNCAST
JT @cond1_expr_end
PUSH16 #1
OR
EXTEND
:cond1_expr_end
STORE_LOCAL16 0 ; expr
HALT
