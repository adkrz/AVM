if 3 << 2 == 12 then print "OK\n";
if 12 >> 1 == 6 then print "OK\n";
if (12 >> 1) | 5 == 7 then print "OK\n";
if (12 >> 1) & 5 == 4 then print "OK\n";
if (12 >> 1) ^ 5 == 3 then print "OK\n";
printnl;

// Check offset and value of different types:
const addr one = 1;
byte offs = 3;
print one << offs;
printnl;