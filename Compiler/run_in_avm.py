import os

from recursive_descent_parser import Parser

with open("input.prg", "rt") as program:
    code = program.read()

parser = Parser(code)
tree = parser.do_parse()
opt = True
#while opt:
#    opt = tree.optimize()
code = tree.gen_code(None)

with open("output.asm", "wt") as asm:
    asm.writelines("\n".join(code.codes))

runtime = r"..\x64\Release\Runtime.exe"
os.system(f"{runtime} output.asm -r -c")