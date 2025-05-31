import os

from recursive_descent_parser import Parser

with open("input.prg", "rt") as program:
    code = program.read()

parser = Parser(code)
parser.do_parse()
parser.optimize()

with open("output.asm", "wt") as asm:
    asm.writelines("\n".join(parser.get_code()))

runtime = r"..\x64\Release\Runtime.exe"
os.system(f"{runtime} output.asm -r -p")