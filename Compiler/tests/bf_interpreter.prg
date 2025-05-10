// Brainfuck interperter
// Hello World:
//byte program[] = addressof("++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.");
// Sierpinski triangle
byte program[] = addressof("++++++++[>+>++++<<-]>++>>+<[-[>>+<<-]+>>]>+[-<<<[->[+[-]+>++>>>-<<]<[<]>>++++++[<<+++++>>-]+<<++.[-]<<]>.>+[>>]>+]");
byte memory[] = 10000;
byte instruction;
byte instruction_pointer = 0;
addr memory_pointer = memory;

while memory_pointer <= 40000 do begin
    memory[memory_pointer] = 0;
    memory_pointer = memory_pointer + 1;
end
memory_pointer = memory;

while 1 do begin
    instruction = program[instruction_pointer];
    if instruction == '\0' then break;

    if instruction == '[' then begin
        if memory[memory_pointer] == 0 then begin
            byte count_brackets = 1;
            while 1 do begin
                instruction_pointer = instruction_pointer + 1;
                instruction = program[instruction_pointer];
                if instruction == '[' then count_brackets = count_brackets + 1;
                if instruction == ']' then begin
                    count_brackets = count_brackets - 1;
                    if count_brackets == 0 then begin
                        instruction_pointer = instruction_pointer + 1;
                        break;
                    end
                end
            end
           continue;
        end
    end

    else if instruction == ']' then begin
        byte count_brackets = 1;
        while 1 do begin
                instruction_pointer = instruction_pointer - 1;
                instruction = program[instruction_pointer];
                if instruction == ']' then count_brackets = count_brackets + 1;
                if instruction == '[' then begin
                    count_brackets = count_brackets - 1;
                    if count_brackets == 0 then break;
                end
        end
        continue;
    end

    else if instruction == '>' then memory_pointer = memory_pointer + 1;
    else if instruction == '<' then memory_pointer = memory_pointer - 1;
    else if instruction == '+' then memory[memory_pointer] = memory[memory_pointer] + 1;
    else if instruction == '-' then memory[memory_pointer] = memory[memory_pointer] - 1;
    else if instruction == '.' then printch memory[memory_pointer];

    instruction_pointer = instruction_pointer + 1;
end
print "Program finished\n";