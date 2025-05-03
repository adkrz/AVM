function fibonacci(byte X, byte ret&)
begin
    if X == 0 then begin
    ret=0;
    return;
    end

    if X == 1 then begin
    ret=1;
    return;
    end

    byte A = 0;
    byte B = 0;
    call fibonacci(X - 2, A);
    call fibonacci(X - 1, B);
    ret = A + B;
end


byte X = 6;
call fibonacci(X, X);
PRINT X;
PRINTNL;
