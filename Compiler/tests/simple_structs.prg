struct str(byte a, addr b, addr c[5]);
struct additional(str x[2], addr y);

// Simple struct:
additional zmienna;
zmienna.x[0].a = 5;
print zmienna.x[0].a;
printnl;

// Array of structs + assign to 16 bit value
additional zmienna2[5];
zmienna2[2].x[0].b = 1;
print zmienna2[2].x[0].b;
printnl;
