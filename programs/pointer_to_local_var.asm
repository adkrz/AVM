push 11
push 12
push 22
; create pointer to "22" using frame ptr + offset
push_reg 2 ; 2=FP
push16 #2 ; offset -> to 8 bit local var no #3
add16
; dereference
load_global
;add 20
push 20
add
syscall std.printint
syscall std.printnewline
halt