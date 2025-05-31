// Fibonacci function using direct return values
function fibonacci(byte X) -> byte
begin
    if X == 0 then return 0;
    else if X == 1 then return 1;
    return call fibonacci(X - 2) + call fibonacci(X - 1);
end


print call fibonacci(6);
PRINTNL;
