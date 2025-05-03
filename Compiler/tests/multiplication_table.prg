// This program tests nested loops, new variable inside loop, continue and break


byte c1 = 1;
byte c2;

while c1 <= 10 do begin
    c2 = 1;
    while c2 <= 10 do begin
        byte result = c1 * c2;
        print result;
        print " ";
        c2 = c2 + 1;
    end
    printnl;
    c1 = c1 + 1;
end

print "Now skip some rows!";
printnl;

c1 = 1;
while c1 <= 10 do begin
    if c1 == 3 then begin
        c1 = c1 + 1;
        continue;
    end
    if c1 == 8 then break;

    c2 = 1;
    while c2 <= 10 do begin
        byte result = c1 * c2;
        print result;
        print " ";
        c2 = c2 + 1;
    end
    printnl;
    c1 = c1 + 1;
end