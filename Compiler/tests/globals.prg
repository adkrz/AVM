// This program tests: global variables, function without args, AND operator, nested IF

byte a = 1;  // must be byte for now - we do not support "4" below as 16-bit variable directly

function func()
begin
global a;
a = a + 3;
end

call func();
if a == 4 && a > 0 then print "OK!";
printnl;
if a == 4 then begin
    if a > 0 then begin
        print "OK2!";
    end
end