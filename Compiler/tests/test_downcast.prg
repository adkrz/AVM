addr a = 33;
byte b = a;
print b;
printnl;
printch a;
printnl;

// Downcast in IF
a = 316;
b = 256;
a = a & b;
if a then print "OK";