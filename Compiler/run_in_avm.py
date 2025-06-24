import os

from codegen_helpers import write_code_to_file
from recursive_descent_parser import Parser

with open("input.prg", "rt") as program:
    text = program.read()

parser = Parser(text)
tree = parser.do_parse()
opt = True
while opt:
    opt = tree.optimize()
code = tree.gen_code(True)

write_code_to_file(code, text, "output.asm", write_debug_info=False)

runtime = r"..\x64\Release\Runtime.exe"
os.system(f"{runtime} output.asm -r -c")