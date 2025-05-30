// Global variable, even if unused, should not contribute to load/store_local offsets inside function
byte mat[] = {0};

function print_sudoku() begin
global mat;
    byte r = 0;
    while r < 9 do begin
        byte c = 0;
        while c < 9  do begin
            print c;
            printch ' ';
            c = c + 1;
        end
        printnl;
        r = r + 1;
    end
end


call print_sudoku();