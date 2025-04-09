from enum import Enum

# TODO:
# while
# general bool expression (to negate it, parentheses etc)
# functions and their arguments + return values
# https://en.wikipedia.org/wiki/Recursive_descent_parser

#input_string = "A=-123.5 + test * 2;\nX=3+5+(2-(3+2));"
input_string = "if A>=3 then X=2; ELSE X=4;"
position = 0
line_number = 1
current_number = 0
current_identifier = ""
code = ""

local_variables = {}  # name-length, in order of occurrence
if_counter = 1


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
    #Negate = 267
    If = 268
    Then = 269
    Else = 270
    And = 271
    Or = 272


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
                rewind()
                return
        elif buffer_mode == 2:
            if t.isalnum() or t == '_':
                buffer += t
                continue
            else:
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
            #else:
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
    print(f"Error in line {line_number}: {what}")
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


def parse_statement():
    global code
    global if_counter
    if accept(Symbol.Identifier):
        var = current_identifier
        expect(Symbol.Becomes)
        parse_expression()
        code += f"STORE_LOCAL {get_variable_offset(var)} ; {var}\n"
        expect(Symbol.Semicolon)
    elif accept(Symbol.If):
        # TODO: optimize unnecessary jumps if IF without ELSE

        parse_condition()
        while current in (Symbol.And, Symbol.Or):
            # TODO: precedence
            if accept(Symbol.Or):
                parse_condition()
                code += "OR\n"
            if accept(Symbol.And):
                parse_condition()
                code += "AND\n"

        code += f"JF @if{if_counter}_else\n"

        expect(Symbol.Then)
        parse_statement()
        code += f"JMP @if{if_counter}_endif\n"
        code += f":if{if_counter}_else\n"

        if accept(Symbol.Else):
            parse_statement()

        code += f":if{if_counter}_endif\n"
        if_counter += 1
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
    #expect(Symbol.Semicolon)
