// This program tests:
// simple arrays, passing them to function, return values from function, print string constants, while loop, expr. as array index

function sum8bit(byte data[], byte sum&)
begin
byte counter = 0;
sum = 0;
while counter <= 4 do begin
    sum = sum + data[counter];
    counter = counter + 1;
end
end

function sum16bit(addr data[], addr sum&)
begin
byte counter = 0;
sum = 0;
while counter <= 4 do begin
    sum = sum + data[counter];
    counter = counter + 1;
end
end

print "8-bit version\n";
byte arr[5];
arr[0] = 11;
arr[1] = 22;
arr[2] = 33;
arr[2+1] = 44; // check if expression works
byte X = 4; // this one must be upcasted
arr[X] = 55;

byte counter = 0;
while counter <= 4 do begin
    print arr[counter];
    printnl;
    counter = counter + 1;
end
print "Sum=";
byte sum8 = 0;
call sum8bit(arr, sum8);
print sum8;
printnl;

print "16-bit version\n";
addr arr2[5];
arr2[0] = 11;
arr2[1] = 22;
arr2[2] = 33;
arr2[3] = 44;
arr2[4] = 55;
counter = 0;
while counter <= 4 do begin
    print arr2[counter];
    printnl;
    counter = counter + 1;
end
print "Sum=";
addr sum16 = 0;
call sum16bit(arr2, sum16);
print sum16;
printnl;