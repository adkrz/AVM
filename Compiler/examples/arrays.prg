arr = [5];
arr[0] = 2;
arr[1] = 3;
print "2+3+1=";
X = arr[0] + arr[1] + 1;
print X;
printnl;

arr[2] = 7;
arr[3] = 4;
arr[4] = 5;

function sum(data[], &sum)
begin
    counter = 5;
    sum = 0;
    while counter >= 0 do begin
        sum = sum + data[counter];
        counter = counter - 1;
    end
end

result = 0;
call sum(arr, result);
print "2+3+7+4+5=";
print result;
printnl;
