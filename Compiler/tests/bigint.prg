// Try to print integer "manually" without using builtin print
// Try to print integer made of multiple bytes array (potentially bigger than 16-bit supported by VM)

function print_decimal(byte data)
begin
    if data == 0 then begin
      print "0";
      return;
     end
    byte buf[32];
    byte i = 0;

    while data > 0 do begin
        buf[i] = '0' + data % 10;
        data = data / 10;
        i = i + 1;
    end
    byte j = i;

    while j>=0 do begin
        printch buf[j - 1];
        j = j - 1;
        if j == 0 then break;  // missing negative numbers support
    end
end

function copy_arr(byte src[], byte dst[], byte size) begin
byte i = 0;
while i < size do begin
    dst[i] = src[i];
    i = i + 1;
end
end

function print_bigint_decimal(byte data[], byte size)
begin
    // Copy input so we can modify it
    byte temp[size];
    call copy_arr(data, temp, size);

    byte digits[10]; // log10(2^32)
    byte digit_count = 0;

    // While the number is not zero
    while 1 do begin
        // Divide temp by 10, store remainder
        addr remainder = 0;
        byte nonzero = 0;
        byte i = 0;

        while i<size do begin
            remainder = (remainder << 8) | temp[i];
            temp[i] = remainder / 10;
            remainder = remainder % 10;
            if temp[i] != 0 then nonzero = 1;
            i = i + 1;
        end

        digits[digit_count] = '0' + remainder;
        digit_count = digit_count + 1;
        if nonzero == 0 then break;
    end

    // Print digits in reverse
    i = digit_count;
    while i>=0 do begin
        printch digits[i - 1];
        i = i - 1;
        if i == 0 then break;  // missing negative numbers support
    end

end

call print_decimal(156);
printnl;
byte data[] = {2,3, 3};
call print_bigint_decimal(data, 3);