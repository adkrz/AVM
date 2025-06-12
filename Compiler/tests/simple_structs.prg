struct str(byte a, addr b, addr c[5]);
struct additional(str x[2], addr y);

// Simple struct:
additional zmienna;
zmienna.x[0].a = 5;
print zmienna.x[0].a;
printnl;

// Array of structs + assign to 16 bit value + index variable that must be extended
byte X = 2;
additional zmienna2[5];
zmienna2[X].x[0].b = 123;
print zmienna2[X].x[0].b;
printnl;

