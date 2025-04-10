import sys
from enum import Enum

# TODO:
# break/continue
# general bool expression (to negate it, parentheses etc)
# functions and their arguments + return values
# https://en.wikipedia.org/wiki/Recursive_descent_parser

# input_string = "A=-123.5 + test * 2;\nX=3+5+(2-(3+2));"
input_string = ("A=5;\n"
                "while A<10 do begin\n"
                "A = A + 1;\nend\n")
position = 0
line_number = 1
current_number = 0
current_identifier = ""
code = ""

local_variables = {}  # name-length, in order of occurrence
if_counter = 1
while_counter = 1


class Symbol(Enum):
    Nothing = -1
    Plus = ord('+')
    Minus = ord('-')
    Mult = ord('*')
    Divide = ord('/')
    Semicolon = ord(';')
    Becomes = ord('=')
    LParen = ord('(')
    RParen = ord(')')
    Number = 256
    Div = 257
    Mod = 258
    Identifier = 259
    EOF = 260
    Equals = 261
    NotEqual = 262
    Gt = 263
    Ge = 264
    Lt = 265
    Le = 266
    # Negate = 267
    If = 268
    Then = 269
    Else = 270
    And = 271
    Or = 272
    Begin = 273
    End = 274
    While = 275
    Do = 276
    Continue = 277
    Break = 278


current = Symbol.Nothing


def getchar() -> str:
    global position
    if position < len(input_string):
        ret = input_string[position]
        position += 1
        return ret
    return ""


def rewind():
    global position
    if position > 0:
        position -= 1


def peek() -> str:
    if position < len(input_string):
        return input_string[position]
    return ""


def next_symbol():
    global current
    global current_number
    global current_identifier
    global line_number

    buffer = ""
    buffer_mode = 0  # 1: number 2: identifier

    while 1:
        t = getchar()

        if buffer_mode == 1:
            if t.isdigit() or t == '.':
                buffer += t
                continue
            else:
                current_number = int(buffer) if '.' not in buffer else float(buffer)
                if t != "":
                    rewind()
                return
        elif buffer_mode == 2:
            if t.isalnum() or t == '_':
                buffer += t
                continue
            else:
                if t != "":
                    rewind()

                buffer_l = buffer.lower()
                if buffer_l == "if":
                    current = Symbol.If
                    return
                elif buffer_l == "then":
                    current = Symbol.Then
                    return
                elif buffer_l == "else":
                    current = Symbol.Else
                    return
                elif buffer_l == "begin":
                    current = Symbol.Begin
                    return
                elif buffer_l == "end":
                    current = Symbol.End
                    return
                elif buffer_l == "while":
                    current = Symbol.While
                    return
                elif buffer_l == "do":
                    current = Symbol.Do
                    return
                elif buffer_l == "continue":
                    current = Symbol.Continue
                    return
                elif buffer_l == "break":
                    current = Symbol.Break
                    return

                current_identifier = buffer
                if current_identifier not in local_variables:
                    local_variables[current_identifier] = 1

                return

        if not t:
            current = Symbol.EOF
            return
        elif t in (' ', '\t'):
            continue
        elif t == '\n':
            line_number += 1
            continue
        elif t.isdigit() or t == '.' or (t == '-' and peek().isdigit()):
            current = Symbol.Number
            buffer += t
            buffer_mode = 1
            continue
        elif t.isalnum():
            current = Symbol.Identifier
            buffer += t
            buffer_mode = 2
            continue
        elif t == "=":
            if peek() == "=":
                current = Symbol.Equals
                getchar()
            else:
                current = Symbol.Becomes
            return
        elif t == "+":
            current = Symbol.Plus
            return
        elif t == "-":
            current = Symbol.Minus
            return
        elif t == "*":
            current = Symbol.Mult
            return
        elif t == "/":
            current = Symbol.Divide
            return
        elif t == ";":
            current = Symbol.Semicolon
            return
        elif t == "(":
            current = Symbol.LParen
            return
        elif t == ")":
            current = Symbol.RParen
            return
        elif t == ">":
            if peek() == "=":
                current = Symbol.Ge
                getchar()
            else:
                current = Symbol.Gt
            return
        elif t == "<":
            if peek() == "=":
                current = Symbol.Le
                getchar()
            else:
                current = Symbol.Lt
            return
        elif t == "!":
            if peek() == "=":
                current = Symbol.NotEqual
                getchar()
            # else:
            #    current = Symbol.Negate
            return
        elif t == "&" and peek() == "&":
            current = Symbol.And
            getchar()
            return
        elif t == "|" and peek() == "|":
            current = Symbol.Or
            getchar()
            return


def accept(t: Symbol) -> bool:
    if t == current:
        next_symbol()
        return True
    return False


def expect(s: Symbol) -> bool:
    if accept(s):
        return True
    error(f"Expected {s}")
    return False


