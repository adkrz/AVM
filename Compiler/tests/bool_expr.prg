// Current "bug/feature"
// 5 > 3 + 1 is interpreted as (5 > 3) +1
// but in the future it could be 5 > (3+1) -> TBD
// Keep the test to check consistent grammar behavior for now
byte A = 5 > 3 + 1;
A = 5 > (3+1);
