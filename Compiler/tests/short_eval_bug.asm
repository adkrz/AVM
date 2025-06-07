; Addr expr
PUSHN 2
PUSH16 #1
DUP16
JT16 @cond1_expr_end
PUSH16 #1
OR16
:cond1_expr_end
EXTEND
STORE_LOCAL16 0 ; expr
HALT