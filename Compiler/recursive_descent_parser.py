import sys
from enum import Enum
from typing import Dict

# TODO:
# general bool expression (to negate it, parentheses etc)
# call function, use return values
# arrays
# global variables, shadowing by locals etc
# https://en.wikipedia.org/wiki/Recursive_descent_parser

# input_string = "A=-123.5 + test * 2;\nX=3+5+(2-(3+2));"
input_string = ("""
A = 1;

function druga(A, &B);

function funkcja(A, &B)
begin
B = A * 2;
call druga(1, B);
end

function druga(A, &B)
begin
B = A * 2;
end

call funkcja(1, A);

""")
position = 0
line_number = 1
current_number = 0
current_identifier = ""

if_counter = 1
while_counter = 1
condition_counter = 1

codes = {}  # per context
local_variables = {}  # per context, then name-length, in order of occurrence
current_context = ""  # empty = global, otherwise in function


def append_code(c: str, newline=True):
    global codes
    if newline:
        c += "\n"
    if current_context not in codes:
        codes[current_context] = c
    else:
        codes[current_context] += c


def prepend_code(c: str, newline=True):
    global codes
    if newline:
        c += "\n"
    if current_context not in codes:
        codes[current_context] = c
    else:
        codes[current_context] = c + codes[current_context]


def register_variable(name: str, length: int):
    if current_context in function_signatures:
        if name in function_signatures[current_context].args:
            return
    global local_variables
    if current_context not in local_variables:
        local_variables[current_context] = {name: length}
    else:
        if name not in local_variables[current_context]:
            local_variables[current_context][name] = length


def gen_load_store_instruction(name: str, load: bool):
    offs = 0
    base = "LOAD" if load else "STORE"
    if current_context in function_signatures and name in function_signatures[current_context].args:
        for k, v in reversed(function_signatures[current_context].args.items()):
            offs += v.length
            if k == name:
                break
        append_code(f"{base}_ARG {offs} ; {name}")
        return
    if current_context not in local_variables:
        error(f"Current context is empty: {current_context}")
    if name not in local_variables[current_context]:
        error(f"Unknown variable {name}")
    for k, v in local_variables[current_context].items():
        if k == name:
            break
        offs += v
    append_code(f"{base}_LOCAL {offs} ; {name}")


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
    Function = 279
    Return = 280
    Call = 281
    Reference = 282
    Comma = 282


class FunctionArgument:
    def __init__(self, length: int, by_ref: bool = False):
        self.length = length
        self.by_ref = by_ref


class FunctionSignature:
    def __init__(self):
        self.args: Dict[str, FunctionArgument] = {}

    def __str__(self):
        return "(" + ", ".join(("&" if v.by_ref else "") + name for name, v in self.args.items()) + ")"


current = Symbol.Nothing

function_signatures: Dict[str, FunctionSignature] = {}


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
    previous_mode = current

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
                elif buffer_l == "function":
                    current = Symbol.Function
                    return
                elif buffer_l == "return":
                    current = Symbol.Return
                    return
                elif buffer_l == "call":
                    current = Symbol.Call
                    return

                current_identifier = buffer
                return

        if not t:
            current = Symbol.EOF
            return
        elif t in (' ', '\t', '\r'):
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
        elif t == "/" and peek() != "/":  # divide vs comment
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
        elif t == "&":
            if peek() == "&":
                current = Symbol.And
                getchar()
            else:
                current = Symbol.Reference
            return
        elif t == "|" and peek() == "|":
            current = Symbol.Or
            getchar()
            return
        elif t == "/" and peek() == "/":
            while peek() != '\n':
                getchar()
        elif t == ',':
            current = Symbol.Comma
            return


def accept(t: Symbol) -> bool:
    if t == current:
        next_symbol()
        return True
    return False


def expect(s: Symbol) -> bool:
    if accept(s):
        return True
    error(f"Expected {s}, got {current}")
    return False


def error(what: str):
    print_code()
    print(f"Error in line {line_number}: {what}", file=sys.stderr)
    exit(1)


def parse_factor():
    if accept(Symbol.Identifier):
        gen_load_store_instruction(current_identifier, True)
    elif accept(Symbol.Number):
        append_code(f"PUSH {current_number}")
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
        append_code("MUL" if v == Symbol.Mult else "DIV")


def parse_condition():
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
        append_code(opcode)
    else:
        error("Condition: invalid operator")


def parse_condition_chain():
    global condition_counter
    parse_condition()
    has_chain = False
    while current in (Symbol.And, Symbol.Or):
        # TODO: precedence
        if accept(Symbol.Or):
            has_chain = True
            append_code(f"DUP\nJT cond{condition_counter}_expr_end")
            parse_condition()
            append_code("OR")
        elif accept(Symbol.And):
            has_chain = True
            append_code(f"DUP\nJF cond{condition_counter}_expr_end")
            parse_condition()
            append_code("AND")
    if has_chain:
        append_code(f":cond{condition_counter}_expr_end")
    condition_counter += 1


