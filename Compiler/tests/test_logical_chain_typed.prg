addr row[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
addr col[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
addr box[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
const addr one = 1;
byte num = 3;
byte ok;
addr val = one << num;
byte i = 1;
byte j = 2;
byte box_index = 3;
if (row[i] & val) || (col[j] & val) || (box[box_index] & val) then ok = 0;
else ok = 1;