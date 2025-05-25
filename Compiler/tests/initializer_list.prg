// Array initializer + length operator
byte arr[] = {1,2,3,4,5};
byte counter = 0;
while counter <= length(arr) do begin
    print arr[counter];
    counter = counter + 1;
end
printnl;

// another one, with other type
addr arr2[] = {1,2,3,4,5};
counter = 0;
while counter <= length(arr) do begin
    print arr[counter];
    counter = counter + 1;
end
printnl;