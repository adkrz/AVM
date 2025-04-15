function fibonacci(X, &ret)
begin
    if X == 0 then begin
    ret=0;
    return;
    end

    if X == 1 then begin
    ret=1;
    return;
    end

    A = 0;
    B = 0;
    call fibonacci(X - 2, A);
    call fibonacci(X - 1, B);
    ret = A + B;
end


X = 6;
call fibonacci(X, X);
PRINT X;
PRINTNL;