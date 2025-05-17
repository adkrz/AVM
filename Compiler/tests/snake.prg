const byte WIDTH = 50;
const byte HEIGHT = 22;
const addr MEMORY_LOCATION = 10000;
CONST addr MEMORY_ROW_STRIDE = 98; // (width-2+1) * 2bits
CONST byte INITIAL_X = 20;
CONST byte INITIAL_HEAD_X = 24; // initial x + len - 1
CONST byte INITIAL_Y = 10;
CONST byte INITIAL_LEN = 5;
CONST byte BODY_CHAR = 'o';
CONST byte HEAD_CHAR = 'O';
CONST byte WALL_CHAR = '#';
CONST byte FRUIT_CHAR = '%';
CONST byte KeyW = 'w';
CONST byte KeyS = 's';
CONST byte KeyA = 'a';
CONST byte KeyD = 'd';
const addr DELAY = 200;
const byte RIGHT = 1;
const byte LEFT = 2;
const byte UP = 3;
const byte DOWN = 4;

function draw_head();

function xy_to_mem_loc(byte x, byte y, addr loc&)
begin
// -1 because we have 1px of borders
// *2 because of 16bit addresses
loc = MEMORY_LOCATION + (y-1) * MEMORY_ROW_STRIDE + (x-1) * 2;
end

function clear_memory()
begin
    addr endloc[];
    call xy_to_mem_loc(WIDTH, HEIGHT, endloc);
    do begin
        endloc[] = 0;
        endloc = endloc - 1;
       end
    while endloc >= MEMORY_LOCATION;
end

function draw_borders()
begin
    setconsolecolors(0, 16);
    byte w = WIDTH;
    while 1 do begin
        setconsolecursorposition(w,0);
        printch WALL_CHAR;
        setconsolecursorposition(w,HEIGHT);
        printch WALL_CHAR;

        w = w - 1;
        if w == 0 then break;
    end
    w = HEIGHT;
    while 1 do begin
        setconsolecursorposition(1,w);
        printch WALL_CHAR;
        setconsolecursorposition(WIDTH,w);
        printch WALL_CHAR;

        w = w - 1;
        if w == 0 then break;
    end
end

function write_initial_body()
begin
    byte X = INITIAL_X;
    byte Y = INITIAL_Y;
    byte L = 0;
    while L < INITIAL_LEN do begin
        addr loc[];
        call xy_to_mem_loc(X, Y, loc);
        loc[] = L + 1;
        L = L + 1;
        X = X + 1;
    end
end

function redraw(addr current_length)
begin
    // Skip 1 in beginning and end due to margin
    byte X = WIDTH - 1;
    while 1 do begin
        byte Y = HEIGHT - 1;
        while 1 do begin
            addr loc[];
            call xy_to_mem_loc(X, Y, loc);
            addr value = loc[];

            setconsolecursorposition(X, Y);
            if value == 0 then printch ' ';
            else if value == current_length then call draw_head();
            else printch BODY_CHAR;

            Y = Y - 1;
            if Y == 0 then break;
        end
        X = X -1;
        if X == 1 then break;
    end
end

function draw_head()
// Draws at current cursor position
begin
    setconsolecolors(0, 3);
    printch HEAD_CHAR;
    setconsolecolors(0, 15);
end

function draw_fruit(byte X, byte Y)
begin
    setconsolecursorposition(X, Y);
    setconsolecolors(10, 15);
    printch FRUIT_CHAR;
    setconsolecolors(0, 15);
end

function new_direction(byte key, byte direction&)
begin
    if key == KeyW then direction = UP;
    else if key == KeyS then direction = DOWN;
    else if key == KeyA then direction = LEFT;
    else if key == KeyD then direction = RIGHT;
end

function next_head_position(byte headX&, byte headY&, byte direction)
// gets X and Y of head and direction
// sets new XY by ref
// direction: 1 right 2 left 3 up 4 down
// note: Y goes down
begin
    if direction == UP then headY = headY - 1;
    else if direction == DOWN then headY = headY + 1;
    else if direction == LEFT then headX = headX - 1;
    else if direction == RIGHT then headX = headX + 1;
end

function random_fruit_position(byte fruit_x&, byte fruit_y&)
begin
    addr mem_ptr[];
    do begin
        fruit_x = getrandomnumber(1, WIDTH-1);
        fruit_y = getrandomnumber(1, HEIGHT-1);
        // check if we do not collide with the snake
        call xy_to_mem_loc(fruit_x, fruit_y, mem_ptr);
    end
    while mem_ptr[] > 0;
end

function move_body()
begin
    // Skip 1 in beginning and end due to margin
    byte X = WIDTH - 1;
    while 1 do begin
        byte Y = HEIGHT - 1;
        while 1 do begin
            addr loc[];
            call xy_to_mem_loc(X, Y, loc);
            addr value = loc[];

            if value > 0 then begin
                setconsolecursorposition(X, Y);
                value = value -1;
                if value == 0 then printch ' ';
                else printch BODY_CHAR;
            end
            loc[] = value;

            Y = Y - 1;
            if Y == 0 then break;
        end
        X = X -1;
        if X == 1 then break;
    end
end


showconsolecursor(0);
consoleclear();

byte direction = RIGHT;
addr length = INITIAL_LEN;
byte head_x = INITIAL_HEAD_X;
byte head_y = INITIAL_Y;
byte fruit_x = 0;
byte fruit_y = 0;
addr mem_ptr[];

call clear_memory();
call draw_borders();
call write_initial_body();
call redraw(length);

while 1 do begin
    byte key = readkey();

    if key then call new_direction(key, direction);

    call next_head_position(head_x, head_y, direction);

    // If the head is outside borders, game over:
    if head_x <= 1 || head_y == 0 || head_x == WIDTH || head_y == HEIGHT then break;

    // If we hit the snake body, game over:
    call xy_to_mem_loc(head_x, head_y, mem_ptr);
    if mem_ptr[] then break;

    //if we hit the fruit, make snake longer and generate another fruit:
    if head_x == fruit_x && head_y == fruit_y then begin
        length = length + 1;
        // by clearing X we mark the fruit as to be generated again:
        fruit_x = 0;
        // Show points:
        setconsolecursorposition(WIDTH + 5, HEIGHT / 2);
        print length - INITIAL_LEN;
    end

    // Write new head position to memory. Value = snake length + 1, so after decrement will be equal to HEAD value
    mem_ptr[] = length + 1;

    //if the fruit is eaten or initial, generate new one:
    if fruit_x == 0 then begin
        call random_fruit_position(fruit_x, fruit_y);
        call draw_fruit(fruit_x, fruit_y);
    end

    call move_body();

    // Show next head pos
    setconsolecursorposition(head_x, head_y);
    call draw_head();

    sleep(DELAY);
end


setconsolecursorposition(WIDTH, HEIGHT);
printnl;
printnl;
