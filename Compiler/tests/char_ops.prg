// This program tests printing chars, infinite loop and reading string as pointer

printch 'T';
printch 'E';
printch 'S';
printch 'T';
printch '\n';

byte string[] = addressof("hello world");
byte index = 0;
byte char;

while 1 do begin
    char = string[index];
    if char == 0 then break;
    printch char;
    index = index + 1;
end

printnl;