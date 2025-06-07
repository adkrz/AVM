// Brainfuck interperter, improved from v2 - uses precomputed bracket caches
// Brainfuck interperter
// Using direct pointer move and dereference[] instead of using array[N]

// Hello World:
//byte program[] = addressof("++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.");
// Sierpinski triangle
byte program[] = addressof("++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]");
byte memory[] = 10000;
byte instruction;
byte instruction_pointer[] = program;
byte memory_pointer[] = memory;

while memory_pointer <= 40000 do begin
    memory_pointer[] = 0;
    memory_pointer = memory_pointer + 1;
end
memory_pointer = memory;

addr strlen = 0;
while instruction_pointer[] != '\0' do begin
    strlen = strlen + 1;
    instruction_pointer = instruction_pointer + 1;
end
instruction_pointer = program;

addr jump_cache[strlen];
addr cache_pointer[] = jump_cache;

// Precompute brackets, using brackets counter
// Another option is recursive call for finding next bracket, but this comes with own overhead
while instruction_pointer[] != '\0' do begin
    instruction = instruction_pointer[];
    if instruction == '[' then begin
        byte count_brackets = 1;
        addr ip1 = instruction_pointer;
        while 1 do begin
            instruction_pointer = instruction_pointer + 1;
            if instruction_pointer[] == '[' then count_brackets = count_brackets + 1;
            else if instruction_pointer[] == ']' then begin
                count_brackets = count_brackets -1;
                if count_brackets == 0 then begin
                    cache_pointer = jump_cache + (ip1 - program);
                    cache_pointer[] = instruction_pointer + 1;
                    cache_pointer = jump_cache + (instruction_pointer - program);
                    cache_pointer[] = ip1;
                    break;
                end
            end
        end
        instruction_pointer = ip1;
    end
    instruction_pointer = instruction_pointer + 1;
end

instruction_pointer = program;
while 1 do begin
    instruction = instruction_pointer[];

    if instruction == '[' then begin
        if memory_pointer[] == 0 then begin
            cache_pointer = jump_cache + (instruction_pointer - program);
            instruction_pointer = cache_pointer[];
            continue;
        end
    end

    else if instruction == ']' then begin
        cache_pointer = jump_cache + (instruction_pointer - program);
        instruction_pointer = cache_pointer[];
        continue;
    end

    else if instruction == '>' then memory_pointer = memory_pointer + 1;
    else if instruction == '<' then memory_pointer = memory_pointer - 1;
    else if instruction == '+' then memory_pointer[] = memory_pointer[] + 1;
    else if instruction == '-' then memory_pointer[] = memory_pointer[] - 1;
    else if instruction == '.' then printch memory_pointer[];
    else if instruction == '\0' then break;

    instruction_pointer = instruction_pointer + 1;
end
print "Program finished\n";