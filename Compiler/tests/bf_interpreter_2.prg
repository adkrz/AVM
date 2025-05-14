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

while 1 do begin
    instruction = instruction_pointer[];

    if instruction == '[' then begin
        if memory_pointer[] == 0 then begin
            byte count_brackets = 1;
            while 1 do begin
                instruction_pointer = succ(instruction_pointer);
                if instruction_pointer[] == '[' then count_brackets = succ(count_brackets);
                else if instruction_pointer[] == ']' then begin
                    count_brackets = pred(count_brackets);
                    if count_brackets == 0 then begin
                        instruction_pointer = succ(instruction_pointer);
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
                instruction_pointer = pred(instruction_pointer);
                if instruction_pointer[] == ']' then count_brackets = succ(count_brackets);
                else if instruction_pointer[] == '[' then begin
                    count_brackets = pred(count_brackets);
                    if count_brackets == 0 then break;
                end
        end
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