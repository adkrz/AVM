;func()
CALL @function_func
; stack cleanup
HALT

:function_func
;()
PUSH16 @string_1
SYSCALL Std.PrintString
RET

:string_1
"Hello!"
