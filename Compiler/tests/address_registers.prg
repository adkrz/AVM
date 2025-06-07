// Tests, if address calculation is reused when doing simple array element modification
byte a[3];
byte index = 2;
a[0] = a[0] + 1;
a[1] = a[1] + 1;
a[index] = a[index] + 1;
// here it cannot be reused:
a[0] = a[1] + 1;