def parse_expression():
    um = False
    if current == Symbol.Plus or current == Symbol.Minus:
        um = True
        next_symbol()
    parse_term()
    if um:
        append_code("NEG")
    while current == Symbol.Plus or current == Symbol.Minus:
        v = current
        next_symbol()
        parse_term()
        append_code("ADD" if v == Symbol.Plus else "SUB")


def parse_statement(inside_loop=False, inside_if=False, inside_function=False):
    global if_counter
    global while_counter
    if accept(Symbol.Identifier):
        var = current_identifier
        register_variable(var, 1)
        expect(Symbol.Becomes)
        parse_expression()
        gen_load_store_instruction(var, False)
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

        append_code(f"JF @if{no}_else")

        expect(Symbol.Then)
        parse_statement(inside_loop=inside_loop, inside_if=True, inside_function=inside_function)
        append_code(f"JMP @if{no}_endif")
        append_code(f":if{no}_else")

        if accept(Symbol.Else):
            if not inside_if:
                error("Else outside IF")
            parse_statement(inside_loop=inside_loop, inside_if=True, inside_function=inside_function)

        append_code(f":if{no}_endif")

    elif accept(Symbol.While):
        no = while_counter
        while_counter += 1
        append_code(f":while{no}_begin")
        parse_condition_chain()
        append_code(f"JF @while{no}_endwhile")

        expect(Symbol.Do)

        parse_statement(inside_loop=True, inside_if=inside_if, inside_function=inside_function)

        append_code(f":while{no}_endwhile")

    elif accept(Symbol.Break):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Break outside loop")
        no = while_counter
        append_code(f"JMP @while{no}_endwhile")

    elif accept(Symbol.Continue):
        expect(Symbol.Semicolon)
        if not inside_loop:
            error("Continue outside loop")
        no = while_counter
        append_code(f"JMP @while{no}_begin")

    elif accept(Symbol.Call):
        expect(Symbol.Identifier)
        func = current_identifier
        if func not in function_signatures:
            error(f"Unknown function {func}")
        signature = function_signatures[func]

        expect(Symbol.LParen)

        append_code(";" + func + str(signature))

        refs_mapping = {}
        for i, arg in enumerate(signature.args.values()):
            if i > 0:
                expect(Symbol.Comma)
            if not arg.by_ref:
                parse_expression()
            else:
                expect(Symbol.Identifier)
                gen_load_store_instruction(current_identifier, True)
                refs_mapping[arg] = current_identifier

        expect(Symbol.RParen)

        expect(Symbol.Semicolon)
        append_code(f"CALL @function_{func}")

        append_code("; stack cleanup")
        for arg in reversed(signature.args.values()):
            if not arg.by_ref:
                append_code(f"POPN {arg.length}")
            else:
                gen_load_store_instruction(refs_mapping[arg], False)


    elif accept(Symbol.Return):
        if not inside_function:
            error("Return outside function")
        append_code("RET")

    else:
        error("parse statement")


def parse_block(inside_function=False):
    global current_context
    global function_signatures

    if accept(Symbol.EOF):
        return

    elif accept(Symbol.Function):
        expect(Symbol.Identifier)
        old_ctx = current_context
        current_context = current_identifier

        signature = FunctionSignature()
        function_signatures[current_context] = signature

        expect(Symbol.LParen)

        while not accept(Symbol.RParen):
            if signature.args:
                expect(Symbol.Comma)
            if accept(Symbol.Identifier):
                arg = FunctionArgument(1, False)
                signature.args[current_identifier] = arg
            elif accept(Symbol.Reference):
                next_symbol()
                arg = FunctionArgument(1, True)
                signature.args[current_identifier] = arg

        if accept(Symbol.Semicolon):
            # just a declaration
            pass
        else:
            # definition
            parse_block(True)
            append_code("RET")
            generate_preamble()
            prepend_code(f":function_{current_context}\n;{signature}")
        current_context = old_ctx
    else:
        parse_statement(inside_function=inside_function)


def generate_preamble():
    txt = ""
    if current_context not in local_variables:
        return
    for k, length in local_variables[current_context].items():
        txt += f"PUSHN {length} ; {k}\n"
    # todo: optimize into one big block
    # todo: initial value instead of just push
    prepend_code(txt, False)


def print_code():
    # "main" must be printed first to not execute functions
    if "" in codes:
        print(codes[""])
    for ctx, code in codes.items():
        if ctx:
            print(code)


if __name__ == '__main__':
    next_symbol()
    while not accept(Symbol.EOF):
        parse_block()
    current_context = ""
    append_code("HALT")
    generate_preamble()
    print_code()
    # expect(Symbol.Semicolon)
