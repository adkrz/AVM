// Brainfuck interperter, improved from v2 - uses precomputed bracket caches
// Brainfuck interperter
// Using direct pointer move and dereference[] instead of using array[N], use pred/succ instead of +/-1

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
    memory_pointer = succ(memory_pointer);
end
memory_pointer = memory;

addr strlen = 0;
while instruction_pointer[] != '\0' do begin
    strlen = succ(strlen);
    instruction_pointer = succ(instruction_pointer);
end
instruction_pointer = program;

addr jump_cache[strlen];
addr cache_pointer[] = jump_cache;

while instruction_pointer[] != '\0' do begin
    instruction = instruction_pointer[];
    if instruction == '[' then begin
        byte count_brackets = 1;
        addr ip1 = instruction_pointer;
        while 1 do begin
            instruction_pointer = succ(instruction_pointer);
            if instruction_pointer[] == '[' then count_brackets = succ(count_brackets);
            else if instruction_pointer[] == ']' then begin
                count_brackets = pred(count_brackets);
                if count_brackets == 0 then begin
                    cache_pointer = jump_cache + (ip1 - program);
                    cache_pointer[] = succ(instruction_pointer);
                    cache_pointer = jump_cache + (instruction_pointer - program);
                    cache_pointer[] = ip1;
                    break;
                end
            end
        end
        instruction_pointer = ip1;
    end
    instruction_pointer = succ(instruction_pointer);
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

    else if instruction == '>' then memory_pointer = succ(memory_pointer);
    else if instruction == '<' then memory_pointer = pred(memory_pointer);
    else if instruction == '+' then memory_pointer[] = succ(memory_pointer[]);
    else if instruction == '-' then memory_pointer[] = pred(memory_pointer[]);
    else if instruction == '.' then printch memory_pointer[];
    else if instruction == '\0' then break;

    instruction_pointer = succ(instruction_pointer);
end
print "Program finished\n";