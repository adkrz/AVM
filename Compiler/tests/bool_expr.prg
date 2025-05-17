// Operator precedence test:
// 5 > 3 + 1 is interpreted as 5 > (3 +1), regardless with or without parentheses
// not as (5>3) + 1
byte A = 5 > 3 + 1;
A = 5 > (3+1);
