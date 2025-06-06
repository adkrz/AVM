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

// Also with array:
byte mat[] = {3,4,5};
addr val = 1 << mat[1];
print val;
printnl;
print ~val;
printnl;
// ensure proper print16
print #1 << mat[2];
printnl;
halt;
