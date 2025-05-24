// based on https://www.geeksforgeeks.org/sudoku-backtracking-7/
byte mat[] = {
        3, 0, 6, 5, 0, 8, 4, 0, 0,
        5, 2, 0, 0, 0, 0, 0, 0, 0,
        0, 8, 7, 0, 0, 0, 0, 3, 1,
        0, 0, 3, 0, 1, 0, 0, 8, 0,
        9, 0, 0, 8, 6, 3, 0, 0, 5,
        0, 5, 0, 0, 9, 0, 6, 0, 0,
        1, 3, 0, 0, 0, 0, 2, 5, 0,
        0, 0, 0, 0, 0, 0, 0, 7, 4,
        0, 0, 5, 2, 0, 6, 3, 0, 0
};

// Evil example from Wikipedia:
//byte mat[] = {
//    0, 0, 0, 0, 0, 0, 0, 0, 0,
//    0, 0, 0, 0, 0, 3, 0, 8, 5,
//    0, 0, 1, 0, 2, 0, 0, 0, 0,
//    0, 0, 0, 5, 0, 7, 0, 0, 0,
//    0, 0, 4, 0, 0, 0, 1, 0, 0,
//    0, 9, 0, 0, 0, 0, 0, 0, 0,
//    5, 0, 0, 0, 0, 0, 0, 7, 3,
//    0, 0, 2, 0, 1, 0, 0, 0, 0,
//    0, 0, 0, 0, 4, 0, 0, 0, 9
//};

addr row[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
addr col[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
addr box[]  = {0, 0, 0, 0, 0, 0, 0, 0, 0};
const addr one = 1;
const byte size = 9;

function print_sudoku(byte matrix[]) begin
    byte r = 0;
    while r < size do begin
        byte c = 0;
        while c < size  do begin
            byte index = r * size + c;
            print matrix[index];
            printch ' ';
            c = c + 1;
        end
        printnl;
        r = r + 1;
    end
end

function sudokuSolverRec(byte mat[], byte i, byte j, addr row[], addr col[], addr box[], byte ret&)
begin
    ret = 0;

    // base case: Reached nth column of last row
    if i == size-1 && j == size then begin
    ret = 1;
    return;
    end

    // If reached last column of the row go to next row
    if j == size then begin
        i = i + 1;
        j = 0;
    end

    byte ok;

    // If cell is already occupied then move forward
    byte index = i * size + j;
    if mat[index] != 0 then begin
        call sudokuSolverRec(mat, i, j + 1, row, col, box, ok);
        ret = ok;
        return;
    end

    byte num = 1;

    while num <= size do begin

        // Check if solution with that number is valid:
        byte box_index = i / 3 * 3 + j / 3; // ensure type - DIV16 not implemented
        addr val = one << num;
        if (row[i] & val) || (col[j] & val) || (box[box_index] & val) then ok = 0;
        else ok = 1;

        if ok then begin
            mat[index] = num;

            //Update masks for the corresponding row, column and box
            row[i] = row[i] | val;
            col[j] = col[j] | val;
            box[box_index] = box[box_index] | val;

            call sudokuSolverRec(mat, i, j+1, row, col, box, ok);
            if ok then begin
                ret = ok;
                return;
            end

            //Unmask the number num in the corresponding row, column and box masks
            mat[index] = 0;
            val = ~val;
            row[i] = row[i] & val;
            col[j] = col[j] & val;
            box[box_index] = box[box_index] & val;
        end
        num = num + 1;
    end

    ret = 0;
end

// Set the bit masks:
byte r = 0;
while r < size do begin
    byte c = 0;
    while c < size  do begin
        byte index = r * size + c;
        if mat[index] != 0 then begin
            addr val = one << mat[index];
            row[r] = row[r] | val;
            col[c] = col[c] | val;
            byte box_index = (r / 3) * 3 + c / 3;
            box[box_index] = box[box_index] | val;
        end
        c = c + 1;
    end
    r = r + 1;
end

byte ok;
call sudokuSolverRec(mat, 0, 0, row, col, box, ok);

call print_sudoku(mat);