def error(what: str):
    print(code)
    print(f"Error in line {line_number}: {what}", file=sys.stderr)
    exit(1)


def get_variable_offset(name: str) -> int:
    offs = 0
    if name not in local_variables:
        error(f"Unknown variable {name}")
    for k, v in local_variables.items():
        if k == name:
            break
        offs += v
    return offs


def parse_factor():
    global code
    if accept(Symbol.Identifier):
        code += f"LOAD_LOCAL {get_variable_offset(current_identifier)} ; {current_identifier}\n"
    elif accept(Symbol.Number):
        code += f"PUSH {current_number}\n"
    elif accept(Symbol.LParen):
        parse_expression()
        expect(Symbol.RParen)
    else:
        error("factor: syntax error")


def parse_term():
    global code
    parse_factor()
    while current == Symbol.Mult or current == Symbol.Divide:
        v = current
        next_symbol()
        parse_factor()
        code += "MUL" if v == Symbol.Mult else "DIV"
        code += '\n'


def parse_condition():
    global code
    parse_expression()
    if current in (Symbol.Equals, Symbol.NotEqual, Symbol.Gt, Symbol.Ge, Symbol.Lt, Symbol.Le):
        v = current
        next_symbol()
        parse_expression()
        if v == Symbol.Equals:
            opcode = "EQ"
        elif v == Symbol.NotEqual:
            opcode = "NE"
        elif v == Symbol.Gt:
            opcode = "GT"
        elif v == Symbol.Ge:
            opcode = "GE"
        elif v == Symbol.Lt:
            opcode = "LT"
        elif v == Symbol.Le:
            opcode = "LE"
        else:
            raise NotImplementedError()
        code += opcode + "\n"
    else:
        error("Condition: invalid operator")


def parse_condition_chain():
    global code
    parse_condition()
    while current in (Symbol.And, Symbol.Or):
        # TODO: precedence, shortcut evaluation
        if accept(Symbol.Or):
            parse_condition()
            code += "OR\n"
        if accept(Symbol.And):
            parse_condition()
            code += "AND\n"


def parse_expression():
    global code
    um = False
    if current == Symbol.Plus or current == Symbol.Minus:
        um = True
        next_symbol()
    parse_term()
    if um:
        code += "NEG\n"
    while current == Symbol.Plus or current == Symbol.Minus:
        v = current
        next_symbol()
        parse_term()
        code += "ADD" if v == Symbol.Plus else "SUB"
        code += '\n'


def parse_statement(inside_loop=False, inside_if=False, inside_function=False):
    global code
    global if_counter
    global while_counter
    if accept(Symbol.Identifier):
        var = current_identifier
        expect(Symbol.Becomes)
        parse_expression()
        code += f"STORE_LOCAL {get_variable_offset(var)} ; {var}\n"
        expect(Symbol.Semicolon)
    elif accept(Symbol.Begin):
        cont = True
        while cont:
            parse_statement(inside_loop=inside_loop, inside_if=inside_if, inside_function=inside_function)
            if accept(Symbol.End):
                break
        # expect(Symbol.End)
    elif accept(Symbol.If):
        # TODO: optimize unnecessary jumps if IF without ELSE
        no = if_counter
        if_counter += 1  # increment right away, because we may nest code
        parse_condition_chain()

        code += f"JF @if{no}_else\n"

        expect(Symbol.Then)
        parse_statement(inside_loop=inside_loop, inside_if=True, inside_function=inside_function)
        code += f"JMP @if{no}_endif\n"
        code += f":if{no}_else\n"

        if accept(Symbol.Else):
            if not inside_if:
                error("Else outside IF")
            parse_statement(inside_loop=inside_loop, inside_if=True, inside_function=inside_function)

        code += f":if{no}_endif\n"

    elif accept(Symbol.While):
        no = while_counter
        while_counter += 1
        code += f":while{no}_begin\n"
        parse_condition_chain()
        code += f"JF @while{no}_endwhile\n"

        expect(Symbol.Do)

        parse_statement(inside_loop=True, inside_if=inside_if, inside_function=inside_function)

        code += f":while{no}_endwhile\n"

    elif accept(Symbol.Break):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Break outside loop")
        no = while_counter
        code += f"JMP @while{no}_endwhile\n"

    elif accept(Symbol.Continue):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Continue outside loop")
        no = while_counter
        code += f"JMP @while{no}_begin\n"

    else:
        error("parse statement")


def parse_block():
    while 1:
        parse_statement()
        if accept(Symbol.EOF):
            break


def generate_preamble():
    global code
    txt = ""
    for k, length in local_variables.items():
        txt += f"PUSHN {length} ; {k}\n"
    # todo: optimize into one big block
    # todo: initial value instead of just push
    code = txt + code


if __name__ == '__main__':
    next_symbol()
    parse_block()
    generate_preamble()
    print(code)
    # expect(Symbol.Semicolon)
