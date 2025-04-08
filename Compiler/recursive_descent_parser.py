from enum import Enum

# TODO:
# unary minus
# identifier table
# functions and conditionals
# https://en.wikipedia.org/wiki/Recursive_descent_parser

input_string = "A=2+(305)*6+7/2+2;"
position = 0
line_number = 1
current_number = 0


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


current = Symbol.Nothing


def getchar() -> str:
    global position
    if position < len(input_string):
        ret = input_string[position]
        position += 1
        return ret
    return ""


def next_symbol():
    global current
    global current_number
    global position
    number_buffer = ""
    while 1:
        t = getchar()

        if number_buffer:
            if t.isdigit():
                number_buffer += t
                continue
            else:
                current_number = int(number_buffer)
                position -= 1
                return

        if not t:
            current = Symbol.EOF
            return
        elif t in (' ', '\t'):
            continue
        elif t.isdigit():
            current = Symbol.Number
            number_buffer += t
            continue
        elif t.isalnum():
            current = Symbol.Identifier
            return
        elif t == "=":
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
    print(f"Error in line {line_number}: {what}")
    exit(1)


def parse_factor():
    if accept(Symbol.Identifier):
        print("Identifier")
    elif accept(Symbol.Number):
        print(f"PUSH {current_number}")
    elif accept(Symbol.LParen):
        parse_expression()
        expect(Symbol.RParen)
    else:
        error("factor: syntax error")


def parse_term():
    parse_factor()
    while current == Symbol.Mult or current == Symbol.Divide:
        v = current
        next_symbol()
        parse_factor()
        print("MUL" if v == Symbol.Mult else "DIV")


def parse_expression():
    global current
    v = current
    if current == Symbol.Plus or current == Symbol.Minus:
        next_symbol()
        if v == Symbol.Minus:
            print("NEGATE NEXT")
    parse_term()
    while current == Symbol.Plus or current == Symbol.Minus:
        v = current
        next_symbol()
        parse_term()
        print("ADD" if v == Symbol.Plus else "SUB")


def parse_statement():
    if accept(Symbol.Identifier):
        expect(Symbol.Becomes)
        parse_expression()
    else:
        error("parse statement")


def parse_block():
    parse_statement()


if __name__ == '__main__':
    next_symbol()
    parse_block()
    expect(Symbol.Semicolon)
