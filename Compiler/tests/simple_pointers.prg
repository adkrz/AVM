byte x = 1;
byte y = 1;
addr uninitialized[];
addr A[] = addressof(x);
A = addressof(y);
// this may crash:
A[2] = 0;
uninitialized = A;